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

    lines: list[str] = [f"预测 CTR 原始值: {predicted_ctr:.4f}"]

    lines.append("1. 认知负荷理论分析")
    if entropy > 7.5 or text_density > 0.3:
        lines.append("画面元素偏多或文案偏密，用户在短时间内更容易产生认知负荷。")
        lines.append("建议减少冗余装饰和文字，只保留 1 到 2 个核心卖点。")
    else:
        lines.append("视觉信息相对清爽，用户更容易快速抓住商品重点。")

    lines.append("2. 主体视觉与图地关系分析")
    if subject_area_ratio < 0.2:
        lines.append("主体占比偏小，背景更容易分散注意力。")
        lines.append("建议放大主体，或通过弱化背景边缘来突出商品。")
    elif subject_area_ratio > 0.6:
        lines.append("主体足够突出，能够较快形成视觉焦点。")
    else:
        lines.append("主体占比适中，可以继续用更明确的色彩对比强化轮廓。")

    lines.append("3. 色彩唤醒分析")
    if color_saturation > 0.6:
        lines.append("色彩饱和度较高，适合需要强刺激和冲动点击的场景。")
    elif color_saturation < 0.3:
        lines.append("整体色调偏克制，适合高级感表达，但在信息流里可能不够抓眼。")
        lines.append("如果目标是快消转化，建议在焦点区域补充更高唤醒色。")
    else:
        lines.append("色彩饱和度处于舒适区间，整体观感比较稳定。")

    return {
        "lines": lines,
        "text": "\n".join(lines),
    }
