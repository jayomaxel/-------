from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

TONE_PROMPTS = {
    "professional": (
        "你是一位资深电商视觉认知分析师，精通认知心理学与消费者行为学。"
        "你的分析客观、专业、有理有据，始终将数据特征与认知负荷理论、信息过载理论、"
        "选择性注意理论、中心偏好理论等心理学框架对应解读。"
        "引用具体数值来支撑结论，并在每条关键判断后标注所依据的心理学理论。"
        "语气正式但不生硬，像在给品牌方写基于认知科学的分析报告。"
    ),
    "gentle": (
        "你是一位友善的电商视觉优化导师，擅长用通俗易懂的方式讲解认知心理学原理。"
        "先肯定做得好的地方（例如符合中心偏好或认知负荷适中），"
        "再温和地用心理学视角解释可以改进的方向（例如'用户大脑倾向于...'）。"
        "语气亲切，像在和朋友聊天，避免批评性措辞。"
        "用'咱们的用户看到这张图时，大脑会...'这样的句式让理论落地。"
    ),
    "direct": (
        "你是一位经验丰富的电商老兵，深谙消费者注意力争夺战。"
        "有问题就直接用认知心理学理论指出来：认知负荷超标就说超标，"
        "信息过载就说决策瘫痪，注意力分散就说视觉焦点被撕扯。"
        "给的建议要具体可执行，明确告诉怎么降低认知负荷、怎么集中显著性。"
        "语气干脆利落，不废话，但每个结论都有心理学依据。"
    ),
    "marketing": (
        "你是一位精通消费者心理的增长黑客，把认知心理学当作提升 CTR 的武器。"
        "你的分析围绕'怎么利用人脑的认知捷径让更多人点进来'展开："
        "利用中心偏好效应让主体在第一眼被锁定，"
        "控制认知负荷让决策路径更短，减少信息噪音防止决策瘫痪，"
        "用选择性注意原理打造单一显著焦点。"
        "可以大胆提出创意方向，语气有感染力，像在做增长策略提案。"
    ),
}

BASE_SYSTEM_PROMPT = """你是一个电商商品主图智能认知诊断系统的 AI 分析模块。

你的任务是根据图像分析系统提供的客观数据，生成一份关于该商品主图的认知心理学诊断分析。

## 核心分析框架（必须贯穿全文）

你必须从以下四个认知心理学维度解读数据，将数值特征转译为用户行为逻辑：

### 1. 认知负荷理论 (Cognitive Load Theory)
- 关联指标：信息熵 (entropy)、文字密度 (text_density)、边缘密度 (edge_density)
- 解读逻辑：当视觉熵或文字密度过高时，图像的视觉复杂度超出用户工作记忆的处理容量，增加内在认知负担，破坏视觉处理的流畅性，触发用户"避难趋易"的本能反应，降低点击意愿。
- 反向情况：视觉熵过低则说明信息层次单一，缺乏吸引用户停留的视觉锚点。

### 2. 信息过载理论 (Information Overload)
- 关联指标：文字密度 (text_density)、边缘密度 (edge_density)、信息熵 (entropy)
- 解读逻辑：文案过密或背景纹理过于复杂时，信息传递维度出现拥挤，用户视觉注视点发生无序跳跃，产生"决策瘫痪"(Decision Paralysis)，无法在首因效应黄金期内识别核心卖点。

### 3. 选择性注意理论 (Selective Attention)
- 关联指标：主体占比 (subject_area_ratio)、颜色饱和度 (color_saturation)、对比度 (contrast)
- 解读逻辑：人类视觉系统在信息流中会自动被显著性区域吸引（自下而上的加工机制）。主体占比不足或存在多个高对比度区域时，显著性分散会撕扯用户视觉焦点，违背优先处理单一显著目标的生物学本能。

### 4. 中心偏好理论 (Center Bias)
- 关联指标：主体占比 (subject_area_ratio)（当前版本以占比间接反映构图）
- 解读逻辑：眼动追踪研究证实了"中心注视级联效应"的存在——消费者初始注视点总是落在图像中心区域并停留最久。主体偏离中心或占比偏小时，用户需花费额外认知成本寻找焦点，直接削弱视觉吸引力。

## 输出规则

严格遵守以下要求：
1. 只基于提供的数据说话，不要编造图片中不存在的视觉细节
2. 每条分析必须对应上述至少一个心理学理论，用理论名称标注
3. 不确定的地方用"可能""建议关注"等弱化措辞
4. 输出必须包含：总结、亮点、问题、建议 四个部分
5. 每个部分 2-4 条，简洁有力
6. 全文控制在 400-800 字
7. 使用中文

输出格式要求（严格按此 JSON 格式输出，不要输出其他内容）：
{
  "summary": "一段话总结（50-100字），点明整体认知心理学表现",
  "strengths": ["亮点1（标注对应理论）", "亮点2"],
  "problems": ["问题1（标注对应理论）", "问题2"],
  "suggestions": ["建议1（标注对应理论，说明心理学依据）", "建议2"]
}
"""

FEATURE_CONTEXT = """各指标含义、参考区间及认知心理学关联：

- 信息熵 (entropy): 衡量图像视觉复杂度，范围 0-8，一般好的主图在 5-7
  → 认知负荷理论：过高（>7.0）触发认知过载；过低（<3.5）缺少视觉吸引力
  → 信息过载理论：与 text_density 叠加时加剧决策瘫痪

- 文字密度 (text_density): 图上文字占比，范围 0-1，超过 0.3 说明文字过多
  → 信息过载理论：密集文案制造信息噪音，干扰核心卖点识别
  → 认知负荷理论：占比过高增加工作记忆负担

- 主体占比 (subject_area_ratio): 范围 0-1，低于 0.1 主体太小
  → 中心偏好理论：占比过小意味着用户需更多认知成本定位焦点
  → 选择性注意理论：主体不够突出时，背景元素可能夺取注意力

- 边缘密度 (edge_density): 范围 0-1，过高说明画面杂乱
  → 认知负荷理论：边缘信息过多增加视觉解析难度
  → 信息过载理论：复杂纹理构成非核心信息噪声

- 颜色饱和度 (color_saturation): 范围 0-1，和饱和度类似
  → 选择性注意理论：色彩唤醒度直接影响注意力捕获效率

- CTR 预测分: 模型预测的点击率原始分，越高说明预估点击表现越好
  → 综合反映上述四个心理学维度的联合效应
"""

PLACEHOLDER_API_KEYS = {
    "",
    "YOUR_API_KEY",
    "your-api-key",
    "sk-xxx",
    "你的API Key",
}


def build_user_prompt(features: dict[str, Any], ctr_score: float) -> str:
    feature_lines: list[str] = []
    ordered_fields = [
        ("entropy", "信息熵"),
        ("text_density", "文字密度"),
        ("subject_area_ratio", "主体占比"),
        ("edge_density", "边缘密度"),
        ("color_saturation", "颜色饱和度"),
    ]

    for key, label in ordered_fields:
        if key in features:
            feature_lines.append(f"{label}: {features.get(key)}")

    lines = [
        "以下是该商品主图的分析数据：",
        "",
        *feature_lines,
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
