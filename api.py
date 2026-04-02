from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

import config
from modules.advisor import generate_advice
from modules.ctr_predictor import predict_ctr
from modules.feature_extractor import extract_features
from modules.heatmap import generate_heatmap
from modules.preprocessor import preprocess_image
from modules.retriever import retrieve_similar

app = FastAPI(title='电商主图智能认知诊断 API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _rgb_array_to_base64(image_rgb: np.ndarray) -> str:
    rgb_image = np.asarray(image_rgb)
    if rgb_image.ndim == 2:
        rgb_image = cv2.cvtColor(rgb_image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
    elif rgb_image.ndim == 3 and rgb_image.shape[2] == 4:
        rgb_image = cv2.cvtColor(rgb_image.astype(np.uint8), cv2.COLOR_RGBA2RGB)
    else:
        rgb_image = rgb_image.astype(np.uint8)

    _, buf = cv2.imencode('.png', cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buf).decode('utf-8')


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


@app.get('/health')
def health() -> dict[str, Any]:
    return {'status': 'ok', 'datasets': list(config.DATASETS.keys())}


@app.post('/analyze')
async def analyze(
    file: UploadFile = File(...),
    dataset_key: str = Form('功能性饮料'),
) -> Any:
    try:
        file_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(file_bytes)).convert('RGB')
        image_array = np.array(pil_image)

        processed_image = preprocess_image(image_array)
        features = extract_features(processed_image)
        ctr_score, ctr_percentile = predict_ctr(features, dataset_key)
        heatmap_array = generate_heatmap(processed_image, dataset_key=dataset_key)
        similar_items = retrieve_similar(
            features['clip_vector'],
            dataset_key=dataset_key,
            top_k=config.TOP_K_SIMILAR,
        )
        advice = generate_advice(features, float(ctr_score), int(ctr_percentile))

        response = {
            'features': {
                'entropy': _to_float(features.get('entropy', 0.0)),
                'text_density': _to_float(features.get('text_density', 0.0)),
                'brightness': _to_float(features.get('brightness', 0.0)),
                'contrast': _to_float(features.get('contrast', 0.0)),
                'saturation': _to_float(features.get('saturation', 0.0)),
            },
            'ctr': {
                'score': _to_float(ctr_score),
                'percentile': int(ctr_percentile),
            },
            'heatmap_base64': _rgb_array_to_base64(heatmap_array),
            'similar': [
                {
                    'rank': int(item.get('rank', index + 1)),
                    'img_name': str(item.get('img_name', '')),
                    'similarity': _to_float(item.get('similarity', 0.0)),
                    'relative_ctr': _to_float(item.get('relative_ctr', 0.0)),
                    'price': _to_float(item.get('price', 0.0)),
                    'img_base64': _similar_image_to_base64(item.get('img_path')),
                }
                for index, item in enumerate(similar_items[: config.TOP_K_SIMILAR])
            ],
            'advice': [
                {
                    'priority': str(item.get('priority', '')),
                    'category': str(item.get('category', '')),
                    'issue': str(item.get('issue', '')),
                    'suggestion': str(item.get('suggestion', '')),
                }
                for item in advice
            ],
        }
        return response
    except Exception as exc:
        return JSONResponse(status_code=500, content={'error': str(exc)})


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
