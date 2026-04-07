# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent

# 缓存和模型路径
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
        # 当前随仓库提供的热力图和 CTR 文件都使用混合类目模型。
        "model_path": GLOBAL_MODEL_PATH,
        "scaler_path": GLOBAL_SCALER_PATH,
    }


# 数据集配置，用于检索和向量缓存。
# 前端不切换数据集，推理统一走全局混合类目模型。
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

# 模块默认数据集
DEFAULT_DATASET = "功能性饮料"
RETRIEVAL_DATASET_KEY = "all"
MODEL_PATH = GLOBAL_MODEL_PATH
SCALER_PATH = GLOBAL_SCALER_PATH

# 图像预处理
IMG_SIZE = (224, 224)
IMG_MEAN = (0.48145466, 0.4578275, 0.40821073)
IMG_STD = (0.26862954, 0.26130258, 0.27577711)

# CLIP 模型
CLIP_MODEL_NAME = "ViT-B/32"
CLIP_DIM = 512

# 相似图检索
TOP_K_SIMILAR = 5
SIMILARITY_EXCLUDE_EQ = True

# 建议生成阈值
ENTROPY_HIGH = 7.0
ENTROPY_LOW = 3.5
TEXT_DENSITY_HIGH = 0.30
SUBJECT_AREA_RATIO_LOW = 0.10

# Excel 列名
COL_IMG_URL = "商品主图"
COL_TITLE = "商品名称"
COL_PRICE_RAW = "价格_清洗"
COL_PRICE_NORM = "价格_标准化"
COL_SALES = "销量_数值"
COL_SALES_NORM = "销量_标准化"
COL_CLICK_VOL = "click_volume"
COL_CTR = "relative_ctr"
COL_IMG_NAME = "std_img_name"

# CTR 模型特征布局
GLOBAL_FEATURE_SCALAR_COLS = [
    "entropy",
    "text_density",
    "subject_area_ratio",
    "edge_density",
    "color_saturation",
]
GLOBAL_FEATURE_DIM = len(GLOBAL_FEATURE_SCALAR_COLS) + CLIP_DIM

# 训练相关常量，保留给旧流程使用
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

# AI 分析配置
AI_MODEL_BASE_URL = os.getenv("AI_MODEL_BASE_URL", "https://api.deepseek.com")
AI_MODEL_API_KEY = os.getenv("AI_MODEL_API_KEY", "YOUR_API_KEY")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "deepseek-chat")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "1500"))
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "30"))
