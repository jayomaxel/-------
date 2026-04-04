"""
Heatmap generation for E's XGBoost-based CTR pipeline.

The original Grad-CAM path does not apply here because the deployed predictor
is not a neural network classifier. This module therefore uses Occlusion
Sensitivity plus OCR text-region fusion:
- occlusion importance weight: 0.8
- OCR text-region weight: 0.2

Performance note:
- Each heatmap may trigger hundreds of repeated feature extractions.
- CPU runtime is typically around 30-120 seconds per image.
- OCR inside feature extraction is often the main bottleneck.
"""

from __future__ import annotations

import logging

import cv2
import numpy as np
import pytesseract

import config
from modules.ctr_predictor import load_model_bundle, predict_ctr
from modules.feature_extractor import extract_features
from modules.preprocessor import preprocess_image


def _prepare_image(image_array: np.ndarray) -> np.ndarray:
    """
    Normalize input into the preprocessor contract: RGB float32 in [0, 1].
    """

    if (
        isinstance(image_array, np.ndarray)
        and image_array.ndim == 3
        and image_array.shape[2] == 3
        and np.issubdtype(image_array.dtype, np.floating)
        and tuple(image_array.shape[:2]) == (config.IMG_SIZE[1], config.IMG_SIZE[0])
        and float(np.min(image_array)) >= 0.0
        and float(np.max(image_array)) <= 1.0
    ):
        return np.clip(image_array.astype(np.float32), 0.0, 1.0)

    return preprocess_image(image_array)


def _to_uint8_rgb(image_array: np.ndarray) -> np.ndarray:
    return np.clip(image_array * 255.0, 0, 255).astype(np.uint8)


def _iter_window_positions(length: int, patch_size: int, stride: int) -> list[int]:
    if length <= patch_size:
        return [0]

    positions = list(range(0, length - patch_size + 1, stride))
    last_start = length - patch_size
    if not positions or positions[-1] != last_start:
        positions.append(last_start)
    return positions


def _build_text_map(image_uint8: np.ndarray) -> np.ndarray:
    height, width = image_uint8.shape[:2]
    text_map = np.zeros((height, width), dtype=np.float32)

    try:
        ocr_data = pytesseract.image_to_data(image_uint8, output_type=pytesseract.Output.DICT)
        conf_list = ocr_data.get("conf", [])

        for index, conf in enumerate(conf_list):
            try:
                conf_value = float(conf)
            except (TypeError, ValueError):
                continue

            if conf_value <= 60:
                continue

            left = int(ocr_data["left"][index])
            top = int(ocr_data["top"][index])
            box_width = int(ocr_data["width"][index])
            box_height = int(ocr_data["height"][index])

            x1 = max(0, left)
            y1 = max(0, top)
            x2 = min(width, x1 + max(0, box_width))
            y2 = min(height, y1 + max(0, box_height))

            if x2 > x1 and y2 > y1:
                text_map[y1:y2, x1:x2] += 1.0
    except Exception:  # noqa: BLE001
        return text_map

    if float(text_map.max()) > 0:
        text_map = text_map / float(text_map.max())
    return text_map


def generate_heatmap(
    image_array: np.ndarray,
    dataset_key: str = config.DEFAULT_DATASET,
) -> np.ndarray:
    """
    Generate an occlusion-sensitivity heatmap blended with OCR text regions.

    Args:
        image_array: Preprocessor output with shape `(224, 224, 3)`, float32 in `[0, 1]`.
        dataset_key: Dataset selector used to resolve model artifacts.

    Returns:
        A `(224, 224, 3)` RGB uint8 array ready for UI display.
    """

    prepared_image = _prepare_image(image_array)
    original_uint8 = _to_uint8_rgb(prepared_image)

    bundle = load_model_bundle(dataset_key)
    if bundle is None:
        logging.warning("热力图模块：模型未就绪，返回原图")
        return original_uint8

    try:
        height, width = prepared_image.shape[:2]
        patch_size = max(1, min(height, width) // 14)
        stride = max(1, min(height, width) // 28)

        base_features = extract_features(prepared_image)
        pred_base, _ = predict_ctr(base_features, dataset_key)

        importance_map = np.zeros((height, width), dtype=np.float32)
        counts = np.zeros((height, width), dtype=np.float32)

        y_positions = _iter_window_positions(height, patch_size, stride)
        x_positions = _iter_window_positions(width, patch_size, stride)

        for y in y_positions:
            for x in x_positions:
                occluded = prepared_image.copy()
                patch = occluded[y : y + patch_size, x : x + patch_size]
                mean_color = np.mean(patch, axis=(0, 1), keepdims=True)
                occluded[y : y + patch_size, x : x + patch_size] = mean_color

                occ_features = extract_features(occluded)
                pred_occ, _ = predict_ctr(occ_features, dataset_key)
                importance = max(0.0, float(pred_base - pred_occ))

                importance_map[y : y + patch_size, x : x + patch_size] += importance
                counts[y : y + patch_size, x : x + patch_size] += 1.0

        valid_mask = counts > 0
        importance_map[valid_mask] = importance_map[valid_mask] / counts[valid_mask]

        ksize = max(1, patch_size | 1)
        occ_heat = cv2.GaussianBlur(importance_map, (ksize, ksize), 0)
        occ_heat = (occ_heat - occ_heat.min()) / (occ_heat.max() - occ_heat.min() + 1e-8)

        text_map = _build_text_map(original_uint8)

        combined = 0.8 * occ_heat + 0.2 * text_map
        combined = (
            (combined - combined.min()) / (combined.max() - combined.min() + 1e-8) * 255
        ).astype(np.uint8)

        colormap = cv2.applyColorMap(combined, cv2.COLORMAP_JET)
        colormap_rgb = cv2.cvtColor(colormap, cv2.COLOR_BGR2RGB)
        result = cv2.addWeighted(original_uint8, 0.7, colormap_rgb, 0.3, 0)
        return result
    except Exception as exc:  # noqa: BLE001
        logging.error("热力图生成失败：%s", exc)
        return original_uint8
