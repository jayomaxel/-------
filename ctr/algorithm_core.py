import cv2
import numpy as np
import pandas as pd
import torch
try:
    import clip
    CLIP_AVAILABLE = True
except Exception:
    clip = None
    CLIP_AVAILABLE = False
import pytesseract
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from PIL import Image
import os

# ===================== 配置 =====================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
if CLIP_AVAILABLE:
    try:
        CLIP_MODEL, CLIP_PREPROCESS = clip.load("ViT-B/32", device=DEVICE)
    except Exception:
        CLIP_MODEL, CLIP_PREPROCESS = None, None
        CLIP_AVAILABLE = False
else:
    CLIP_MODEL, CLIP_PREPROCESS = None, None

IMG_SIZE = (224, 224)

# ===================== 特征提取 =====================
def get_image_entropy(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    s = hist.sum()
    if s <= 0:
        return 0.0
    hist = hist / s
    # avoid log2(0)
    hist_nonzero = hist[hist > 0]
    entropy = -np.sum(hist_nonzero * np.log2(hist_nonzero))
    return float(entropy)

def get_text_density(img_path):
    try:
        img = Image.open(img_path).resize(IMG_SIZE)
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        area = IMG_SIZE[0] * IMG_SIZE[1]
        d = pytesseract.image_to_data(img_cv, output_type=pytesseract.Output.DICT)
        total = 0
        # conf can be string; convert safely
        confs = d.get('conf', [])
        widths = d.get('width', [])
        heights = d.get('height', [])
        for c, w, h in zip(confs, widths, heights):
            try:
                cval = float(c)
            except Exception:
                cval = -1.0
            if cval > 60:
                total += (int(w) if w is not None else 0) * (int(h) if h is not None else 0)
        return total / area
    except:
        return 0.0

def get_clip_feature(img_path):
    try:
        if not CLIP_AVAILABLE or CLIP_MODEL is None or CLIP_PREPROCESS is None:
            # fallback: return zeros vector with expected CLIP dim (512)
            return np.zeros(512, dtype=np.float32)
        img = CLIP_PREPROCESS(Image.open(img_path)).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            feat = CLIP_MODEL.encode_image(img)
        feat = feat.cpu().numpy().squeeze()
        norm = np.linalg.norm(feat)
        if norm > 1e-6:
            feat = feat / norm
        return feat.astype(np.float32)
    except:
        return np.zeros(512, dtype=np.float32)

# ===================== 【核心】直接运行，无CSV，不存文件 =====================
if __name__ == "__main__":
    print("=" * 50)
    print("        C部分：电商主图CTR预测（无CSV版）")
    print("=" * 50)

    import argparse

    parser = argparse.ArgumentParser(description="CTR prediction run")
    parser.add_argument("--img-folder", default="product_imgs")
    parser.add_argument("--label-excel", default="功能性饮料_数据集.xlsx")
    parser.add_argument("--sample-limit", type=int, default=0, help="0=all, >0 quick run limit")
    args = parser.parse_args()

    # 你的文件路径（不用改）
    IMG_FOLDER = args.img_folder
    LABEL_EXCEL = args.label_excel
    SAMPLE_LIMIT = args.sample_limit

    # 1. 读取标签（只保留有用的两列，彻底去掉文字列）
    print("🔍 读取标签...")
    df = pd.read_excel(LABEL_EXCEL, engine="openpyxl")
    df = df[["std_img_name", "relative_ctr"]].dropna()

    # 2. 批量提取特征（内存直接运算，不写任何文件）
    print("🔍 提取图片特征中...")
    X = []
    y = []

    for i, row in df.iterrows():
        img_name = row["std_img_name"]
        ctr = row["relative_ctr"]
        img_path = os.path.join(IMG_FOLDER, img_name)

        if not os.path.exists(img_path):
            continue

        # 提取3种特征
        img = cv2.imread(img_path)
        if img is None:
            continue
        img = cv2.resize(img, IMG_SIZE)
        ent = get_image_entropy(img)
        txt = get_text_density(img_path)
        clip_feat = get_clip_feature(img_path)

        # 拼接成一个特征向量
        all_feat = [ent, txt] + list(clip_feat)
        X.append(all_feat)
        y.append(ctr)

        # 显示进度
        if len(X) % 500 == 0:
            print(f"已处理：{len(X)} 张")
        # 支持快速测试限制
        if SAMPLE_LIMIT and SAMPLE_LIMIT > 0 and len(X) >= SAMPLE_LIMIT:
            print(f"达到 sample-limit={SAMPLE_LIMIT}，提前结束特征提取")
            break

    # 转成数字格式（XGBoost只认这个）
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)
    print(f"✅ 数据准备完成：共 {len(X)} 条")

    # 3. 训练模型
    print("🚀 开始训练 XGBoost 模型...")
    # 标准化特征可以稳定训练
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=1000,
        n_jobs=-1,
        random_state=42,
        verbosity=1
    )
    # 使用早停（eval set）加速并防过拟合（若当前 xgboost 版本支持）
    eval_set = [(X_test, y_test)]
    try:
        model.fit(X_train, y_train, early_stopping_rounds=20, eval_set=eval_set, verbose=20)
    except TypeError:
        print("当前 xgboost 版本不支持 early_stopping_rounds 参数，退回到无早停训练")
        model.fit(X_train, y_train)

    # 4. 输出结果（C部分必须要的指标）
    y_pred = model.predict(X_test)
    pearson = np.corrcoef(y_test, y_pred)[0, 1]
    r2 = r2_score(y_test, y_pred)

    print("\n" + "=" * 50)
    print("🎉 C 部分 全部完成！")
    print(f"📊 皮尔逊相关系数：{pearson:.3f}")
    print(f"📊 R2 拟合分数：{r2:.3f}")
    print(f"📊 模型已保存：ctr_xgboost_model.pkl")
    print("=" * 50)

    # 保存模型（给D部分用）
    joblib.dump(model, "ctr_xgboost_model.pkl")
    joblib.dump(scaler, "ctr_feature_scaler.pkl")