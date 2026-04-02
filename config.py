from pathlib import Path

# 鈥斺€?鏍圭洰褰?鈥斺€?ROOT_DIR = Path(__file__).parent

# 鈥斺€?妗岄潰鍙扮伅鏁版嵁闆?鈥斺€?LAMP_DATA_DIR     = "data/lamp/"
LAMP_EXCEL_PATH   = "data/lamp/妗岄潰鍙扮伅_鏁版嵁闆?xlsx"
LAMP_IMAGES_DIR   = "data/lamp/images_standard/"
LAMP_IMG_PREFIX   = "lamp_"
LAMP_SAMPLE_SIZE  = 2681

# 鈥斺€?鍔熻兘鎬чギ鏂欐暟鎹泦 鈥斺€?DRINK_DATA_DIR    = "data/drink/"
DRINK_EXCEL_PATH  = "data/drink/鍔熻兘鎬чギ鏂檁鏁版嵁闆?xlsx"
DRINK_IMAGES_DIR  = "data/drink/images_standard/"
DRINK_IMG_PREFIX  = "drink_"
DRINK_SAMPLE_SIZE = 2115

# 鈥斺€?鍏煎鏃ф帴鍙ｏ紙榛樿鎸囧悜鍙扮伅锛夆€斺€?DATA_DIR   = LAMP_DATA_DIR
EXCEL_PATH = LAMP_EXCEL_PATH
IMAGES_DIR = LAMP_IMAGES_DIR

# 鈥斺€?鏁版嵁闆嗘敞鍐岃〃 鈥斺€?DATASETS = {
    "妗岄潰鍙扮伅": {
        "data_dir":      LAMP_DATA_DIR,
        "excel_path":    LAMP_EXCEL_PATH,
        "images_dir":    LAMP_IMAGES_DIR,
        "img_prefix":    LAMP_IMG_PREFIX,
        "sample_size":   LAMP_SAMPLE_SIZE,
        "cache_vectors": "cache/lamp_clip_vectors.npy",
        "model_path":    "models/lamp_xgboost_ctr.pkl",
        "scaler_path":   "models/lamp_ctr_scaler.pkl",
    },
    "鍔熻兘鎬чギ鏂?: {
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
DEFAULT_DATASET = "妗岄潰鍙扮伅"

# 鈥斺€?缂撳瓨涓庢ā鍨嬭矾寰勶紙榛樿鍙扮伅锛夆€斺€?CACHE_DIR         = "cache/"
CLIP_VECTORS_PATH = "cache/lamp_clip_vectors.npy"
MODEL_PATH        = "models/lamp_xgboost_ctr.pkl"

# 鈥斺€?鍥惧儚澶勭悊鍙傛暟 鈥斺€?IMG_SIZE = (224, 224)
IMG_MEAN = (0.48145466, 0.4578275, 0.40821073)
IMG_STD  = (0.26862954, 0.26130258, 0.27577711)

# 鈥斺€?CLIP 妯″瀷 鈥斺€?CLIP_MODEL_NAME = "ViT-B/32"
CLIP_DEVICE     = "cpu"  # 鏃?GPU 鏃剁敤 cpu锛涙湁 GPU 鍙敼涓?"cuda"

# 鈥斺€?鐩镐技鍥炬绱?鈥斺€?TOP_K_SIMILAR         = 5
SIMILARITY_EXCLUDE_EQ = True

# 鈥斺€?鐗瑰緛鎻愬彇闃堝€硷紙advisor 瑙勫垯寮曟搸浣跨敤锛夆€斺€?ENTROPY_HIGH      = 7.0
ENTROPY_LOW       = 3.5
CONTRAST_LOW      = 20.0
CONTRAST_HIGH     = 80.0
TEXT_DENSITY_HIGH = 0.30
BRIGHTNESS_LOW    = 0.30
BRIGHTNESS_HIGH   = 0.90
CTR_PCT_LOW       = 30
CTR_PCT_MID       = 60

# 鈥斺€?鏁版嵁闆嗗瓧娈靛悕锛圗xcel 鍒楀悕甯搁噺锛夆€斺€?COL_IMG_URL    = "鍟嗗搧涓诲浘"
COL_IMG_NAME   = "std_img_name"
COL_PRICE_RAW  = "浠锋牸_娓呮礂"
COL_PRICE_NORM = "浠锋牸_鏍囧噯鍖?
COL_SALES      = "閿€閲廮瀵规暟"
COL_SALES_NORM = "閿€閲廮鏍囧噯鍖?
COL_CLICK_VOL  = "click_volume"
COL_CTR        = "relative_ctr"
COL_TITLE      = "鍟嗗搧鍚嶇О"

# 鏂板锛氱壒寰佺淮搴﹀父閲忥紙渚?ctr_predictor.py / train.py 寮曠敤锛?FEATURE_SCALAR_COLS = ["entropy", "text_density"]   # 2 涓爣閲忕壒寰侊紝椤哄簭鍥哄畾
CLIP_DIM = 512
FEATURE_DIM = len(FEATURE_SCALAR_COLS) + CLIP_DIM   # = 514

# 鈥斺€?璁粌鍙傛暟 鈥斺€?TRAIN_TEST_SPLIT = 0.2
RANDOM_STATE     = 42
CTR_ZERO_EXCLUDE = True
XGB_PARAMS = {
    "objective":    "reg:squarederror",
    "n_estimators": 1000,
    "n_jobs":       -1,
    "random_state": RANDOM_STATE,
    "verbosity":    1,
}
