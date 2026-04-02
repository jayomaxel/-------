from __future__ import annotations

import functools
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import config


def _round4(value: float) -> float:
    rounded = float(np.round(float(value), 4))
    return 0.0 if rounded == 0.0 else rounded


def _resolve_path(path_value: str) -> Path:
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (config.ROOT_DIR / path_obj).resolve()


def _get_dataset_config(dataset_key: str) -> dict:
    if dataset_key not in config.DATASETS:
        valid_keys = ', '.join(config.DATASETS.keys())
        raise ValueError(f'Unknown dataset_key: {dataset_key}. Available dataset keys: {valid_keys}')
    return config.DATASETS[dataset_key]


def _mock_ctr_from_features(features: dict) -> tuple[float, int]:
    score = config.CTR_PCT_MID / 100.0
    entropy = float(features.get('entropy', 0.0))
    contrast = float(features.get('contrast', 0.0))
    text_density = float(features.get('text_density', 0.0))
    brightness = float(features.get('brightness', 0.0))

    if entropy > config.ENTROPY_HIGH:
        score -= 0.08
    if contrast < config.CONTRAST_LOW:
        score -= 0.08
    if text_density > config.TEXT_DENSITY_HIGH:
        score -= 0.08
    if brightness < config.BRIGHTNESS_LOW or brightness > config.BRIGHTNESS_HIGH:
        score -= 0.06

    score = float(np.clip(score, 0.0, 1.0))
    percentile = int(round(score * 100))
    return _round4(score), percentile


def _build_feature_vector(features: dict) -> np.ndarray:
    scalar_values = [float(features.get(col, 0.0)) for col in config.FEATURE_SCALAR_COLS]
    clip_vector = np.asarray(features.get('clip_vector', np.zeros(config.CLIP_DIM)), dtype=np.float32).reshape(-1)

    if clip_vector.size < config.CLIP_DIM:
        clip_vector = np.pad(clip_vector, (0, config.CLIP_DIM - clip_vector.size))
    elif clip_vector.size > config.CLIP_DIM:
        clip_vector = clip_vector[: config.CLIP_DIM]

    return np.concatenate([np.asarray(scalar_values, dtype=np.float32), clip_vector.astype(np.float32)])


@functools.lru_cache(maxsize=8)
def _load_reference_ctr(dataset_key: str) -> np.ndarray:
    dataset_cfg = _get_dataset_config(dataset_key)
    excel_path = _resolve_path(dataset_cfg['excel_path'])
    dataframe = pd.read_excel(excel_path)
    if config.COL_CTR not in dataframe.columns:
        return np.array([], dtype=np.float32)
    ctr_values = pd.to_numeric(dataframe[config.COL_CTR], errors='coerce').dropna().to_numpy(dtype=np.float32)
    return ctr_values


@functools.lru_cache(maxsize=8)
def _load_model_and_scaler(dataset_key: str):
    dataset_cfg = _get_dataset_config(dataset_key)
    model_path = _resolve_path(dataset_cfg['model_path'])
    scaler_path = _resolve_path(dataset_cfg['scaler_path'])

    if not model_path.exists():
        return None, None

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path) if scaler_path.exists() else None
    return model, scaler


def _score_to_percentile(score: float, reference_ctr: np.ndarray) -> int:
    if reference_ctr.size == 0:
        if 0.0 <= score <= 1.0:
            return int(round(np.clip(score, 0.0, 1.0) * 100))
        return int(np.clip(round(score), 0, 100))

    pct = float(np.mean(reference_ctr <= score) * 100.0)
    return int(np.clip(round(pct), 0, 100))


def predict_ctr(features: dict, dataset_key: str = config.DEFAULT_DATASET) -> tuple[float, int]:
    model, scaler = _load_model_and_scaler(dataset_key)
    reference_ctr = _load_reference_ctr(dataset_key)

    if model is None:
        return _mock_ctr_from_features(features)

    feature_vector = _build_feature_vector(features).reshape(1, -1)
    if scaler is not None:
        feature_vector = scaler.transform(feature_vector)

    raw_score = float(model.predict(feature_vector)[0])
    if not np.isfinite(raw_score):
        return _mock_ctr_from_features(features)

    ctr_score = _round4(raw_score)
    ctr_percentile = _score_to_percentile(raw_score, reference_ctr)
    return ctr_score, ctr_percentile
