# -*- coding: utf-8 -*-
"""基于规则生成主图优化建议。"""

import config


def _to_float(value: object, default: float = 0.0) -> float:
    """把值转成 float，失败时返回默认值。"""
    try:
        return float(value)
    except Exception:
        return default


def _to_int(value: object, default: int = 0) -> int:
    """把值转成 int，失败时返回默认值。"""
    try:
        return int(value)
    except Exception:
        return default


def _to_optional_int(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _get_optional_float(source: dict, key: str) -> float | None:
    if key not in source:
        return None
    try:
        return float(source.get(key))
    except Exception:
        return None


def generate_advice(features: dict, ctr_score: float, ctr_percentile: int | None) -> list[dict]:
    """按优先级返回主图优化建议。"""
    entropy = _to_float(features.get("entropy", 0.0))
    text_density = _to_float(features.get("text_density", 0.0))
    contrast = _get_optional_float(features, "contrast")
    brightness = _get_optional_float(features, "brightness")
    percentile = _to_optional_int(ctr_percentile)
    score = _to_float(ctr_score, 0.0)

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

    if contrast is not None and contrast < config.CONTRAST_LOW:
        advice.append(
            {
                "priority": "高",
                "category": "颜色对比度",
                "issue": f"颜色对比度为 {contrast:.4f}，低于阈值 {config.CONTRAST_LOW}",
                "suggestion": "主体与背景分离度不足，选择性注意理论表明用户难以快速锁定显著目标，建议使用更高对比度背景或补色搭配来强化视觉显著性。",
            }
        )
    elif contrast is not None and contrast > config.CONTRAST_HIGH:
        advice.append(
            {
                "priority": "中",
                "category": "颜色对比度",
                "issue": f"颜色对比度为 {contrast:.4f}，高于阈值 {config.CONTRAST_HIGH}",
                "suggestion": "多个高对比度区域可能分散用户的选择性注意力，建议适度柔化非主体区域色调，确保单一视觉焦点。",
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

    if brightness is not None and brightness < config.BRIGHTNESS_LOW:
        advice.append(
            {
                "priority": "高",
                "category": "图像亮度",
                "issue": f"亮度为 {brightness:.4f}，低于阈值 {config.BRIGHTNESS_LOW}",
                "suggestion": "整体偏暗削弱了主体的视觉显著性，不利于选择性注意的激活，建议提升曝光或补光。",
            }
        )
    elif brightness is not None and brightness > config.BRIGHTNESS_HIGH:
        advice.append(
            {
                "priority": "中",
                "category": "图像亮度",
                "issue": f"亮度为 {brightness:.4f}，高于阈值 {config.BRIGHTNESS_HIGH}",
                "suggestion": "画面过亮可能导致细节层次丢失，降低视觉信息的区分度，建议适当降低亮度并保留层次。",
            }
        )

    if percentile is not None and percentile < config.CTR_PCT_LOW:
        advice.append(
            {
                "priority": "高",
                "category": "综合评分",
                "issue": (
                    f"CTR 预测分数为 {score:.4f}，当前仅优于 {percentile}% 同类商品，"
                    f"低于阈值 {config.CTR_PCT_LOW}%"
                ),
                "suggestion": "综合认知诊断表现偏弱，建议参考高 CTR 样式，从认知负荷、信息密度、视觉显著性、中心构图四个维度进行结构性重设计。",
            }
        )
    elif percentile is not None and config.CTR_PCT_LOW <= percentile < config.CTR_PCT_MID:
        advice.append(
            {
                "priority": "中",
                "category": "综合评分",
                "issue": (
                    f"CTR 预测分数为 {score:.4f}，当前优于 {percentile}% 同类商品，"
                    f"仍低于目标阈值 {config.CTR_PCT_MID}%"
                ),
                "suggestion": "整体有优化空间，建议优先修复高优先级问题并持续 A/B 测试。",
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
