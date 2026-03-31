from pathlib import Path
import os
import tempfile

import cv2
import joblib
import numpy as np
import pytesseract
from PIL import Image

from algorithm_core import get_clip_feature, get_image_entropy, get_text_density, IMG_SIZE


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = (BASE_DIR / "ctr_xgboost_model.pkl").resolve()
DEFAULT_SCALER_PATH = (BASE_DIR / "ctr_feature_scaler.pkl").resolve()
DEFAULT_SAMPLE_IMAGE_PATH = (BASE_DIR / "product_imgs" / "drink_0001.jpg").resolve()
DEFAULT_TEST_HEATMAP_PATH = (BASE_DIR / "test_heatmap.jpg").resolve()


def _resolve_to_abs_path(path_value: str | os.PathLike[str]) -> str:
    path_obj = Path(path_value)
    if not path_obj.is_absolute():
        path_obj = BASE_DIR / path_obj
    return str(path_obj.resolve())


def generate_ctr_heatmap(
    img_path,
    model_path=str(DEFAULT_MODEL_PATH),
    save_heatmap_path="heatmap.jpg",
):
    """
    Generate CTR attention heatmap for an image.

    Args:
        img_path: input image path (absolute or relative to this file).
        model_path: xgboost model path.
        save_heatmap_path: output heatmap image path.

    Returns:
        np.ndarray | None: BGR overlay image or None when failed.
    """
    img_path = _resolve_to_abs_path(img_path)
    model_path = _resolve_to_abs_path(model_path)
    save_heatmap_path = _resolve_to_abs_path(save_heatmap_path)
    Path(save_heatmap_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        model = joblib.load(model_path)
    except Exception as exc:
        print(f"无法加载模型 {model_path}: {exc}")
        return None

    if not os.path.exists(img_path):
        print(f"图像文件不存在: {img_path}")
        return None

    img = Image.open(img_path).convert("RGB").resize(IMG_SIZE)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Keep these feature calls for consistency with the original pipeline behavior.
    _ = get_image_entropy(img_cv)
    _ = get_text_density(img_path)

    height, width = img_gray.shape

    def compute_occlusion_heatmap(img_bgr, xgb_model, scaler=None, patch_size=32, stride=16):
        h, w = img_bgr.shape[:2]
        heat = np.zeros((h, w), dtype=np.float32)

        tmp_path = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp_path = tmp.name
            tmp.close()

            cv2.imwrite(tmp_path, img_bgr)
            base_ent = get_image_entropy(img_bgr)
            base_txt = get_text_density(tmp_path)
            base_clip = get_clip_feature(tmp_path)
            base_feat = np.concatenate(([base_ent, base_txt], base_clip)).astype(np.float32).reshape(1, -1)
            base_feat_s = scaler.transform(base_feat) if scaler is not None else base_feat
            base_pred = float(xgb_model.predict(base_feat_s)[0])

            for y in range(0, h, stride):
                for x in range(0, w, stride):
                    y2 = min(y + patch_size, h)
                    x2 = min(x + patch_size, w)
                    occluded = img_bgr.copy()
                    patch = occluded[y:y2, x:x2]
                    if patch.size == 0:
                        continue

                    mean_color = patch.mean(axis=(0, 1)).astype(np.uint8)
                    occluded[y:y2, x:x2] = mean_color
                    cv2.imwrite(tmp_path, occluded)

                    ent_o = get_image_entropy(occluded)
                    txt_o = get_text_density(tmp_path)
                    clip_o = get_clip_feature(tmp_path)
                    feat_o = np.concatenate(([ent_o, txt_o], clip_o)).astype(np.float32).reshape(1, -1)
                    feat_o_s = scaler.transform(feat_o) if scaler is not None else feat_o
                    pred_o = float(xgb_model.predict(feat_o_s)[0])

                    importance = max(0.0, base_pred - pred_o)
                    heat[y:y2, x:x2] += importance
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        kernel = max(1, (patch_size // 8) * 2 + 1)
        heat = cv2.GaussianBlur(heat, (kernel, kernel), 0)
        if heat.max() > 0:
            heat = heat / heat.max()
        return heat

    try:
        scaler = joblib.load(str(DEFAULT_SCALER_PATH))
    except Exception:
        scaler = None

    try:
        patch_size = max(16, min(height, width) // 14)
        stride = max(8, min(height, width) // 28)
        occ_heat = compute_occlusion_heatmap(
            img_cv,
            model,
            scaler=scaler,
            patch_size=patch_size,
            stride=stride,
        )
    except Exception:
        occ_heat = np.zeros((height, width), dtype=np.float32)

    text_map = np.zeros((height, width), dtype=np.float32)
    try:
        ocr_dict = pytesseract.image_to_data(img_cv, output_type=pytesseract.Output.DICT)
    except Exception:
        ocr_dict = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}

    texts = ocr_dict.get("text", [])
    confs = ocr_dict.get("conf", [])
    lefts = ocr_dict.get("left", [])
    tops = ocr_dict.get("top", [])
    widths = ocr_dict.get("width", [])
    heights = ocr_dict.get("height", [])

    for i in range(len(texts)):
        try:
            conf = float(confs[i])
        except Exception:
            conf = -1.0

        if conf <= 60:
            continue

        x = int(lefts[i]) if i < len(lefts) else 0
        y = int(tops[i]) if i < len(tops) else 0
        w = int(widths[i]) if i < len(widths) else 0
        h = int(heights[i]) if i < len(heights) else 0

        x2 = min(x + w, width)
        y2 = min(y + h, height)
        x = max(0, x)
        y = max(0, y)

        if x < x2 and y < y2:
            text_map[y:y2, x:x2] += 1.0

    text_norm = text_map
    if text_norm.max() > 0:
        text_norm = text_norm / text_norm.max()

    combined = 0.8 * occ_heat + 0.2 * text_norm
    heatmap = (combined * 255.0).astype(np.float32)

    heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
    heatmap = heatmap.astype(np.uint8)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    result = cv2.addWeighted(img_cv, 0.7, heatmap, 0.3, 0)

    cv2.imwrite(save_heatmap_path, result)
    print(f"热力图已保存: {save_heatmap_path}")
    return result


if __name__ == "__main__":
    generate_ctr_heatmap(
        img_path=str(DEFAULT_SAMPLE_IMAGE_PATH),
        model_path=str(DEFAULT_MODEL_PATH),
        save_heatmap_path=str(DEFAULT_TEST_HEATMAP_PATH),
    )
