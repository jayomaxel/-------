# -*- coding: utf-8 -*-
"""基于当前主链路真实特征生成主图优化建议。"""

import config


def _to_float(value: object, default: float = 0.0) -> float:
    """把值转成 float，失败时返回默认值。"""
    try:
        return float(value)
    except Exception:
        return default


def generate_advice(features: dict) -> list[dict]:
    """按优先级返回主图优化建议。"""
    entropy = _to_float(features.get("entropy", 0.0))
    text_density = _to_float(features.get("text_density", 0.0))
    subject_area_ratio = _to_float(features.get("subject_area_ratio", 0.0))

    advice: list[dict] = []

    if entropy > config.ENTROPY_HIGH:
        advice.append(
            {
                "priority": "高",
                "category": "视觉复杂度",
                "issue": f"视觉熵为 {entropy:.4f}，高于阈值 {config.ENTROPY_HIGH}",
                "suggestion": "视觉复杂度超出认知负荷理论的舒适阈值，建议简化背景元素、减少装饰纹理，强化主体聚焦以降低用户的视觉解析成本。",
            }
        )
    elif entropy < config.ENTROPY_LOW:
        advice.append(
            {
                "priority": "中",
                "category": "视觉复杂度",
                "issue": f"视觉熵为 {entropy:.4f}，低于阈值 {config.ENTROPY_LOW}",
                "suggestion": "画面信息层次单一，缺乏有效的视觉锚点来激活选择性注意机制，建议增加辅助场景或视觉层次感。",
            }
        )

    if text_density > config.TEXT_DENSITY_HIGH:
        advice.append(
            {
                "priority": "高",
                "category": "文字密度",
                "issue": f"文字密度为 {text_density:.4f}，高于阈值 {config.TEXT_DENSITY_HIGH}",
                "suggestion": "文案信息过密可能引发信息过载与决策瘫痪，建议精简文字至 1-2 个核心卖点，在首因效应黄金期内完成价值传达。",
            }
        )

    if subject_area_ratio < config.SUBJECT_AREA_RATIO_LOW:
        advice.append(
            {
                "priority": "中",
                "category": "主体聚焦",
                "issue": (
                    f"主体占比为 {subject_area_ratio:.4f}，低于阈值 "
                    f"{config.SUBJECT_AREA_RATIO_LOW}"
                ),
                "suggestion": "主体面积偏小会抬高用户寻找视觉焦点的认知成本，建议放大主体或压缩非核心背景区域，增强中心聚焦感。",
            }
        )

    if not advice:
        advice.append(
            {
                "priority": "低",
                "category": "综合评估",
                "issue": "当前主要指标均在合理区间内。",
                "suggestion": "主图表现良好，建议保持现有方向并做小步迭代验证。",
            }
        )

    priority_order = ("高", "中", "低")
    advice.sort(key=lambda item: priority_order.index(item["priority"]))
    return advice
