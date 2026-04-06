from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

TONE_PROMPTS = {
    "professional": (
        "你是一位资深电商视觉分析师，擅长从数据角度解读商品主图的优劣。"
        "你的分析客观、专业、有理有据，引用具体数值来支撑结论。"
        "语气正式但不生硬，像在给品牌方写分析报告。"
    ),
    "gentle": (
        "你是一位友善的电商运营导师，擅长用温和鼓励的方式帮助商家改进主图。"
        "先肯定做得好的地方，再温和地指出可以改进的方向。"
        "语气亲切，像在和朋友聊天，避免批评性措辞。"
    ),
    "direct": (
        "你是一位经验丰富的电商老兵，说话直接不绕弯。"
        "有问题就指出来，不需要铺垫。给的建议要具体可执行。"
        "语气干脆利落，不废话。"
    ),
    "marketing": (
        "你是一位增长黑客，一切以提升点击率和转化率为目标。"
        "你的分析围绕“怎么让更多人点进来”展开，建议偏实战和增长导向。"
        "可以大胆提出创意方向，语气有感染力。"
    ),
}

BASE_SYSTEM_PROMPT = """你是一个电商商品主图智能诊断系统的 AI 分析模块。

你的任务是根据图像分析系统提供的客观数据，生成一份关于该商品主图的诊断分析。

严格遵守以下规则：
1. 只基于提供的数据说话，不要编造图片中不存在的信息
2. 不确定的地方用“可能”“建议关注”等弱化措辞
3. 输出必须包含：总结、亮点、问题、建议 四个部分
4. 每个部分 2-4 条，简洁有力
5. 全文控制在 400-800 字
6. 使用中文

输出格式要求（严格按此 JSON 格式输出，不要输出其他内容）：
{
  "summary": "一段话总结（50-100字）",
  "strengths": ["亮点1", "亮点2"],
  "problems": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}
"""

FEATURE_CONTEXT = """各指标含义和参考区间：
- 信息熵 (entropy): 衡量图像信息丰富度，范围 0-8，一般好的主图在 5-7
- 文字密度 (text_density): 图上文字占比，范围 0-1，超过 0.3 说明文字过多
- 亮度 (brightness): 范围 0-1，低于 0.3 偏暗，高于 0.9 偏亮
- 对比度 (contrast): 范围 0-100，低于 20 偏平淡，高于 80 偏强烈
- 饱和度 (saturation): 范围 0-1，低于 0.15 色彩寡淡
- 主体占比 (subject_area_ratio): 范围 0-1，低于 0.1 主体太小
- 边缘密度 (edge_density): 范围 0-1，过高说明画面杂乱
- 颜色饱和度 (color_saturation): 范围 0-1，和饱和度类似
- CTR 预测分: 模型预测的点击率原始分，越高说明预估点击表现越好
"""

PLACEHOLDER_API_KEYS = {
    "",
    "YOUR_API_KEY",
    "your-api-key",
    "sk-xxx",
    "你的API Key",
}


def build_user_prompt(features: dict[str, Any], ctr_score: float) -> str:
    lines = [
        "以下是该商品主图的分析数据：",
        "",
        f"信息熵: {features.get('entropy', 'N/A')}",
        f"文字密度: {features.get('text_density', 'N/A')}",
        f"亮度: {features.get('brightness', 'N/A')}",
        f"对比度: {features.get('contrast', 'N/A')}",
        f"饱和度: {features.get('saturation', 'N/A')}",
        f"主体占比: {features.get('subject_area_ratio', 'N/A')}",
        f"边缘密度: {features.get('edge_density', 'N/A')}",
        f"颜色饱和度: {features.get('color_saturation', 'N/A')}",
        f"CTR 预测原始分: {ctr_score}",
        "",
        FEATURE_CONTEXT,
        "",
        "请基于以上数据进行分析，严格按要求的 JSON 格式输出。",
    ]
    return "\n".join(lines)


def _strip_code_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines:
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _resolve_api_key(api_key: str | None) -> str:
    candidate = (api_key or "").strip()
    if candidate:
        return candidate
    return str(config.AI_MODEL_API_KEY).strip()


def _api_key_is_configured(api_key: str) -> bool:
    return api_key not in PLACEHOLDER_API_KEYS


def _build_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url=config.AI_MODEL_BASE_URL,
        timeout=config.AI_TIMEOUT,
    )


def analyze_with_ai(
    features: dict[str, Any],
    ctr_score: float,
    tone: str = "professional",
    api_key: str | None = None,
) -> dict[str, Any]:
    tone_prompt = TONE_PROMPTS.get(tone, TONE_PROMPTS["professional"])
    system_prompt = tone_prompt + "\n\n" + BASE_SYSTEM_PROMPT
    user_prompt = build_user_prompt(features, ctr_score)
    content = ""
    resolved_api_key = _resolve_api_key(api_key)

    if not _api_key_is_configured(resolved_api_key):
        return {
            "tone": tone,
            "summary": "",
            "strengths": [],
            "problems": [],
            "suggestions": [],
            "success": False,
            "error": "AI API Key 未配置，请先在前端填写，或在服务端 config.py / 环境变量中设置有效值。",
        }

    try:
        client = _build_client(resolved_api_key)
        response = client.chat.completions.create(
            model=config.AI_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=config.AI_MAX_TOKENS,
            temperature=0.7,
            timeout=config.AI_TIMEOUT,
        )

        content = (response.choices[0].message.content or "").strip()
        content = _strip_code_fence(content)
        result = json.loads(content)

        return {
            "tone": tone,
            "summary": str(result.get("summary", "")).strip(),
            "strengths": _as_string_list(result.get("strengths")),
            "problems": _as_string_list(result.get("problems")),
            "suggestions": _as_string_list(result.get("suggestions")),
            "success": True,
        }
    except json.JSONDecodeError:
        logger.warning("AI returned non-JSON content, falling back to raw text.")
        return {
            "tone": tone,
            "summary": content or "分析生成失败",
            "strengths": [],
            "problems": [],
            "suggestions": [],
            "success": True,
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("AI analysis failed: %s", exc)
        error_message = str(exc)
        lowered = error_message.lower()
        if "401" in error_message or "authentication" in lowered:
            error_message = "AI 模型认证失败，请检查 API Key 或模型服务地址配置。"
        elif "timeout" in lowered:
            error_message = "AI 分析请求超时，请稍后重试。"

        return {
            "tone": tone,
            "summary": "",
            "strengths": [],
            "problems": [],
            "suggestions": [],
            "success": False,
            "error": error_message,
        }
