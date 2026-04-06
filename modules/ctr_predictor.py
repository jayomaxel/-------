"""CTR 预测适配层。"""

from __future__ import annotations

import functools
import logging
from pathlib import Path

import joblib
import numpy as np

import config

MOCK_SCORE = 0.5


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


def _build_feature_vector(features: dict, scalar_cols: tuple[str, ...]) -> np.ndarray:
    scalar_values = np.asarray(
        [float(features.get(column, 0.0)) for column in scalar_cols],
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

    return np.concatenate([scalar_values, clip_vector.astype(np.float32)]).reshape(1, -1)


@functools.lru_cache(maxsize=16)
def _load_bundle(
    model_path_value: str,
    scaler_path_value: str,
    scalar_cols: tuple[str, ...],
    scope: str,
) -> dict | None:
    model_path = _resolve_path(model_path_value)
    scaler_path = _resolve_path(scaler_path_value)

    if not model_path.exists():
        logging.warning("CTR predictor: missing %s model file: %s", scope, model_path)
        return None

    if not scaler_path.exists():
        logging.warning("CTR predictor: missing %s scaler file: %s", scope, scaler_path)
        return None

    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
    except Exception as exc:  # noqa: BLE001
        logging.warning("CTR predictor: failed to load %s bundle: %s", scope, exc)
        return None

    feature_dim = len(scalar_cols) + config.CLIP_DIM
    return {
        "model": model,
        "scaler": scaler,
        "scope": scope,
        "feature_scalar_cols": scalar_cols,
        "feature_dim": feature_dim,
        "model_path": str(model_path),
        "scaler_path": str(scaler_path),
    }


def _load_global_bundle() -> dict | None:
    return _load_bundle(
        config.MODEL_PATH,
        config.SCALER_PATH,
        tuple(config.FEATURE_SCALAR_COLS),
        "global",
    )


def _load_legacy_bundle(dataset_key: str) -> dict | None:
    dataset_cfg = _get_dataset_config(dataset_key)
    return _load_bundle(
        dataset_cfg["model_path"],
        dataset_cfg["scaler_path"],
        tuple(config.LEGACY_FEATURE_SCALAR_COLS),
        f"legacy:{dataset_key}",
    )


@functools.lru_cache(maxsize=8)
def load_model_bundle(dataset_key: str = config.DEFAULT_DATASET) -> dict | None:
    global_bundle = _load_global_bundle()
    if global_bundle is not None:
        return global_bundle
    return _load_legacy_bundle(dataset_key)


def _predict_with_bundle(features: dict, bundle: dict) -> tuple[float, int | None]:
    X = _build_feature_vector(features, bundle["feature_scalar_cols"])
    expected_dim = int(bundle["feature_dim"])
    if X.shape[1] != expected_dim:
        raise ValueError(
            f"Runtime feature dimension mismatch for {bundle['scope']}: "
            f"expected {expected_dim}, got {X.shape[1]}"
        )

    scaler_dim = int(getattr(bundle["scaler"], "n_features_in_", expected_dim))
    if scaler_dim != expected_dim:
        raise ValueError(
            f"Scaler dimension mismatch for {bundle['scope']}: "
            f"expected {expected_dim}, scaler expects {scaler_dim}"
        )

    X_scaled = bundle["scaler"].transform(X)
    score = float(bundle["model"].predict(X_scaled)[0])
    score = float(np.round(score, 4))
    return score, None


def _build_details(
    *,
    degraded: bool,
    reason: str | None,
    bundle_scope: str,
    percentile_available: bool,
) -> dict[str, object]:
    return {
        "degraded": degraded,
        "reason": reason,
        "bundle_scope": bundle_scope,
        "percentile_available": percentile_available,
    }


def _mock_result(reason: str) -> tuple[float, None, dict[str, object]]:
    return (
        MOCK_SCORE,
        None,
        _build_details(
            degraded=True,
            reason=reason,
            bundle_scope="mock",
            percentile_available=False,
        ),
    )


def predict_ctr(
    features: dict,
    dataset_key: str = config.DEFAULT_DATASET,
    return_details: bool = False,
) -> tuple[float, int | None] | tuple[float, int | None, dict[str, object]]:
    """根据提取后的特征预测 CTR。"""

    global_bundle = _load_global_bundle()
    if global_bundle is not None:
        try:
            score, percentile = _predict_with_bundle(features, global_bundle)
            details = _build_details(
                degraded=False,
                reason=None,
                bundle_scope=str(global_bundle["scope"]),
                percentile_available=percentile is not None,
            )
            return (score, percentile, details) if return_details else (score, percentile)
        except Exception as exc:  # noqa: BLE001
            logging.warning("CTR predictor: global bundle inference failed: %s", exc)

    legacy_bundle = _load_legacy_bundle(dataset_key)
    if legacy_bundle is not None:
        try:
            score, percentile = _predict_with_bundle(features, legacy_bundle)
            details = _build_details(
                degraded=True,
                reason="ctr_fallback_legacy_model",
                bundle_scope=str(legacy_bundle["scope"]),
                percentile_available=percentile is not None,
            )
            return (score, percentile, details) if return_details else (score, percentile)
        except Exception as exc:  # noqa: BLE001
            logging.warning("CTR predictor: legacy bundle inference failed: %s", exc)

    score, percentile, details = _mock_result("ctr_fallback_mock_value")
    return (score, percentile, details) if return_details else (score, percentile)
