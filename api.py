from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

import config
from modules.advisor import generate_advice
from modules.ctr_predictor import load_model_bundle, predict_ctr
from modules.feature_extractor import extract_features
from modules.heatmap import generate_heatmap
from modules.preprocessor import preprocess_image
from modules.retriever import load_dataset_vectors, retrieve_similar

app = FastAPI(title="E-commerce Main Image Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve_path(path_value: str) -> Path:
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (config.ROOT_DIR / path_obj).resolve()


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _to_uint8_rgb(image_rgb: np.ndarray) -> np.ndarray:
    rgb_image = np.asarray(image_rgb)

    if np.issubdtype(rgb_image.dtype, np.floating):
        rgb_image = np.clip(rgb_image, 0.0, 1.0) * 255.0
    else:
        rgb_image = np.clip(rgb_image, 0, 255)

    if rgb_image.ndim == 2:
        rgb_image = cv2.cvtColor(rgb_image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
    elif rgb_image.ndim == 3 and rgb_image.shape[2] == 4:
        rgb_image = cv2.cvtColor(rgb_image.astype(np.uint8), cv2.COLOR_RGBA2RGB)
    else:
        rgb_image = rgb_image.astype(np.uint8)

    return rgb_image


def _rgb_array_to_base64(image_rgb: np.ndarray) -> str:
    rgb_image = _to_uint8_rgb(image_rgb)
    _, buf = cv2.imencode(".png", cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buf).decode("utf-8")


def _read_image_unicode_safe(image_path: Path) -> np.ndarray | None:
    if not image_path.exists():
        return None

    image_bytes = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_UNCHANGED)
    if image is None:
        return None

    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    if image.ndim == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return None


def _similar_image_to_base64(img_path: str | None) -> str | None:
    if not img_path:
        return None

    image = _read_image_unicode_safe(Path(img_path))
    if image is None:
        return None

    return _rgb_array_to_base64(image)


def _build_readiness_components() -> dict[str, bool]:
    dataset_cfg = config.DATASETS[config.DEFAULT_DATASET]

    ctr_bundle = load_model_bundle(config.DEFAULT_DATASET)
    global_bundle_ready = ctr_bundle is not None and str(ctr_bundle.get("scope", "")).startswith("global")

    components: dict[str, bool] = {
        "ctr_model": global_bundle_ready,
        "ctr_scaler": global_bundle_ready,
        "vector_cache": _resolve_path(dataset_cfg["cache_vectors"]).exists(),
        "dataset_excel": _resolve_path(dataset_cfg["excel_path"]).exists(),
        "dataset_images": _resolve_path(dataset_cfg["images_dir"]).exists(),
    }

    retrieval_ready = False
    if components["vector_cache"] and components["dataset_excel"] and components["dataset_images"]:
        try:
            load_dataset_vectors(config.DEFAULT_DATASET)
            retrieval_ready = True
        except Exception:
            retrieval_ready = False

    components["retrieval"] = retrieval_ready
    return components


@app.get("/health")
def health() -> dict[str, Any]:
    components = _build_readiness_components()
    ready = all(components.values())
    return {
        "status": "ok",
        "ready": ready,
        "mode": "full" if ready else "degraded",
        "model_scope": "global",
        "components": components,
    }


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> Any:
    warnings: list[str] = []

    try:
        file_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        image_array = np.array(pil_image)
        processed_image = preprocess_image(image_array)
        features = extract_features(processed_image)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=400, content={"error": f"Image processing failed: {exc}"})

    try:
        ctr_score, ctr_percentile, ctr_details = predict_ctr(features, return_details=True)
        if bool(ctr_details.get("degraded")):
            reason = ctr_details.get("reason")
            if isinstance(reason, str) and reason:
                warnings.append(reason)
    except Exception:  # noqa: BLE001
        ctr_score, ctr_percentile = 0.5, 50
        warnings.append("ctr_fallback_mock_value")

    try:
        heatmap_array = generate_heatmap(processed_image)
    except Exception:  # noqa: BLE001
        heatmap_array = processed_image
        warnings.append("heatmap_fallback_original_image")

    similar_items: list[dict] = []
    try:
        similar_items = retrieve_similar(features["clip_vector"], top_k=config.TOP_K_SIMILAR)
    except Exception:  # noqa: BLE001
        warnings.append("retrieval_disabled")

    advice: list[dict] = []
    try:
        advice = generate_advice(features, float(ctr_score), int(ctr_percentile))
    except Exception:  # noqa: BLE001
        warnings.append("advice_generation_failed")

    response = {
        "features": {
            "entropy": _to_float(features.get("entropy", 0.0)),
            "text_density": _to_float(features.get("text_density", 0.0)),
            "brightness": _to_float(features.get("brightness", 0.0)),
            "contrast": _to_float(features.get("contrast", 0.0)),
            "saturation": _to_float(features.get("saturation", 0.0)),
        },
        "ctr": {
            "score": _to_float(ctr_score),
            "percentile": int(ctr_percentile),
        },
        "heatmap_base64": _rgb_array_to_base64(heatmap_array),
        "similar": [
            {
                "rank": int(item.get("rank", index + 1)),
                "img_name": str(item.get("img_name", "")),
                "similarity": _to_float(item.get("similarity", 0.0)),
                "relative_ctr": _to_float(item.get("relative_ctr", 0.0)),
                "price": _to_float(item.get("price", 0.0)),
                "img_base64": _similar_image_to_base64(item.get("img_path")),
            }
            for index, item in enumerate(similar_items[: config.TOP_K_SIMILAR])
        ],
        "advice": [
            {
                "priority": str(item.get("priority", "")),
                "category": str(item.get("category", "")),
                "issue": str(item.get("issue", "")),
                "suggestion": str(item.get("suggestion", "")),
            }
            for item in advice
        ],
        "warnings": warnings,
    }
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
