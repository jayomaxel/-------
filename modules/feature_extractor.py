from __future__ import annotations

import functools

import cv2
import numpy as np
from PIL import Image

import config

try:
    import torch
except Exception:  # pragma: no cover - optional runtime dependency
    torch = None

try:
    import clip
except Exception:  # pragma: no cover - optional runtime dependency
    clip = None


def _round4(value: float) -> float:
    rounded = float(np.round(float(value), 4))
    return 0.0 if rounded == 0.0 else rounded


def _to_uint8_rgb(image_array: np.ndarray) -> np.ndarray:
    if not isinstance(image_array, np.ndarray):
        raise TypeError('image_array must be a numpy.ndarray')
    if image_array.ndim != 3 or image_array.shape[2] != 3:
        raise ValueError('image_array must have shape (H, W, 3)')

    if np.issubdtype(image_array.dtype, np.floating):
        image = np.clip(image_array, 0.0, 1.0) * 255.0
    else:
        image = np.clip(image_array, 0, 255)

    return image.astype(np.uint8)


def _compute_entropy(image_rgb_uint8: np.ndarray) -> float:
    gray = cv2.cvtColor(image_rgb_uint8, cv2.COLOR_RGB2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    total = float(hist.sum())
    if total <= 0:
        return 0.0
    prob = hist / total
    prob = prob[prob > 0]
    entropy = -np.sum(prob * np.log2(prob))
    return _round4(entropy)


def _compute_contrast(image_rgb_uint8: np.ndarray) -> float:
    lab = cv2.cvtColor(image_rgb_uint8, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)

    # Convert OpenCV LAB scale to approximate CIELAB scale for Delta-E distance.
    lab[:, 0] = lab[:, 0] * (100.0 / 255.0)
    lab[:, 1] = lab[:, 1] - 128.0
    lab[:, 2] = lab[:, 2] - 128.0

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, _, centers = cv2.kmeans(
        lab,
        2,
        None,
        criteria,
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    delta_e = float(np.linalg.norm(centers[0] - centers[1]))
    delta_e = float(np.clip(delta_e, 0.0, 100.0))
    return _round4(delta_e)


def _compute_text_density(image_rgb_uint8: np.ndarray) -> float:
    try:
        import pytesseract
    except Exception:
        return 0.0

    height, width = image_rgb_uint8.shape[:2]
    image_area = float(height * width)
    if image_area <= 0:
        return 0.0

    try:
        ocr = pytesseract.image_to_data(
            image_rgb_uint8, output_type=pytesseract.Output.DICT
        )
    except Exception:
        return 0.0

    text_list = ocr.get('text', [])
    width_list = ocr.get('width', [])
    height_list = ocr.get('height', [])

    bbox_area_sum = 0.0
    for text, box_w, box_h in zip(text_list, width_list, height_list):
        if not str(text).strip():
            continue
        w = int(box_w)
        h = int(box_h)
        if w <= 0 or h <= 0:
            continue
        bbox_area_sum += float(w * h)

    density = min(bbox_area_sum / image_area, 1.0)
    return _round4(density)


def _compute_subject_area_ratio(image_rgb_uint8: np.ndarray) -> float:
    gray = cv2.cvtColor(image_rgb_uint8, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    thresholded = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2,
    )
    kernel = np.ones((5, 5), dtype=np.uint8)
    closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return 0.0

    image_area = float(image_rgb_uint8.shape[0] * image_rgb_uint8.shape[1])
    if image_area <= 0:
        return 0.0

    max_area = float(max(cv2.contourArea(contour) for contour in contours))
    return _round4(min(max_area / image_area, 1.0))


def _compute_edge_density(image_rgb_uint8: np.ndarray) -> float:
    gray = cv2.cvtColor(image_rgb_uint8, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    image_area = float(image_rgb_uint8.shape[0] * image_rgb_uint8.shape[1])
    if image_area <= 0:
        return 0.0
    density = float(np.count_nonzero(edges)) / image_area
    return _round4(min(density, 1.0))


def _compute_color_saturation(image_rgb_uint8: np.ndarray) -> float:
    hsv = cv2.cvtColor(image_rgb_uint8, cv2.COLOR_RGB2HSV)
    saturation = float(np.mean(hsv[:, :, 1].astype(np.float32)) / 255.0)
    return _round4(saturation)


@functools.lru_cache(maxsize=4)
def _load_clip_model(model_name: str, device_name: str):
    if torch is None:
        raise ImportError('torch package is not installed')
    if clip is None:
        raise ImportError('clip package is not installed')
    model, preprocess = clip.load(model_name, device=device_name)
    model.eval()
    return model, preprocess


def _extract_clip_vector(image_rgb_uint8: np.ndarray) -> np.ndarray:
    model, preprocess = _load_clip_model(config.CLIP_MODEL_NAME, config.CLIP_DEVICE)

    pil_image = Image.fromarray(image_rgb_uint8)
    image_tensor = preprocess(pil_image).unsqueeze(0).to(config.CLIP_DEVICE)

    with torch.no_grad():
        vector = model.encode_image(image_tensor).float().cpu().numpy().reshape(-1)

    if vector.shape[0] != config.CLIP_DIM:
        raise ValueError(f'Unexpected CLIP vector length: {vector.shape[0]}')

    norm = float(np.linalg.norm(vector))
    if norm <= 0:
        raise ValueError('CLIP vector norm is zero')

    vector = (vector / norm).astype(np.float32)
    return vector


def _compute_hsv_stats(image_rgb_uint8: np.ndarray) -> tuple[float, float]:
    hsv = cv2.cvtColor(image_rgb_uint8, cv2.COLOR_RGB2HSV)
    saturation = _compute_color_saturation(image_rgb_uint8)
    brightness = float(np.mean(hsv[:, :, 2] / 255.0))
    return _round4(brightness), _round4(saturation)


def extract_features(
    image_array: np.ndarray,
    *,
    include_clip: bool = True,
    include_text_density: bool = True,
) -> dict:
    image_rgb_uint8 = _to_uint8_rgb(image_array)

    features: dict = {
        'entropy': 0.0,
        'contrast': 0.0,
        'text_density': 0.0,
        'subject_area_ratio': 0.0,
        'edge_density': 0.0,
        'color_saturation': 0.0,
        'clip_vector': np.zeros(config.CLIP_DIM, dtype=np.float32),
        'brightness': 0.0,
        'saturation': 0.0,
    }

    try:
        features['entropy'] = _compute_entropy(image_rgb_uint8)
    except Exception:
        features['entropy'] = 0.0

    try:
        features['contrast'] = _compute_contrast(image_rgb_uint8)
    except Exception:
        features['contrast'] = 0.0

    if include_text_density:
        try:
            features['text_density'] = _compute_text_density(image_rgb_uint8)
        except Exception:
            features['text_density'] = 0.0

    try:
        features['subject_area_ratio'] = _compute_subject_area_ratio(image_rgb_uint8)
    except Exception:
        features['subject_area_ratio'] = 0.0

    try:
        features['edge_density'] = _compute_edge_density(image_rgb_uint8)
    except Exception:
        features['edge_density'] = 0.0

    try:
        features['color_saturation'] = _compute_color_saturation(image_rgb_uint8)
    except Exception:
        features['color_saturation'] = 0.0

    if include_clip:
        try:
            features['clip_vector'] = _extract_clip_vector(image_rgb_uint8)
        except Exception:
            features['clip_vector'] = np.zeros(config.CLIP_DIM, dtype=np.float32)

    try:
        brightness, saturation = _compute_hsv_stats(image_rgb_uint8)
        features['brightness'] = brightness
        features['saturation'] = saturation
    except Exception:
        features['brightness'] = 0.0
        features['saturation'] = 0.0

    if features['color_saturation'] == 0.0 and features['saturation'] != 0.0:
        features['color_saturation'] = features['saturation']

    return features
