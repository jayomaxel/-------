from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Mapping

from openai import AsyncOpenAI

import config

DEFAULT_TONE = "professional"

TONE_STYLES: dict[str, dict[str, str]] = {
    "professional": {
        "label": "Professional",
        "instruction": "Use a professional, objective, consultant-like tone.",
    },
    "encouraging": {
        "label": "Encouraging",
        "instruction": "Use a warm, supportive, constructive tone.",
    },
    "direct": {
        "label": "Direct",
        "instruction": "Use a direct, sharp, no-fluff tone without being rude.",
    },
    "strategic": {
        "label": "Strategic",
        "instruction": "Use a strategy-director tone that emphasizes priorities and business impact.",
    },
}


class AIAnalysisConfigurationError(RuntimeError):
    """Raised when the AI provider configuration is missing or invalid."""


class AIAnalysisGenerationError(RuntimeError):
    """Raised when the AI provider returns an unusable response."""


def _is_placeholder_api_key(value: str) -> bool:
    normalized = value.strip()
    return not normalized or normalized in {
        "YOUR_API_KEY",
        "your-api-key",
        "sk-xxx",
    }


def _round_number(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, 4)
    return value


def _compact_features(features: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(features, Mapping):
        return {}

    return {
        key: _round_number(features.get(key))
        for key in (
            "entropy",
            "text_density",
            "brightness",
            "contrast",
            "saturation",
            "subject_area_ratio",
            "edge_density",
            "color_saturation",
        )
        if key in features
    }


def _compact_ctr(ctr: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(ctr, Mapping):
        return {}

    return {
        "score": _round_number(ctr.get("score", 0.0)),
        "percentile": ctr.get("percentile"),
        "percentile_available": bool(ctr.get("percentile_available", False)),
    }


def _compact_similar_items(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []

    compact_items: list[dict[str, Any]] = []
    for item in items[:3]:
        if not isinstance(item, Mapping):
            continue

        compact_items.append(
            {
                "rank": item.get("rank", 0),
                "dataset_name": item.get("dataset_name") or item.get("dataset_key") or "",
                "img_name": item.get("img_name", ""),
                "similarity": _round_number(item.get("similarity", 0.0)),
                "relative_ctr": _round_number(item.get("relative_ctr", 0.0)),
                "price": _round_number(item.get("price", 0.0)),
            }
        )

    return compact_items


def _compact_advice(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []

    compact_items: list[dict[str, Any]] = []
    for item in items[:3]:
        if not isinstance(item, Mapping):
            continue

        compact_items.append(
            {
                "priority": str(item.get("priority", "")),
                "category": str(item.get("category", "")),
                "issue": str(item.get("issue", "")),
                "suggestion": str(item.get("suggestion", "")),
            }
        )

    return compact_items


def _compact_psychological_report(report: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(report, Mapping):
        return {"text": "", "lines": []}

    lines = report.get("lines", [])
    if not isinstance(lines, list):
        lines = []

    return {
        "text": str(report.get("text", "")),
        "lines": [str(line) for line in lines[:4]],
    }


def _build_analysis_summary(analysis: Mapping[str, Any]) -> dict[str, Any]:
    warnings = analysis.get("warnings", [])
    if not isinstance(warnings, list):
        warnings = []

    return {
        "features": _compact_features(analysis.get("features")),
        "ctr": _compact_ctr(analysis.get("ctr")),
        "similar_products": _compact_similar_items(analysis.get("similar")),
        "rule_advice": _compact_advice(analysis.get("advice")),
        "psychological_report": _compact_psychological_report(
            analysis.get("psychological_report")
        ),
        "warnings": [str(item) for item in warnings[:8]],
    }


def _extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            text_value = None
            if isinstance(item, Mapping):
                text_value = item.get("text")
            else:
                text_value = getattr(item, "text", None)

            if isinstance(text_value, str) and text_value.strip():
                chunks.append(text_value.strip())

        return "\n".join(chunks).strip()

    return ""


def _build_messages(analysis_summary: Mapping[str, Any], tone: str) -> list[dict[str, str]]:
    tone_config = TONE_STYLES.get(tone, TONE_STYLES[DEFAULT_TONE])
    system_prompt = (
        "You are an e-commerce main-image diagnosis assistant. "
        "Use only the provided structured analysis data. "
        "Do not invent visual details that are not supported by the data. "
        "Write the final answer in Simplified Chinese. "
        "The report must cover overall judgment, key issues, and actionable optimization directions. "
        "Do not output JSON, tables, or code blocks."
    )
    user_prompt = (
        f"Tone label: {tone_config['label']}. {tone_config['instruction']}\n"
        "Write 3 to 4 short paragraphs in Simplified Chinese. "
        "Each paragraph should have 1 to 3 sentences. "
        "Keep the full report around 220 to 420 Chinese characters. "
        "Paragraph 1: overall conclusion. "
        "Paragraph 2: key issues. "
        "Paragraph 3: practical optimization directions and priority. "
        "If warnings exist, briefly mention the possible downgrade impact in a natural way. "
        "Try to synthesize CTR, visual features, similar products, rule-based advice, and psychology report clues.\n\n"
        "Structured analysis data:\n"
        f"{json.dumps(analysis_summary, ensure_ascii=False, indent=2)}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    api_key = str(config.AI_MODEL_API_KEY).strip()
    if _is_placeholder_api_key(api_key):
        raise AIAnalysisConfigurationError(
            "AI_MODEL_API_KEY is not configured. Set it in the environment or config.py first."
        )

    return AsyncOpenAI(
        api_key=api_key,
        base_url=str(config.AI_MODEL_BASE_URL).rstrip("/"),
        timeout=float(config.AI_TIMEOUT),
    )


async def generate_ai_analysis_report(
    analysis: Mapping[str, Any],
    tone: str = DEFAULT_TONE,
) -> dict[str, str]:
    tone_key = tone if tone in TONE_STYLES else DEFAULT_TONE
    client = _get_client()
    summary = _build_analysis_summary(analysis)

    response = await client.chat.completions.create(
        model=str(config.AI_MODEL_NAME),
        messages=_build_messages(summary, tone_key),
        temperature=0.7,
        max_tokens=int(config.AI_MAX_TOKENS),
    )

    if not response.choices:
        raise AIAnalysisGenerationError("The AI model returned no usable choices.")

    report = _extract_message_text(response.choices[0].message.content).strip()
    if not report:
        raise AIAnalysisGenerationError("The AI model returned an empty report.")

    return {
        "tone": tone_key,
        "tone_label": TONE_STYLES[tone_key]["label"],
        "report": report,
        "model": str(config.AI_MODEL_NAME),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
