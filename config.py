# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).resolve().parent

# Cache/model paths
CACHE_DIR = "cache"
GLOBAL_MODEL_PATH = "heatmap/ctr_xgboost_model_global.pkl"
GLOBAL_SCALER_PATH = "heatmap/ctr_feature_scaler.pkl"


def _build_dataset_config(
    *,
    slug: str,
    display_name: str,
    excel_name: str,
    img_prefix: str,
    sample_size: int,
) -> dict[str, str | int]:
    base_dir = f"data/{slug}"
    return {
        "slug": slug,
        "display_name": display_name,
        "data_dir": base_dir,
        "excel_path": f"{base_dir}/{excel_name}",
        "images_dir": f"{base_dir}/images_standard",
        "img_prefix": img_prefix,
        "sample_size": sample_size,
        "cache_vectors": f"{CACHE_DIR}/{slug}_clip_vectors.npy",
        # The shipped heatmap / CTR artifacts are trained on a mixed six-category dataset.
        "model_path": GLOBAL_MODEL_PATH,
        "scaler_path": GLOBAL_SCALER_PATH,
    }


# Dataset registry used for retrieval resources / cache generation.
# Frontend does not need dataset switching because inference uses the global mixed-category model.
DATASETS = {
    "功能性饮料": _build_dataset_config(
        slug="drink",
        display_name="功能性饮料",
        excel_name="功能性饮料_数据集.xlsx",
        img_prefix="drink_",
        sample_size=2115,
    ),
    "桌面台灯": _build_dataset_config(
        slug="lamp",
        display_name="桌面台灯",
        excel_name="桌面台灯_数据集.xlsx",
        img_prefix="lamp_",
        sample_size=2681,
    ),
    "ins风手机壳": _build_dataset_config(
        slug="phonecase",
        display_name="ins风手机壳",
        excel_name="ins风手机壳_数据集.xlsx",
        img_prefix="phonecase_",
        sample_size=565,
    ),
    "创意玻璃杯": _build_dataset_config(
        slug="glass",
        display_name="创意玻璃杯",
        excel_name="创意玻璃杯_数据集.xlsx",
        img_prefix="glass_",
        sample_size=570,
    ),
    "印花丝巾": _build_dataset_config(
        slug="scarf",
        display_name="印花丝巾",
        excel_name="印花丝巾_数据集.xlsx",
        img_prefix="scarf_",
        sample_size=651,
    ),
    "口红": _build_dataset_config(
        slug="lipstick",
        display_name="口红",
        excel_name="口红_数据集.xlsx",
        img_prefix="lipstick_",
        sample_size=501,
    ),
}

# Default dataset key used by internal module defaults.
DEFAULT_DATASET = "功能性饮料"
RETRIEVAL_DATASET_KEY = "all"

# Legacy aliases (kept for backward compatibility with older scripts).
DATA_DIR = DATASETS[DEFAULT_DATASET]["data_dir"]
EXCEL_PATH = DATASETS[DEFAULT_DATASET]["excel_path"]
IMAGES_DIR = DATASETS[DEFAULT_DATASET]["images_dir"]

# Cache/model paths (legacy single-dataset style)
CLIP_VECTORS_PATH = DATASETS[DEFAULT_DATASET]["cache_vectors"]
LEGACY_MODEL_PATH = DATASETS[DEFAULT_DATASET]["model_path"]
LEGACY_SCALER_PATH = DATASETS[DEFAULT_DATASET]["scaler_path"]
MODEL_PATH = GLOBAL_MODEL_PATH
SCALER_PATH = GLOBAL_SCALER_PATH

# Image preprocessing
IMG_SIZE = (224, 224)
IMG_MEAN = (0.48145466, 0.4578275, 0.40821073)
IMG_STD = (0.26862954, 0.26130258, 0.27577711)

# CLIP model
CLIP_MODEL_NAME = "ViT-B/32"
CLIP_DEVICE = "cpu"  # Change to "cuda" if you have GPU support
CLIP_DIM = 512

# Similar retrieval
TOP_K_SIMILAR = 5
SIMILARITY_EXCLUDE_EQ = True

# Advisor thresholds
ENTROPY_HIGH = 7.0
ENTROPY_LOW = 3.5
CONTRAST_LOW = 20.0
CONTRAST_HIGH = 80.0
TEXT_DENSITY_HIGH = 0.30
BRIGHTNESS_LOW = 0.30
BRIGHTNESS_HIGH = 0.90
CTR_PCT_LOW = 30
CTR_PCT_MID = 60

# Excel column names
COL_IMG_URL = "商品主图"
COL_TITLE = "商品名称"
COL_PRICE_RAW = "价格_清洗"
COL_PRICE_NORM = "价格_标准化"
COL_SALES = "销量_数值"
COL_SALES_NORM = "销量_标准化"
COL_CLICK_VOL = "click_volume"
COL_CTR = "relative_ctr"
COL_IMG_NAME = "std_img_name"

# Feature vector layouts for CTR model input
LEGACY_FEATURE_SCALAR_COLS = ["entropy", "text_density"]
LEGACY_FEATURE_DIM = len(LEGACY_FEATURE_SCALAR_COLS) + CLIP_DIM

GLOBAL_FEATURE_SCALAR_COLS = [
    "entropy",
    "text_density",
    "subject_area_ratio",
    "edge_density",
    "color_saturation",
]
GLOBAL_FEATURE_DIM = len(GLOBAL_FEATURE_SCALAR_COLS) + CLIP_DIM

FEATURE_SCALAR_COLS = GLOBAL_FEATURE_SCALAR_COLS
FEATURE_DIM = GLOBAL_FEATURE_DIM

# Training-related constants (kept for compatibility)
TRAIN_TEST_SPLIT = 0.2
RANDOM_STATE = 42
CTR_ZERO_EXCLUDE = True
XGB_PARAMS = {
    "objective": "reg:squarederror",
    "n_estimators": 1000,
    "n_jobs": -1,
    "random_state": RANDOM_STATE,
    "verbosity": 1,
}
