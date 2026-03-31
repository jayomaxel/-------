"""
Heatmap adapter for Streamlit pipeline.

This module bridges preprocessed image arrays to the core CTR heatmap logic in
`gradcam_analysis.generate_ctr_heatmap`, which uses Occlusion Sensitivity
(not Grad-CAM). Each image can take roughly 30-120 seconds.

Callers should wrap `generate_heatmap(...)` with `st.spinner(...)`.
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

import config

CTR_DIR = (Path(__file__).resolve().parents[1] / "ctr").resolve()
if str(CTR_DIR) not in sys.path:
    sys.path.insert(0, str(CTR_DIR))
try:
    from gradcam_analysis import generate_ctr_heatmap as _core_heatmap
except Exception as exc:  # noqa: BLE001
    _core_heatmap = None
    logging.warning("Heatmap fallback: cannot import core heatmap module: %s", exc)


def _to_uint8_rgb(image_array: np.ndarray) -> np.ndarray:
    """Convert an image array (float [0,1] or integer [0,255]) to uint8 RGB."""
    if not isinstance(image_array, np.ndarray):
        raise TypeError("image_array must be a numpy.ndarray")
    if image_array.ndim != 3 or image_array.shape[2] != 3:
        raise ValueError("image_array must have shape (H, W, 3)")

    if np.issubdtype(image_array.dtype, np.floating):
        return (image_array * 255).clip(0, 255).astype(np.uint8)
    return image_array.clip(0, 255).astype(np.uint8)


def generate_heatmap(
    image_array: np.ndarray,
    dataset_key: str = config.DEFAULT_DATASET,
) -> np.ndarray:
    """
    Generate a CTR attention heatmap image as RGB uint8 for direct UI display.

    Notes:
        - Core method is Occlusion Sensitivity and may take 30-120 seconds.
        - On configured fallback cases, this function degrades to returning the
          original image (uint8 RGB) and does not raise.

    Args:
        image_array: Preprocessor output (224, 224, 3), float32 in [0, 1].
        dataset_key: Dataset selector used to resolve model path.

    Returns:
        A (224, 224, 3) uint8 RGB NumPy array for `st.image`.
    """
    img_rgb = _to_uint8_rgb(image_array)

    dataset_cfg = config.DATASETS.get(dataset_key)
    model_path_raw = (dataset_cfg or {}).get("model_path")
    if not model_path_raw:
        logging.warning(
            "Heatmap fallback: dataset '%s' has no configured model_path.",
            dataset_key,
        )
        return img_rgb

    model_path = Path(model_path_raw)
    if not model_path.is_absolute():
        model_path = (Path(config.ROOT_DIR) / model_path).resolve()

    if not model_path.exists():
        logging.warning(
            "Heatmap fallback: model file missing for dataset '%s': %s",
            dataset_key,
            model_path,
        )
        return img_rgb

    if _core_heatmap is None:
        logging.warning("Heatmap fallback: core heatmap function unavailable.")
        return img_rgb

    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    tmp_input = ""
    tmp_output = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as fin:
            tmp_input = fin.name
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as fout:
            tmp_output = fout.name

        cv2.imwrite(tmp_input, img_bgr)

        try:
            result_bgr = _core_heatmap(
                img_path=tmp_input,
                model_path=str(model_path),
                save_heatmap_path=tmp_output,
            )
            if result_bgr is None:
                logging.warning(
                    "Heatmap fallback: core returned None for dataset '%s'.",
                    dataset_key,
                )
                return img_rgb
            return cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
        except Exception as exc:  # noqa: BLE001
            logging.warning(
                "Heatmap fallback: core heatmap failed for dataset '%s': %s",
                dataset_key,
                exc,
            )
            return img_rgb
    finally:
        for path in (tmp_input, tmp_output):
            if path:
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass
