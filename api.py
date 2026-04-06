from __future__ import annotations

import base64
import io
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, Field

import config
from modules.advisor import generate_advice
from modules.ai_analyzer import analyze_with_ai
from modules.heatmap import generate_heatmap
from modules.reference_pipeline import (
    extract_reference_features,
    predict_reference_ctr,
    generate_psychological_report,
)
from modules.retriever import load_retrieval_corpus, retrieve_similar

app = FastAPI(title="E-commerce Main Image Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AIAnalysisRequest(BaseModel):
    tone: str = Field(default="professional", description="语气风格")
    features: dict[str, Any] = Field(..., description="调用方传入的视觉特征对象")
    ctr_score: float = Field(..., description="CTR 预测分")
    api_key: str | None = Field(default=None, description="前端传入的 AI API Key")


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
    components: dict[str, bool] = {
        "ctr_model": _resolve_path(config.MODEL_PATH).exists(),
        "ctr_scaler": _resolve_path(config.SCALER_PATH).exists(),
        "vector_cache": all(
            _resolve_path(str(dataset_cfg["cache_vectors"])).exists()
            for dataset_cfg in config.DATASETS.values()
        ),
        "dataset_excel": all(
            _resolve_path(str(dataset_cfg["excel_path"])).exists()
            for dataset_cfg in config.DATASETS.values()
        ),
        "dataset_images": all(
            _resolve_path(str(dataset_cfg["images_dir"])).exists()
            for dataset_cfg in config.DATASETS.values()
        ),
    }

    retrieval_ready = False
    if components["vector_cache"] and components["dataset_excel"] and components["dataset_images"]:
        try:
            load_retrieval_corpus(config.RETRIEVAL_DATASET_KEY)
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
    temp_image_path: Path | None = None

    try:
        try:
            file_bytes = await file.read()
            suffix = Path(file.filename or "upload.png").suffix or ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(file_bytes)
                temp_image_path = Path(temp_file.name)

            pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            image_array = np.array(pil_image)
            features = extract_reference_features(temp_image_path)
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=400,
                content={"error": f"Image processing failed: {exc}"},
            )

        try:
            ctr_score = predict_reference_ctr(features)
            ctr_percentile = None
        except Exception:  # noqa: BLE001
            ctr_score, ctr_percentile = 0.5, None
            warnings.append("ctr_fallback_mock_value")

        try:
            heatmap_array = generate_heatmap(image_array)
        except Exception:  # noqa: BLE001
            heatmap_array = image_array
            warnings.append("heatmap_fallback_original_image")

        similar_items: list[dict] = []
        try:
            similar_items = retrieve_similar(
                features["clip_vector"],
                dataset_key=config.RETRIEVAL_DATASET_KEY,
                top_k=config.TOP_K_SIMILAR,
            )
        except Exception:  # noqa: BLE001
            warnings.append("retrieval_disabled")

        advice: list[dict] = []
        try:
            advice = generate_advice(features, float(ctr_score), ctr_percentile)
        except Exception:  # noqa: BLE001
            warnings.append("advice_generation_failed")

        psychological_report = {"lines": [], "text": ""}
        try:
            psychological_report = generate_psychological_report(features, float(ctr_score))
        except Exception:  # noqa: BLE001
            warnings.append("psychological_report_failed")

        response = {
            "features": {
                "entropy": _to_float(features.get("entropy", 0.0)),
                "text_density": _to_float(features.get("text_density", 0.0)),
                "subject_area_ratio": _to_float(features.get("subject_area_ratio", 0.0)),
                "edge_density": _to_float(features.get("edge_density", 0.0)),
                "color_saturation": _to_float(features.get("color_saturation", 0.0)),
            },
            "ctr": {
                "score": _to_float(ctr_score),
                "percentile": int(ctr_percentile) if ctr_percentile is not None else None,
                "percentile_available": ctr_percentile is not None,
            },
            "heatmap_base64": _rgb_array_to_base64(heatmap_array),
            "similar": [
                {
                    "rank": int(item.get("rank", index + 1)),
                    "dataset_key": str(item.get("dataset_key", "")),
                    "dataset_name": str(item.get("dataset_name", "")),
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
            "psychological_report": {
                "lines": [str(line) for line in psychological_report.get("lines", [])],
                "text": str(psychological_report.get("text", "")),
            },
            "warnings": warnings,
        }
        return response
    finally:
        if temp_image_path is not None:
            try:
                temp_image_path.unlink(missing_ok=True)
            except Exception:
                pass


@app.post("/ai-analysis")
async def ai_analysis(payload: AIAnalysisRequest) -> Any:
    valid_tones = ["professional", "gentle", "direct", "marketing"]
    tone = payload.tone if payload.tone in valid_tones else "professional"

    try:
        result = analyze_with_ai(
            features=payload.features,
            ctr_score=payload.ctr_score,
            tone=tone,
            api_key=payload.api_key,
        )
        return result
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
