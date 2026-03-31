from pathlib import Path

# —— 根目录 ——
ROOT_DIR = Path(__file__).parent

# —— 桌面台灯数据集 ——
LAMP_DATA_DIR     = "data/lamp/"
LAMP_EXCEL_PATH   = "data/lamp/桌面台灯_数据集.xlsx"
LAMP_IMAGES_DIR   = "data/lamp/images_standard/"
LAMP_IMG_PREFIX   = "lamp_"
LAMP_SAMPLE_SIZE  = 2681

# —— 功能性饮料数据集 ——
DRINK_DATA_DIR    = "data/drink/"
DRINK_EXCEL_PATH  = "data/drink/功能性饮料数据集.xlsx"
DRINK_IMAGES_DIR  = "data/drink/images_standard/"
DRINK_IMG_PREFIX  = "drink_"
DRINK_SAMPLE_SIZE = 2115

# —— 兼容旧接口（默认指向台灯）——
DATA_DIR   = LAMP_DATA_DIR
EXCEL_PATH = LAMP_EXCEL_PATH
IMAGES_DIR = LAMP_IMAGES_DIR

# —— 数据集注册表 ——
DATASETS = {
    "桌面台灯": {
        "data_dir":      LAMP_DATA_DIR,
        "excel_path":    LAMP_EXCEL_PATH,
        "images_dir":    LAMP_IMAGES_DIR,
        "img_prefix":    LAMP_IMG_PREFIX,
        "sample_size":   LAMP_SAMPLE_SIZE,
        "cache_vectors": "cache/lamp_clip_vectors.npy",
        "model_path":    "models/lamp_xgboost_ctr.pkl",
        "scaler_path":   "models/lamp_ctr_scaler.pkl",
    },
    "功能性饮料": {
        "data_dir":      DRINK_DATA_DIR,
        "excel_path":    DRINK_EXCEL_PATH,
        "images_dir":    DRINK_IMAGES_DIR,
        "img_prefix":    DRINK_IMG_PREFIX,
        "sample_size":   DRINK_SAMPLE_SIZE,
        "cache_vectors": "cache/drink_clip_vectors.npy",
        "model_path":    "models/drink_xgboost_ctr.pkl",
        "scaler_path":   "models/drink_ctr_scaler.pkl",
    },
}
DEFAULT_DATASET = "桌面台灯"

# —— 缓存与模型路径（默认台灯）——
CACHE_DIR         = "cache/"
CLIP_VECTORS_PATH = "cache/lamp_clip_vectors.npy"
MODEL_PATH        = "models/lamp_xgboost_ctr.pkl"

# —— 图像处理参数 ——
IMG_SIZE = (224, 224)
IMG_MEAN = (0.48145466, 0.4578275, 0.40821073)
IMG_STD  = (0.26862954, 0.26130258, 0.27577711)

# —— CLIP 模型 ——
CLIP_MODEL_NAME = "ViT-B/32"
CLIP_DEVICE     = "cpu"  # 无 GPU 时用 cpu；有 GPU 可改为 "cuda"

# —— 相似图检索 ——
TOP_K_SIMILAR         = 5
SIMILARITY_EXCLUDE_EQ = True

# —— 特征提取阈值（advisor 规则引擎使用）——
ENTROPY_HIGH      = 7.0
ENTROPY_LOW       = 3.5
CONTRAST_LOW      = 20.0
CONTRAST_HIGH     = 80.0
TEXT_DENSITY_HIGH = 0.30
BRIGHTNESS_LOW    = 0.30
BRIGHTNESS_HIGH   = 0.90
CTR_PCT_LOW       = 30
CTR_PCT_MID       = 60

# —— 数据集字段名（Excel 列名常量）——
COL_IMG_URL    = "商品主图"
COL_IMG_NAME   = "std_img_name"
COL_PRICE_RAW  = "价格_清洗"
COL_PRICE_NORM = "价格_标准化"
COL_SALES      = "销量_对数"
COL_SALES_NORM = "销量_标准化"
COL_CLICK_VOL  = "click_volume"
COL_CTR        = "relative_ctr"
COL_TITLE      = "商品名称"

# 新增：特征维度常量（供 ctr_predictor.py / train.py 引用）
FEATURE_SCALAR_COLS = ["entropy", "text_density"]   # 2 个标量特征，顺序固定
CLIP_DIM = 512
FEATURE_DIM = len(FEATURE_SCALAR_COLS) + CLIP_DIM   # = 514

# —— 训练参数 ——
TRAIN_TEST_SPLIT = 0.2
RANDOM_STATE     = 42
CTR_ZERO_EXCLUDE = True
XGB_PARAMS = {
    "objective":    "reg:squarederror",
    "n_estimators": 1000,
    "n_jobs":       -1,
    "random_state": RANDOM_STATE,
    "verbosity":    1,
}