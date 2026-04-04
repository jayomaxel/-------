import cv2
import numpy as np
import joblib
from PIL import Image
import pytesseract
import os

# ====== 尝试导入 Torch 和 CLIP ======
try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    torch = None
    TORCH_AVAILABLE = False
try:
    import clip
    CLIP_AVAILABLE = True
except Exception:
    clip = None
    CLIP_AVAILABLE = False

# ====== 配置 ======
DEVICE = "cuda" if (TORCH_AVAILABLE and torch.cuda.is_available()) else "cpu"
IMG_SIZE = (224, 224)

print("正在加载模型环境...")
if CLIP_AVAILABLE and TORCH_AVAILABLE:
    try:
        CLIP_MODEL, CLIP_PREPROCESS = clip.load("ViT-B/32", device=DEVICE)
    except Exception:
        CLIP_MODEL, CLIP_PREPROCESS = None, None
else:
    CLIP_MODEL, CLIP_PREPROCESS = None, None


# ====== 复用训练时的特征提取函数 ======
def get_image_entropy(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    s = hist.sum()
    if s <= 0: return 0.0
    hist = hist / s
    hist_nonzero = hist[hist > 0]
    return float(-np.sum(hist_nonzero * np.log2(hist_nonzero)))

def get_text_density(img_path):
    try:
        img = Image.open(img_path).resize(IMG_SIZE)
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        area = IMG_SIZE[0] * IMG_SIZE[1]
        d = pytesseract.image_to_data(img_cv, output_type=pytesseract.Output.DICT)
        total = 0
        for c, w, h in zip(d.get('conf', []), d.get('width', []), d.get('height', [])):
            try: cval = float(c)
            except: cval = -1.0
            if cval > 60:
                total += (int(w) if w is not None else 0) * (int(h) if h is not None else 0)
        return total / area
    except:
        return 0.0

def get_subject_area_ratio(img):
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours: return 0.0
        max_area = max([cv2.contourArea(c) for c in contours])
        h, w = img.shape[:2]
        return float(max_area / (w * h))
    except: return 0.0

def get_edge_density(img):
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        h, w = img.shape[:2]
        return float(np.count_nonzero(edges)) / (w * h)
    except: return 0.0

def get_color_saturation(img):
    try:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1].astype(np.float32)
        return float(np.mean(sat) / 255.0)
    except: return 0.0

def get_clip_feature(img_path):
    try:
        if not CLIP_AVAILABLE or CLIP_MODEL is None or CLIP_PREPROCESS is None:
            return np.zeros(512, dtype=np.float32)
        img = CLIP_PREPROCESS(Image.open(img_path)).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            feat = CLIP_MODEL.encode_image(img)
        feat = feat.cpu().numpy().squeeze()
        norm = np.linalg.norm(feat)
        if norm > 1e-6: feat = feat / norm
        return feat.astype(np.float32)
    except:
        return np.zeros(512, dtype=np.float32)

# ====== 新增：视觉注意力热力图生成 ======
def generate_attention_heatmap(img_path, output_path="heatmap_result.jpg"):
    """使用图像对比度和边缘特征模拟人眼视觉停留热力图"""
    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None: return
    
    # 转换为Lab色彩空间，利用亮度与色彩差异寻找显著区域
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # 计算距离均值的色彩对比度作为显著性基础
    lm, am, bm = np.mean(l), np.mean(a), np.mean(b)
    saliency = np.sqrt(np.square(l - lm) + np.square(a - am) + np.square(b - bm))
    
    # 加入边缘特征(人眼对边缘敏感)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edges_blurred = cv2.GaussianBlur(edges, (15, 15), 0)
    
    # 融合显著性与边缘，平滑处理
    heatmap_gray = cv2.normalize(saliency + edges_blurred, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heatmap_gray = cv2.GaussianBlur(heatmap_gray, (31, 31), 0) # 大核平滑，模拟焦点
    
    # 转换为伪彩色热力图 (JET: 红/黄为热点，蓝为冷点)
    heatmap_color = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_JET)
    
    # 将热力图与原图叠加 (60%原图 + 40%热力图)
    overlay = cv2.addWeighted(img, 0.6, heatmap_color, 0.4, 0)
    
    # 保存结果
    cv2.imencode('.jpg', overlay)[1].tofile(output_path)
    print(f"🔥 热力图已生成并保存至: {output_path}")

# ====== 新增：结合心理学理论的自然语言建议 ======
def generate_psychological_report(ent, txt, subj_ratio, edge_den, color_sat, predicted_ctr):
    print("\n" + "💡 心理学与视觉营销诊断报告 ".center(46, "="))
    
    # 1. 认知负荷理论 (Cognitive Load Theory)
    # 依赖特征：图像熵 (混乱度)、文本密度
    print("【1. 认知负荷理论分析】")
    if ent > 7.5 or txt > 0.3:
        print(" -> ⚠️ 画面元素过多/文案过密。消费者在短时间内处理信息的“工作记忆”有限，过高的视觉复杂度会引发认知超载，导致滑动跳失。")
        print(" -> 🛠️ 优化建议：做减法。留白（Negative Space），减少多余的装饰背景，精简营销文案，只保留1-2个核心卖点。")
    else:
        print(" -> ✅ 视觉清爽，认知负荷低。消费者能瞬间捕捉商品，符合“极简即高效”的信息传递原则。")

    # 2. 冯·雷斯托夫效应 / 格式塔图形与背景法则 (Isolation Effect / Figure-Ground)
    # 依赖特征：主体占比、边缘密度
    print("\n【2. 主体视觉与格式塔法则分析】")
    if subj_ratio < 0.2:
        print(" -> ⚠️ 主体占比偏小，背景反客为主。违背了格式塔心理学中的“图形与背景分离”原则。")
        print(" -> 🛠️ 优化建议：放大商品主体，或使用景深虚化（降低背景边缘密度），利用“冯·雷斯托夫效应”让商品本身成为唯一视觉焦点。")
    elif subj_ratio > 0.6:
        print(" -> ✅ 主体极其突出，占据核心视野，能迅速建立视觉锚点，有效激发用户的点击欲望。")
    else:
        print(" -> ℹ️ 主体大小适中，建议配合高对比度色彩进一步强化主体轮廓。")

    # 3. 色彩情绪与唤醒理论 (Color Psychology & Arousal)
    # 依赖特征：色彩饱和度
    print("\n【3. 色彩情绪唤醒理论】")
    if color_sat > 0.6:
        print(" -> ✅ 色彩饱和度高。高饱和度能唤起强烈的情感波动（如热情、食欲、活力），极度适合促销和冲动消费品类（如食品、功能饮料）。")
    elif color_sat < 0.3:
        print(" -> ℹ️ 整体偏冷色调或低饱和。传递出高级、冷静、克制的品牌调性（适合3C数码、高端个护）。但如果不是为了营造高级感，可能在信息流中缺乏“吸睛力”。")
        print(" -> 🛠️ 优化建议：如果是快消品，建议在热力图焦点区域（如按钮、核心卖点）增加明黄色、亮红色等高唤醒度色彩。")
    else:
        print(" -> ✅ 色彩饱和度处于舒适区间，视觉平稳。")
        
    print("=" * 50)


# ====== 核心预测逻辑 ======
def predict_image_ctr(img_path, model_path, scaler_path):
    if not os.path.exists(img_path):
        print(f"找不到图片: {img_path}")
        return None

    # 1. 加载模型
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # 2. 读取并提取特征
    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    img_resized = cv2.resize(img, IMG_SIZE)

    ent = get_image_entropy(img_resized)
    txt = get_text_density(img_path)
    subj_ratio = get_subject_area_ratio(img_resized)
    edge_den = get_edge_density(img_resized)
    color_sat = get_color_saturation(img_resized)
    clip_feat = get_clip_feature(img_path)

    all_feat = [ent, txt, subj_ratio, edge_den, color_sat] + list(clip_feat)
    X_scaled = scaler.transform(np.array([all_feat], dtype=np.float32))

    # 3. 进行预测
    predicted_ctr = model.predict(X_scaled)[0]
    
    print("\n" + "🌟" * 20)
    print(f"  预测图片: {os.path.basename(img_path)}")
    print(f"  预估 CTR 相对值: {predicted_ctr:.4f}")
    print("🌟" * 20)
    
    # 4. 生成视觉焦点热力图
    heatmap_save_path = os.path.join(os.path.dirname(img_path), "heatmap_" + os.path.basename(img_path))
    generate_attention_heatmap(img_path, heatmap_save_path)
    
    # 5. 输出心理学分析报告
    generate_psychological_report(ent, txt, subj_ratio, edge_den, color_sat, predicted_ctr)
    
    return predicted_ctr


if __name__ == "__main__":
    # 替换为你真实的路径
    MODEL_PATH = r"D:\Afile\compet\heatmap\ctr_xgboost_model_global.pkl"
    SCALER_PATH = r"D:\Afile\compet\heatmap\ctr_feature_scaler.pkl" 
    
    # 找一张你要测试的主图
    TEST_IMAGE = r"D:\Afile\compet\heatmap\lamp_2678.jpg"
    
    predict_image_ctr(TEST_IMAGE, MODEL_PATH, SCALER_PATH)