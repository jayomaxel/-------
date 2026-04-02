from __future__ import annotations

from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).resolve().parent

# Dataset paths (relative to ROOT_DIR)
DRINK_DATA_DIR = "data/drink"
DRINK_EXCEL_PATH = "data/drink/功能性饮料_数据集.xlsx"
DRINK_IMAGES_DIR = "data/drink/images_standard"
DRINK_IMG_PREFIX = "drink_"
DRINK_SAMPLE_SIZE = 2115

LAMP_DATA_DIR = "data/lamp"
LAMP_EXCEL_PATH = "data/lamp/桌面台灯_数据集.xlsx"
LAMP_IMAGES_DIR = "data/lamp/images_standard"
LAMP_IMG_PREFIX = "lamp_"
LAMP_SAMPLE_SIZE = 2681

# Dataset registry
DATASETS = {
    "功能性饮料": {
        "data_dir": DRINK_DATA_DIR,
        "excel_path": DRINK_EXCEL_PATH,
        "images_dir": DRINK_IMAGES_DIR,
        "img_prefix": DRINK_IMG_PREFIX,
        "sample_size": DRINK_SAMPLE_SIZE,
        "cache_vectors": "cache/drink_clip_vectors.npy",
        "model_path": "models/drink_xgboost_ctr.pkl",
        "scaler_path": "models/drink_ctr_scaler.pkl",
    },
    "桌面台灯": {
        "data_dir": LAMP_DATA_DIR,
        "excel_path": LAMP_EXCEL_PATH,
        "images_dir": LAMP_IMAGES_DIR,
        "img_prefix": LAMP_IMG_PREFIX,
        "sample_size": LAMP_SAMPLE_SIZE,
        "cache_vectors": "cache/lamp_clip_vectors.npy",
        "model_path": "models/lamp_xgboost_ctr.pkl",
        "scaler_path": "models/lamp_ctr_scaler.pkl",
    },
}

# Default dataset key used by internal module defaults.
DEFAULT_DATASET = "功能性饮料"

# Legacy aliases (kept for backward compatibility with older scripts).
DATA_DIR = DATASETS[DEFAULT_DATASET]["data_dir"]
EXCEL_PATH = DATASETS[DEFAULT_DATASET]["excel_path"]
IMAGES_DIR = DATASETS[DEFAULT_DATASET]["images_dir"]

# Cache/model paths (legacy single-dataset style)
CACHE_DIR = "cache"
CLIP_VECTORS_PATH = DATASETS[DEFAULT_DATASET]["cache_vectors"]
MODEL_PATH = DATASETS[DEFAULT_DATASET]["model_path"]

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

# Feature vector layout for CTR model input
FEATURE_SCALAR_COLS = ["entropy", "text_density"]
FEATURE_DIM = len(FEATURE_SCALAR_COLS) + CLIP_DIM

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

