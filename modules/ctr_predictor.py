"""
CTR prediction adapter for the XGBoost bundle delivered by E.

This module aligns runtime inference with the actual artifact layout used by
training:
- model and scaler are saved as separate pickle files
- feature input is 514 dimensions: [entropy, text_density, clip_vector(512)]
- no PCA projection is applied
- no ctr_quantiles metadata is available, so percentile uses a linear fallback
"""

from __future__ import annotations

import functools
import logging
from pathlib import Path

import joblib
import numpy as np

import config


def _resolve_path(path_value: str) -> Path:
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (config.ROOT_DIR / path_obj).resolve()


def _get_dataset_config(dataset_key: str) -> dict:
    if dataset_key not in config.DATASETS:
        valid_keys = ", ".join(config.DATASETS.keys())
        raise ValueError(f"Unknown dataset_key: {dataset_key}. Available dataset keys: {valid_keys}")
    return config.DATASETS[dataset_key]


def _build_feature_vector(features: dict) -> np.ndarray:
    scalar = np.asarray(
        [
            float(features.get("entropy", 0.0)),
            float(features.get("text_density", 0.0)),
        ],
        dtype=np.float32,
    )

    clip_vector = np.asarray(
        features.get("clip_vector", np.zeros(config.CLIP_DIM, dtype=np.float32)),
        dtype=np.float32,
    ).reshape(-1)

    if clip_vector.size < config.CLIP_DIM:
        clip_vector = np.pad(clip_vector, (0, config.CLIP_DIM - clip_vector.size))
    elif clip_vector.size > config.CLIP_DIM:
        clip_vector = clip_vector[: config.CLIP_DIM]

    return np.concatenate([scalar, clip_vector.astype(np.float32)]).reshape(1, -1)


@functools.lru_cache(maxsize=8)
def load_model_bundle(dataset_key: str = config.DEFAULT_DATASET) -> dict | None:
    """
    Load the dataset-specific XGBoost model bundle from separate pickle files.

    Args:
        dataset_key: Dataset key registered in `config.DATASETS`.

    Returns:
        A dict with `model` and `scaler` when both files are available and
        load successfully; otherwise `None`.
    """

    dataset_cfg = _get_dataset_config(dataset_key)
    model_path = _resolve_path(dataset_cfg["model_path"])
    scaler_path = _resolve_path(dataset_cfg["scaler_path"])

    if not model_path.exists():
        logging.warning("CTR predictor: missing model file for dataset '%s': %s", dataset_key, model_path)
        return None

    if not scaler_path.exists():
        logging.warning(
            "CTR predictor: missing scaler file for dataset '%s': %s",
            dataset_key,
            scaler_path,
        )
        return None

    try:
        xgb_model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
    except Exception as exc:  # noqa: BLE001
        logging.warning("CTR predictor: failed to load bundle for dataset '%s': %s", dataset_key, exc)
        return None

    return {"model": xgb_model, "scaler": scaler}


def predict_ctr(features: dict, dataset_key: str = config.DEFAULT_DATASET) -> tuple[float, int]:
    """
    Predict CTR score and percentile from extracted image features.

    The feature layout is strictly:
    [entropy, text_density, clip_vector(512)]
    Contrast, brightness, and saturation are intentionally excluded because
    E's delivered model was not trained with them.

    Args:
        features: Feature dict returned by `modules.feature_extractor.extract_features()`.
        dataset_key: Dataset key registered in `config.DATASETS`.

    Returns:
        A tuple of `(score, percentile)`.
    """

    bundle = load_model_bundle(dataset_key)
    if bundle is None:
        logging.warning("当前为Mock值，模型未就绪")
        return 0.5, 50

    X = _build_feature_vector(features)
    expected_dim = X.shape[1]
    scaler_dim = getattr(bundle["scaler"], "n_features_in_", expected_dim)

    if int(scaler_dim) != int(expected_dim):
        logging.warning(
            "CTR predictor: scaler for dataset '%s' expects %s features, but runtime builds %s.",
            dataset_key,
            scaler_dim,
            expected_dim,
        )
        logging.warning("当前为Mock值，模型未就绪")
        return 0.5, 50

    try:
        X_scaled = bundle["scaler"].transform(X)[0]
        score = float(bundle["model"].predict(X_scaled.reshape(1, -1))[0])
    except Exception as exc:  # noqa: BLE001
        logging.warning("CTR predictor: inference failed for dataset '%s': %s", dataset_key, exc)
        logging.warning("当前为Mock值，模型未就绪")
        return 0.5, 50

    score = float(np.clip(score, 0.0, 1.0))
    score = float(np.round(score, 4))
    percentile = int(np.clip(score * 100, 1, 99))
    return score, percentile
