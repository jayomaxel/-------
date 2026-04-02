import cv2
import numpy as np
import pickle
import pytesseract

# ==============================
# 路径
# ==============================
IMAGE_PATH = r"C:\Users\wangj\Desktop\ctr_project\test_image.jpg"
MODEL_PATH = r"C:\Users\wangj\ctr_xgboost_model_global.pkl"


# ==============================
# 加载模型
# ==============================
def load_model(path):
    with open(path, "rb") as f:
        return pickle.load(f)


# ==============================
# 视觉熵
# ==============================
def calc_entropy(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0,256])
    hist = hist / hist.sum()
    hist = hist[hist > 0]
    return -np.sum(hist * np.log2(hist))


# ==============================
# OCR文本密度
# ==============================
def calc_text_density(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return np.sum(edges > 0) / edges.size

# ==============================
# 特征构建（简化）
# ==============================
def build_features(img):
    entropy = calc_entropy(img)
    text_density = calc_text_density(img)

    # 🔥 补充3个特征（关键）
    h, w, _ = img.shape
    aspect_ratio = w / h

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    contrast = np.std(gray)

    extra = [aspect_ratio, brightness, contrast]

    # CLIP占位
    clip = np.zeros(512)

    features = np.concatenate((
        [entropy, text_density],
        extra,
        clip
    ))

    return features.reshape(1, -1), entropy, text_density

# ==============================
# 🔥 核心：生成热力图
# ==============================
def generate_heatmap(img, model, window_size=50, stride=25):
    h, w, _ = img.shape
    heatmap = np.zeros((h, w))

    # 原始预测
    base_feat, _, _ = build_features(img)
    base_pred = model.predict(base_feat)[0]

    mean_color = img.mean(axis=(0,1))

    for y in range(0, h - window_size, stride):
        for x in range(0, w - window_size, stride):

            occluded = img.copy()
            occluded[y:y+window_size, x:x+window_size] = mean_color

            feat, _, _ = build_features(occluded)
            pred = model.predict(feat)[0]

            impact = base_pred - pred

            heatmap[y:y+window_size, x:x+window_size] += impact

    # 归一化
    heatmap = np.maximum(heatmap, 0)
    heatmap = heatmap / (heatmap.max() + 1e-6)

    return heatmap


# ==============================
# 热力图可视化
# ==============================
def visualize_heatmap(img, heatmap):
    heatmap_resized = cv2.resize(heatmap, (img.shape[1], img.shape[0]))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)

    colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

    overlay = cv2.addWeighted(img, 0.7, colored, 0.3, 0)

    return overlay


# ==============================
# 热力图分析
# ==============================
def analyze_heatmap(heatmap):
    mean = np.mean(heatmap)
    high = np.sum(heatmap > 0.6) / heatmap.size
    var = np.var(heatmap)

    h, w = heatmap.shape
    center = heatmap[h//4:3*h//4, w//4:3*w//4]
    center_focus = np.mean(center)

    return mean, high, var, center_focus


# ==============================
# 建议生成
# ==============================
def generate_advice(entropy, text_density, heat):
    mean, high, var, center = heat

    problems, psychology, suggestions = [], [], []

    if entropy > 4.5:
        problems.append("背景复杂")
        psychology.append("认知负荷过高")
        suggestions.append("简化背景")

    if text_density > 0.25:
        problems.append("文本过多")
        psychology.append("信息过载")
        suggestions.append("减少文字")

    if var < 0.02:
        problems.append("注意力分散")
        psychology.append("缺乏选择性注意")
        suggestions.append("增强主体")

    if center < mean:
        problems.append("主体不在中心")
        psychology.append("违反中心偏好")
        suggestions.append("主体居中")

    if high < 0.15:
        problems.append("吸引力不足")
        psychology.append("刺激不足")
        suggestions.append("增强对比")

    return problems, psychology, suggestions


# ==============================
# 主函数
# ==============================
def main():
    img = cv2.imread(IMAGE_PATH)
    model = load_model(MODEL_PATH)

    # 特征 + CTR
    feat, entropy, text_density = build_features(img)
    ctr = model.predict(feat)[0]

    # 🔥 自动生成热力图
    heatmap = generate_heatmap(img, model)

    # 可视化
    overlay = visualize_heatmap(img, heatmap)
    cv2.imwrite("heatmap_result.jpg", overlay)

    # 分析
    heat_features = analyze_heatmap(heatmap)

    # 建议
    problems, psychology, suggestions = generate_advice(
        entropy, text_density, heat_features
    )

    # 输出
    print("\n===== CTR分析 =====")
    print(f"CTR预测: {ctr:.4f}")

    print("\n问题:")
    print(problems)

    print("\n建议:")
    print(suggestions)

    print("\n热力图已保存：heatmap_result.jpg")


if __name__ == "__main__":
    main()