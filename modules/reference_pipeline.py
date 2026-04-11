# -*- coding: utf-8 -*-
from __future__ import annotations

import functools
from pathlib import Path

import cv2
import joblib
import numpy as np
from PIL import Image

import config

try:
    import pytesseract
except Exception:  # pragma: no cover - optional runtime dependency
    pytesseract = None

try:
    import torch
except Exception:  # pragma: no cover - optional runtime dependency
    torch = None

try:
    import clip
except Exception:  # pragma: no cover - optional runtime dependency
    clip = None


def _resolve_path(path_value: str | Path) -> Path:
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (config.ROOT_DIR / path_obj).resolve()


def _read_image_bgr(image_input: str | Path | np.ndarray) -> np.ndarray:
    if isinstance(image_input, np.ndarray):
        image = np.asarray(image_input)
        if image.ndim == 2:
            return cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGBA2BGR)
        if image.ndim == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2BGR)
        raise ValueError(f"Unsupported image array shape: {image.shape}")

    image_path = _resolve_path(image_input)
    image_bytes = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Failed to read image: {image_path}")
    return image


def _resize_bgr(image_bgr: np.ndarray) -> np.ndarray:
    width, height = config.IMG_SIZE
    return cv2.resize(image_bgr, (width, height))


def get_image_entropy(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    hist_sum = float(hist.sum())
    if hist_sum <= 0:
        return 0.0
    hist = hist / hist_sum
    hist_nonzero = hist[hist > 0]
    return float(-np.sum(hist_nonzero * np.log2(hist_nonzero)))


def get_text_density(image_path: str | Path) -> float:
    if pytesseract is None:
        return 0.0

    try:
        img = Image.open(_resolve_path(image_path)).convert("RGB").resize(config.IMG_SIZE)
        img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        area = float(config.IMG_SIZE[0] * config.IMG_SIZE[1])
        ocr_data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)

        total_area = 0.0
        for conf, width, height in zip(
            ocr_data.get("conf", []),
            ocr_data.get("width", []),
            ocr_data.get("height", []),
        ):
            try:
                conf_value = float(conf)
            except (TypeError, ValueError):
                conf_value = -1.0

            if conf_value > 60:
                total_area += float(int(width or 0) * int(height or 0))

        return total_area / area if area > 0 else 0.0
    except Exception:
        return 0.0


def get_subject_area_ratio(image_bgr: np.ndarray) -> float:
    try:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        threshold = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2,
        )
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0.0

        max_area = max(cv2.contourArea(contour) for contour in contours)
        height, width = image_bgr.shape[:2]
        return float(max_area / float(width * height))
    except Exception:
        return 0.0


def get_edge_density(image_bgr: np.ndarray) -> float:
    try:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        height, width = image_bgr.shape[:2]
        return float(np.count_nonzero(edges)) / float(width * height)
    except Exception:
        return 0.0


def get_color_saturation(image_bgr: np.ndarray) -> float:
    try:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1].astype(np.float32)
        return float(np.mean(saturation) / 255.0)
    except Exception:
        return 0.0


@functools.lru_cache(maxsize=1)
def _load_clip_runtime():
    if clip is None or torch is None:
        return None, None, None

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(config.CLIP_MODEL_NAME, device=device)
    model.eval()
    return model, preprocess, device


def get_clip_feature(image_path: str | Path) -> np.ndarray:
    try:
        model, preprocess, device = _load_clip_runtime()
        if model is None or preprocess is None or device is None:
            return np.zeros(config.CLIP_DIM, dtype=np.float32)

        image = preprocess(Image.open(_resolve_path(image_path)).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            feature = model.encode_image(image)

        feature = feature.float().cpu().numpy().reshape(-1)
        norm = float(np.linalg.norm(feature))
        if norm > 1e-6:
            feature = feature / norm
        return feature.astype(np.float32)
    except Exception:
        return np.zeros(config.CLIP_DIM, dtype=np.float32)


@functools.lru_cache(maxsize=1)
def _load_reference_bundle() -> tuple[object, object]:
    model = joblib.load(_resolve_path(config.MODEL_PATH))
    scaler = joblib.load(_resolve_path(config.SCALER_PATH))
    return model, scaler


def extract_reference_features(image_path: str | Path) -> dict[str, object]:
    image_bgr = _resize_bgr(_read_image_bgr(image_path))
    return {
        "entropy": get_image_entropy(image_bgr),
        "text_density": get_text_density(image_path),
        "subject_area_ratio": get_subject_area_ratio(image_bgr),
        "edge_density": get_edge_density(image_bgr),
        "color_saturation": get_color_saturation(image_bgr),
        "clip_vector": get_clip_feature(image_path),
    }


def predict_reference_ctr(reference_features: dict[str, object]) -> float:
    model, scaler = _load_reference_bundle()
    scalar_values = [
        float(reference_features.get("entropy", 0.0)),
        float(reference_features.get("text_density", 0.0)),
        float(reference_features.get("subject_area_ratio", 0.0)),
        float(reference_features.get("edge_density", 0.0)),
        float(reference_features.get("color_saturation", 0.0)),
    ]
    clip_vector = np.asarray(
        reference_features.get("clip_vector", np.zeros(config.CLIP_DIM, dtype=np.float32)),
        dtype=np.float32,
    ).reshape(-1)

    feature_vector = np.array([scalar_values + list(clip_vector)], dtype=np.float32)
    scaled_vector = scaler.transform(feature_vector)
    return float(model.predict(scaled_vector)[0])


def generate_attention_heatmap(image_input: str | Path | np.ndarray) -> np.ndarray:
    image_bgr = _read_image_bgr(image_input)
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    l_mean = float(np.mean(l_channel))
    a_mean = float(np.mean(a_channel))
    b_mean = float(np.mean(b_channel))
    saliency = np.sqrt(
        np.square(l_channel.astype(np.float32) - l_mean)
        + np.square(a_channel.astype(np.float32) - a_mean)
        + np.square(b_channel.astype(np.float32) - b_mean)
    )

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edges_blurred = cv2.GaussianBlur(edges, (15, 15), 0)

    heatmap_gray = cv2.normalize(saliency + edges_blurred, None, 0, 255, cv2.NORM_MINMAX)
    heatmap_gray = heatmap_gray.astype(np.uint8)
    heatmap_gray = cv2.GaussianBlur(heatmap_gray, (31, 31), 0)

    heatmap_color = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(image_bgr, 0.6, heatmap_color, 0.4, 0)
    return cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)


def generate_psychological_report(reference_features: dict[str, object], predicted_ctr: float) -> dict[str, object]:
    entropy = float(reference_features.get("entropy", 0.0))
    text_density = float(reference_features.get("text_density", 0.0))
    subject_area_ratio = float(reference_features.get("subject_area_ratio", 0.0))
    color_saturation = float(reference_features.get("color_saturation", 0.0))
    edge_density = float(reference_features.get("edge_density", 0.0))

    lines: list[str] = [f"预测 CTR 原始值: {predicted_ctr:.4f}"]

    lines.append("")
    lines.append("【认知负荷理论分析】")
    cognitive_load_high = entropy > config.ENTROPY_HIGH or text_density > config.TEXT_DENSITY_HIGH
    if cognitive_load_high:
        overload_factors = []
        if entropy > config.ENTROPY_HIGH:
            overload_factors.append(f"视觉熵({entropy:.2f})超出阈值({config.ENTROPY_HIGH})")
        if text_density > config.TEXT_DENSITY_HIGH:
            overload_factors.append(
                f"文字密度({text_density:.2f})超出阈值({config.TEXT_DENSITY_HIGH})"
            )
        lines.append(
            f"{'、'.join(overload_factors)}，视觉复杂度可能超出用户工作记忆容量，"
            "增加内在认知负担，触发'避难趋易'本能，降低点击意愿。"
        )
        lines.append(
            f"边缘密度当前为 {edge_density:.2f}，建议继续结合背景纹理观察是否在放大解析负担。"
        )
        lines.append("建议：精简背景元素与非核心文案，降低用户完成首轮理解时的视觉解析成本。")
    elif entropy < config.ENTROPY_LOW:
        lines.append(
            f"视觉熵({entropy:.2f})低于阈值({config.ENTROPY_LOW})，"
            "画面信息层次单一，缺乏吸引用户停留的视觉锚点。"
        )
        lines.append("建议：适度增加视觉层次感，如场景化背景或辅助元素，但避免过度堆砌。")
    else:
        lines.append(
            f"视觉熵({entropy:.2f})与文字密度({text_density:.2f})未触发高负荷阈值，"
            "整体认知负荷相对平稳。"
        )
        lines.append(
            f"边缘密度当前为 {edge_density:.2f}，可继续关注背景纹理是否在局部削弱主体识别效率。"
        )

    lines.append("")
    lines.append("【信息过载理论分析】")
    if text_density > config.TEXT_DENSITY_HIGH:
        if entropy > config.ENTROPY_HIGH:
            lines.append(
                f"文字密度({text_density:.2f})与视觉熵({entropy:.2f})同时偏高，"
                "信息传递维度出现拥挤，用户视觉注视点可能发生无序跳跃，"
                "存在'决策瘫痪'(Decision Paralysis)风险。"
            )
            lines.append(
                f"边缘密度当前为 {edge_density:.2f}，建议同步检查背景纹理是否在继续抬高信息噪音。"
            )
            lines.append("建议：削减非核心文案和装饰信息，确保用户能更早识别核心卖点。")
        else:
            lines.append(
                f"文字密度({text_density:.2f})超过阈值({config.TEXT_DENSITY_HIGH})，"
                "即使不额外叠加新的数值判断，密集文案本身也可能构成信息噪音，"
                "干扰核心卖点的快速传达。"
            )
            lines.append(
                f"边缘密度当前为 {edge_density:.2f}，可进一步核对背景元素是否还在分散文案主次。"
            )
            lines.append("建议：精简文案为核心卖点表达，并为主体和关键信息留出呼吸空间。")
    else:
        lines.append(
            f"文字密度({text_density:.2f})未超过阈值({config.TEXT_DENSITY_HIGH})，"
            "信息输入通道相对克制，不易直接形成信息过载。"
        )
        lines.append(
            f"边缘密度当前为 {edge_density:.2f}，后续仍可结合实际画面检查是否存在多余装饰噪音。"
        )

    lines.append("")
    lines.append("【选择性注意理论分析】")
    lines.append(
        f"当前主体占比为 {subject_area_ratio:.2f}，边缘密度为 {edge_density:.2f}，颜色饱和度为 {color_saturation:.2f}。"
    )
    if entropy > config.ENTROPY_HIGH or text_density > config.TEXT_DENSITY_HIGH:
        lines.append(
            "在视觉熵或文字密度偏高的情况下，背景纹理和非核心信息更容易与主体竞争注意力，"
            "削弱单一视觉焦点。"
        )
        lines.append(
            "建议：优先减少会抢走第一视线的背景元素和文字信息，再观察主体是否足够先被看到。"
        )
    elif entropy < config.ENTROPY_LOW:
        lines.append(
            "画面整体较简洁时，用户是否会把第一眼停留在主体上，更依赖主体占比和局部显著线索的组织方式。"
        )
        lines.append(
            "建议：保留简洁结构的同时，让主体、文案和辅助元素围绕同一个注意力锚点组织。"
        )
    else:
        lines.append(
            "在当前特征体系下，选择性注意主要还是通过主体占比、边缘信息和色彩唤醒来判断焦点是否集中。"
        )
        lines.append("建议：检查这些线索是否共同服务于主体，而不是让用户在背景和卖点之间来回跳转。")

    lines.append("")
    lines.append("【中心偏好理论分析】")
    lines.append(
        f"当前主体占比为 {subject_area_ratio:.2f}。中心偏好理论关注的是用户能否在初始注视阶段"
        "迅速锁定主体，因此这个指标更适合作为构图聚焦程度的辅助信号。"
    )
    lines.append(
        "在不额外引入新数值阈值的前提下，建议回到实际构图检查主体是否稳定落在中心关注区，"
        "以及主要信息是否围绕主体组织。"
    )
    lines.append("建议：尽量减少用户寻找焦点的路径成本，让主体在首轮浏览中更快被识别。")

    return {
        "lines": lines,
        "text": "\n".join(lines),
    }
