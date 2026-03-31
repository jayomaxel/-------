"""
File Purpose:
    Streamlit main interface for the "电商主图智能认知诊断系统".

Main Functions:
    - run_analysis(uploaded_file: Any, dataset_key: str) -> None
    - render_sidebar() -> tuple[str, Any, bool]
    - render_main_content(uploaded_file: Any, dataset_key: str) -> None

Input / Output Types:
    - Input:
        uploaded_file: Streamlit UploadedFile (jpg/png)
        dataset_key: str from config.DATASETS keys
    - Output:
        UI rendering via Streamlit and analysis results stored in st.session_state
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st

import config


ANALYSIS_STATE_KEYS = (
    "img_array",
    "original_image",
    "image_info",
    "features",
    "ctr_score",
    "ctr_pct",
    "heatmap",
    "similar",
    "advice",
    "step_errors",
    "analysis_done",
    "model_ready",
    "cache_ready",
)


def resolve_path(path_value: str) -> Path:
    """
    Resolve a relative/absolute configured path to an absolute Path.

    Args:
        path_value: Path string from `config.py`.

    Returns:
        Path: Absolute resolved path.
    """
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (config.ROOT_DIR / path_obj).resolve()


def clear_analysis_state() -> None:
    """
    Clear analysis-related keys in Streamlit session state.

    Returns:
        None
    """
    for key in ANALYSIS_STATE_KEYS:
        st.session_state.pop(key, None)


def init_session_state() -> None:
    """
    Initialize required session state defaults.

    Returns:
        None
    """
    if "dataset_key" not in st.session_state:
        st.session_state.dataset_key = config.DEFAULT_DATASET
    if "prev_dataset_key" not in st.session_state:
        st.session_state.prev_dataset_key = st.session_state.dataset_key
    if "step_errors" not in st.session_state:
        st.session_state.step_errors = {}


def get_dataset_paths(dataset_key: str) -> dict[str, Path]:
    """
    Get absolute paths for selected dataset config.

    Args:
        dataset_key: Dataset key in `config.DATASETS`.

    Returns:
        dict[str, Path]: Contains `images_dir`, `cache_vectors`, and `model_path`.

    Raises:
        ValueError: If dataset_key is not registered in config.DATASETS.
    """
    if dataset_key not in config.DATASETS:
        valid = ", ".join(config.DATASETS.keys())
        raise ValueError(f"Unknown dataset_key: {dataset_key}. Available: {valid}")
    dataset_cfg = config.DATASETS[dataset_key]
    return {
        "images_dir": resolve_path(dataset_cfg["images_dir"]),
        "cache_vectors": resolve_path(dataset_cfg["cache_vectors"]),
        "model_path": resolve_path(dataset_cfg["model_path"]),
    }


def mock_ctr_from_features(features: dict) -> tuple[float, int]:
    """
    Build a deterministic mock CTR score when model file is not ready.

    Args:
        features: Extracted feature dictionary.

    Returns:
        tuple[float, int]: mock (ctr_score, ctr_percentile)
    """
    score = config.CTR_PCT_MID / 100.0
    entropy = float(features.get("entropy", 0.0))
    contrast = float(features.get("contrast", 0.0))
    text_density = float(features.get("text_density", 0.0))
    brightness = float(features.get("brightness", 0.0))

    if entropy > config.ENTROPY_HIGH:
        score -= 0.08
    if contrast < config.CONTRAST_LOW:
        score -= 0.08
    if text_density > config.TEXT_DENSITY_HIGH:
        score -= 0.08
    if brightness < config.BRIGHTNESS_LOW or brightness > config.BRIGHTNESS_HIGH:
        score -= 0.06

    score = float(np.clip(score, 0.0, 1.0))
    percentile = int(round(score * 100))
    return score, percentile


def run_analysis(uploaded_file: Any, dataset_key: str) -> None:
    """
    Execute the analysis pipeline step-by-step with independent error handling.

    Steps:
        1) preprocess_image
        2) extract_features
        3) predict_ctr
        4) generate_heatmap
        5) retrieve_similar
        6) generate_advice

    Args:
        uploaded_file: Streamlit uploaded image object.
        dataset_key: Dataset key selected in UI.

    Returns:
        None. Results are written into `st.session_state`.
    """
    step_errors: dict[str, str] = {}
    paths = get_dataset_paths(dataset_key)
    st.session_state.model_ready = paths["model_path"].exists()
    st.session_state.cache_ready = paths["cache_vectors"].exists()

    progress = st.progress(0, text="准备开始分析...")
    start_ts = time.time()

    st.session_state.img_array = None
    st.session_state.features = None
    st.session_state.ctr_score = None
    st.session_state.ctr_pct = None
    st.session_state.heatmap = None
    st.session_state.similar = []
    st.session_state.advice = []

    try:
        from PIL import Image  # lazy import
        from modules.preprocessor import preprocess_image  # lazy import

        uploaded_file.seek(0)
        pil_image = Image.open(uploaded_file).convert("RGB")
        st.session_state.original_image = np.array(pil_image)
        st.session_state.image_info = {
            "name": uploaded_file.name,
            "width": pil_image.width,
            "height": pil_image.height,
            "format": pil_image.format if pil_image.format else "未知",
        }
        st.session_state.img_array = preprocess_image(pil_image)
    except Exception as exc:
        step_errors["preprocess"] = f"图像预处理失败: {exc}"
    progress.progress(15, text="步骤 1/6: 图像预处理完成")

    try:
        if st.session_state.img_array is not None:
            from modules.feature_extractor import extract_features  # lazy import

            st.session_state.features = extract_features(st.session_state.img_array)
        else:
            step_errors["features"] = "特征提取跳过：图像预处理未成功。"
    except Exception as exc:
        step_errors["features"] = f"特征提取失败: {exc}"
    progress.progress(35, text="步骤 2/6: 视觉特征提取完成")

    try:
        if st.session_state.features is not None:
            if st.session_state.model_ready:
                from modules.ctr_predictor import predict_ctr  # lazy import

                ctr_score, ctr_pct = predict_ctr(st.session_state.features, dataset_key)
                st.session_state.ctr_score = float(ctr_score)
                st.session_state.ctr_pct = int(ctr_pct)
            else:
                st.session_state.ctr_score, st.session_state.ctr_pct = mock_ctr_from_features(
                    st.session_state.features
                )
                step_errors["ctr"] = "模型未就绪，当前显示模拟值。"
        else:
            step_errors["ctr"] = "CTR 预测跳过：缺少视觉特征。"
            st.session_state.ctr_score = 0.0
            st.session_state.ctr_pct = 0
    except Exception as exc:
        if st.session_state.features is not None:
            st.session_state.ctr_score, st.session_state.ctr_pct = mock_ctr_from_features(
                st.session_state.features
            )
            step_errors["ctr"] = f"CTR 预测失败，已回退模拟值: {exc}"
        else:
            st.session_state.ctr_score = 0.0
            st.session_state.ctr_pct = 0
            step_errors["ctr"] = f"CTR 预测失败: {exc}"
    progress.progress(55, text="步骤 3/6: CTR 预测完成")

    try:
        if st.session_state.img_array is not None:
            from modules.heatmap import generate_heatmap  # lazy import

            img_array = st.session_state.img_array
            with st.spinner("正在生成注意力热力图（遮挡分析中，约 30~120 秒）..."):
                st.session_state.heatmap = generate_heatmap(img_array, dataset_key=dataset_key)
        else:
            step_errors["heatmap"] = "热力图生成跳过：图像预处理未成功。"
    except Exception as exc:
        step_errors["heatmap"] = f"热力图生成失败: {exc}"
    progress.progress(70, text="步骤 4/6: 热力图生成完成")

    try:
        if not st.session_state.cache_ready:
            step_errors["similar"] = "向量缓存未找到，请先运行 precompute_vectors.py。"
            st.session_state.similar = []
        elif st.session_state.features is not None and "clip_vector" in st.session_state.features:
            from modules.retriever import retrieve_similar  # lazy import

            st.session_state.similar = retrieve_similar(
                st.session_state.features["clip_vector"],
                dataset_key=dataset_key,
                top_k=config.TOP_K_SIMILAR,
            )
        else:
            step_errors["similar"] = "相似检索跳过：缺少 CLIP 向量。"
            st.session_state.similar = []
    except Exception as exc:
        step_errors["similar"] = f"相似检索失败: {exc}"
        st.session_state.similar = []
    progress.progress(85, text="步骤 5/6: 相似检索完成")

    try:
        if st.session_state.features is not None:
            from modules.advisor import generate_advice  # lazy import

            st.session_state.advice = generate_advice(
                st.session_state.features,
                float(st.session_state.ctr_score if st.session_state.ctr_score is not None else 0.0),
                int(st.session_state.ctr_pct if st.session_state.ctr_pct is not None else 0),
            )
        else:
            step_errors["advice"] = "优化建议生成跳过：缺少视觉特征。"
            st.session_state.advice = []
    except Exception as exc:
        step_errors["advice"] = f"优化建议生成失败: {exc}"
        st.session_state.advice = []
    progress.progress(100, text="步骤 6/6: 优化建议生成完成")

    elapsed = time.time() - start_ts
    progress.empty()
    st.session_state.step_errors = step_errors
    st.session_state.analysis_done = True
    st.success(f"分析完成，用时 {elapsed:.2f}s")


def inject_styles() -> None:
    """
    Inject dashboard styles while keeping default white page theme.

    Returns:
        None
    """
    st.markdown(
        """
<style>
[data-testid="collapsedControl"] {
    display: none !important;
}
[data-testid="stSidebar"] {
    min-width: 280px !important;
    max-width: 280px !important;
}
.panel {
    background: #101828;
    color: #F8FAFC;
    border-radius: 14px;
    border: 1px solid #1F2937;
    padding: 16px;
    margin-bottom: 14px;
}
.panel h4 {
    margin: 0 0 10px 0;
    color: #E2E8F0;
}
.muted { color: #94A3B8; font-size: 12px; }
.kpi {
    background: #0B1220;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 10px 12px;
    text-align: center;
}
.kpi-label { color: #94A3B8; font-size: 12px; }
.kpi-value { color: #F8FAFC; font-size: 22px; font-weight: 700; }
.bar-wrap { margin-bottom: 10px; }
.bar-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 4px;
    color: #CBD5E1;
}
.bar-bg {
    width: 100%;
    height: 8px;
    background: #1E293B;
    border-radius: 999px;
    overflow: hidden;
}
.bar-fg {
    height: 100%;
    border-radius: 999px;
}
.advice-card {
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
    border-left: 5px solid;
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_status_line(name: str, ready: bool, ready_text: str, pending_text: str) -> None:
    """
    Render a simple status row in sidebar.

    Args:
        name: Module name.
        ready: Status flag.
        ready_text: Text when ready.
        pending_text: Text when pending.

    Returns:
        None
    """
    color = "#16A34A" if ready else "#CA8A04"
    dot = "●"
    message = ready_text if ready else pending_text
    st.markdown(
        f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin:4px 0;">
  <span>{dot} {name}</span>
  <span style="color:{color};font-size:12px;">{message}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, Any, bool]:
    """
    Render sidebar controls and status panel.

    Returns:
        tuple[str, Any, bool]:
            - dataset_key
            - uploaded_file
            - run_clicked
    """
    dataset_options = list(config.DATASETS.keys())
    current_idx = dataset_options.index(st.session_state.dataset_key)

    with st.sidebar:
        st.title("电商主图智能认知诊断系统")
        st.caption("上传商品主图后，系统将自动完成特征提取、CTR预测、热力图解释与相似爆款检索。")

        selected_dataset = st.selectbox(
            "品类选择",
            options=dataset_options,
            index=current_idx,
        )
        st.session_state.dataset_key = selected_dataset

        uploader_key = f"uploader_{selected_dataset}"
        uploaded_file = st.file_uploader(
            "上传商品主图",
            type=["jpg", "png"],
            key=uploader_key,
        )

        if uploaded_file is not None:
            try:
                from PIL import Image  # lazy import

                uploaded_file.seek(0)
                preview = Image.open(uploaded_file)
                st.image(preview, use_container_width=True)
                st.caption(
                    f"文件: {uploaded_file.name} | 尺寸: {preview.width}×{preview.height}"
                )
            except Exception as exc:
                st.warning(f"图片预览失败: {exc}")

        run_clicked = st.button("开始分析", disabled=uploaded_file is None, use_container_width=True)

        sample_size = config.DATASETS[selected_dataset]["sample_size"]
        st.info(f"当前品类参考图片数量: {sample_size}")

        dataset_paths = get_dataset_paths(selected_dataset)
        cache_ready = dataset_paths["cache_vectors"].exists()
        model_ready = dataset_paths["model_path"].exists()

        st.markdown("### 模块状态")
        render_status_line("特征提取", True, "就绪", "未就绪")
        render_status_line("相似检索", cache_ready, "就绪", "等待向量缓存")
        render_status_line("CTR 预测", model_ready, "就绪", "等待模型文件")
        render_status_line("热力图", False, "就绪", "等待 C 同学")

    return selected_dataset, uploaded_file, run_clicked


def metric_color_for_feature(name: str, value: float) -> str:
    """
    Select metric color by threshold rules from config constants.

    Args:
        name: Feature name.
        value: Numeric value.

    Returns:
        str: HEX color string.
    """
    if name == "entropy":
        if value > config.ENTROPY_HIGH:
            return "#EF4444"
        if value < config.ENTROPY_LOW:
            return "#F59E0B"
        return "#22C55E"
    if name == "contrast":
        if value < config.CONTRAST_LOW:
            return "#EF4444"
        if value > config.CONTRAST_HIGH:
            return "#F59E0B"
        return "#22C55E"
    if name == "text_density":
        if value > config.TEXT_DENSITY_HIGH:
            return "#EF4444"
        return "#22C55E"
    if name == "brightness":
        if value < config.BRIGHTNESS_LOW:
            return "#EF4444"
        if value > config.BRIGHTNESS_HIGH:
            return "#F59E0B"
        return "#22C55E"
    return "#38BDF8"


def render_metric_block(label: str, value: str, color: str) -> None:
    """
    Render a single KPI block.

    Args:
        label: KPI label.
        value: KPI value text.
        color: Value color.

    Returns:
        None
    """
    st.markdown(
        f"""
<div class="kpi">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value" style="color:{color};">{value}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_progress_bar(label: str, value_text: str, ratio: float, color: str) -> None:
    """
    Render a custom progress bar with color.

    Args:
        label: Bar label.
        value_text: Display value text.
        ratio: Progress ratio in [0, 1].
        color: Bar color.

    Returns:
        None
    """
    width = int(np.clip(ratio, 0.0, 1.0) * 100)
    st.markdown(
        f"""
<div class="bar-wrap">
  <div class="bar-row"><span>{label}</span><span>{value_text}</span></div>
  <div class="bar-bg"><div class="bar-fg" style="width:{width}%;background:{color};"></div></div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_section_1(uploaded_file: Any) -> None:
    """
    Render section 1: uploaded image preview and metadata.

    Args:
        uploaded_file: Streamlit uploaded image.

    Returns:
        None
    """
    st.markdown('<div class="panel"><h4>区域1 — 上传图片预览与元信息</h4>', unsafe_allow_html=True)
    image_info = st.session_state.get("image_info")
    original_image = st.session_state.get("original_image")

    if original_image is None and uploaded_file is not None:
        try:
            from PIL import Image  # lazy import

            uploaded_file.seek(0)
            preview = Image.open(uploaded_file).convert("RGB")
            original_image = np.array(preview)
            image_info = {
                "name": uploaded_file.name,
                "width": preview.width,
                "height": preview.height,
                "format": preview.format if preview.format else "未知",
            }
        except Exception as exc:
            st.error(f"图片预览失败: {exc}")

    if original_image is not None:
        st.image(original_image, use_container_width=True)

    if image_info:
        c1, c2, c3 = st.columns(3)
        c1.metric("宽度", f'{image_info.get("width", "-")} px')
        c2.metric("高度", f'{image_info.get("height", "-")} px')
        c3.metric("格式", str(image_info.get("format", "未知")))
        st.caption(f'文件名: {image_info.get("name", "未知")}')

    if "preprocess" in st.session_state.step_errors:
        st.error(st.session_state.step_errors["preprocess"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_section_2() -> None:
    """
    Render section 2: visual feature metrics and threshold-colored bars.

    Returns:
        None
    """
    st.markdown('<div class="panel"><h4>区域2 — 视觉特征指标</h4>', unsafe_allow_html=True)
    features = st.session_state.get("features")

    if not features:
        st.info("尚未生成特征结果。点击“开始分析”后显示。")
        if "features" in st.session_state.step_errors:
            st.error(st.session_state.step_errors["features"])
        st.markdown("</div>", unsafe_allow_html=True)
        return

    entropy = float(features.get("entropy", 0.0))
    contrast = float(features.get("contrast", 0.0))
    text_density = float(features.get("text_density", 0.0))
    brightness = float(features.get("brightness", 0.0))
    saturation = float(features.get("saturation", 0.0))

    cols = st.columns(5)
    with cols[0]:
        render_metric_block("视觉熵", f"{entropy:.4f}", metric_color_for_feature("entropy", entropy))
    with cols[1]:
        render_metric_block("颜色对比度", f"{contrast:.4f}", metric_color_for_feature("contrast", contrast))
    with cols[2]:
        render_metric_block("文字密度", f"{text_density:.4f}", metric_color_for_feature("text_density", text_density))
    with cols[3]:
        render_metric_block("亮度", f"{brightness:.4f}", metric_color_for_feature("brightness", brightness))
    with cols[4]:
        render_metric_block("饱和度", f"{saturation:.4f}", metric_color_for_feature("saturation", saturation))

    st.markdown("#### 关键指标进度")
    entropy_ratio = entropy / max(config.ENTROPY_HIGH * 1.5, 1e-6)
    contrast_ratio = contrast / max(config.CONTRAST_HIGH * 1.25, 1e-6)
    text_ratio = text_density
    brightness_ratio = brightness

    render_progress_bar(
        "视觉熵",
        f"{entropy:.4f}",
        entropy_ratio,
        metric_color_for_feature("entropy", entropy),
    )
    render_progress_bar(
        "颜色对比度",
        f"{contrast:.4f}",
        contrast_ratio,
        metric_color_for_feature("contrast", contrast),
    )
    render_progress_bar(
        "文字密度",
        f"{text_density:.4f}",
        text_ratio,
        metric_color_for_feature("text_density", text_density),
    )
    render_progress_bar(
        "亮度",
        f"{brightness:.4f}",
        brightness_ratio,
        metric_color_for_feature("brightness", brightness),
    )

    if "features" in st.session_state.step_errors:
        st.error(st.session_state.step_errors["features"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_section_3(dataset_key: str) -> None:
    """
    Render section 3: CTR score board and percentile progress.

    Args:
        dataset_key: Selected dataset key.

    Returns:
        None
    """
    st.markdown('<div class="panel"><h4>区域3 — CTR 预测</h4>', unsafe_allow_html=True)
    ctr_score = st.session_state.get("ctr_score")
    ctr_pct = st.session_state.get("ctr_pct")
    model_ready = bool(st.session_state.get("model_ready", False))

    if ctr_score is None or ctr_pct is None:
        st.info("尚未生成 CTR 结果。点击“开始分析”后显示。")
        if "ctr" in st.session_state.step_errors:
            st.warning(st.session_state.step_errors["ctr"])
        st.markdown("</div>", unsafe_allow_html=True)
        return

    label = "CTR 预测分数" if model_ready else "CTR 预测分数 (模型未就绪)"
    st.metric(label, f"{float(ctr_score):.4f}")

    pct_value = int(np.clip(int(ctr_pct), 0, 100))
    if pct_value < config.CTR_PCT_LOW:
        pct_color = "#EF4444"
    elif pct_value < config.CTR_PCT_MID:
        pct_color = "#F59E0B"
    else:
        pct_color = "#22C55E"

    render_progress_bar("数据集百分位", f"{pct_value}%", pct_value / 100.0, pct_color)
    st.caption(f"当前品类: {dataset_key}")

    if "ctr" in st.session_state.step_errors:
        st.warning(st.session_state.step_errors["ctr"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_section_4() -> None:
    """
    Render section 4: original image vs heatmap comparison and legend.

    Returns:
        None
    """
    st.markdown('<div class="panel"><h4>区域4 — 热力图对比</h4>', unsafe_allow_html=True)
    st.caption("注意：热力图采用遮挡敏感性分析，每张图片需要 30~120 秒，请耐心等待。")
    original_image = st.session_state.get("original_image")
    heatmap = st.session_state.get("heatmap")

    if original_image is None:
        st.info("尚无原图可显示。")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    c1, c2 = st.columns(2)
    with c1:
        st.image(original_image, caption="原图", use_container_width=True)
    with c2:
        if heatmap is not None:
            st.image(heatmap, caption="梯度热力图叠加图（Grad-CAM）", use_container_width=True)
        else:
            st.warning("热力图未生成。")

    st.markdown(
        """
<div style="margin-top:8px;">
  <span class="muted">色彩图例：</span>
  <div style="height:10px;border-radius:999px;background:linear-gradient(90deg,#38BDF8,#22C55E,#F59E0B,#EF4444);"></div>
  <div class="muted">蓝色(低注意力) → 绿色(中) → 橙色(较高) → 红色(高注意力)</div>
</div>
""",
        unsafe_allow_html=True,
    )
    if "heatmap" in st.session_state.step_errors:
        st.warning(st.session_state.step_errors["heatmap"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_section_5(dataset_key: str) -> None:
    """
    Render section 5: top-k similar items cards.

    Args:
        dataset_key: Selected dataset key.

    Returns:
        None
    """
    st.markdown('<div class="panel"><h4>区域5 — 前5相似爆款</h4>', unsafe_allow_html=True)
    paths = get_dataset_paths(dataset_key)
    if not paths["cache_vectors"].exists():
        st.warning("相似检索缓存未找到，请先运行 precompute_vectors.py。")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    similar = st.session_state.get("similar", [])
    if not similar:
        st.info("尚无相似检索结果。点击“开始分析”后显示。")
        if "similar" in st.session_state.step_errors:
            st.warning(st.session_state.step_errors["similar"])
        st.markdown("</div>", unsafe_allow_html=True)
        return

    cols = st.columns(min(len(similar), config.TOP_K_SIMILAR))
    for col, item in zip(cols, similar):
        with col:
            st.markdown(
                f"""
<div style="background:#0B1220;border:1px solid #1E293B;border-radius:12px;padding:10px;">
  <div style="font-size:12px;color:#94A3B8;">#{item.get("rank", "-")} {item.get("img_name", "")}</div>
  <div style="font-size:12px;color:#CBD5E1;">相似度: {float(item.get("similarity", 0.0)):.4f}</div>
  <div style="font-size:12px;color:#CBD5E1;">CTR: {float(item.get("relative_ctr", 0.0)):.4f}</div>
  <div style="font-size:12px;color:#CBD5E1;">价格: {float(item.get("price", 0.0)):.4f}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            img_path = item.get("img_path")
            if img_path is not None and Path(img_path).exists():
                st.image(img_path, use_container_width=True)
            else:
                st.caption("图片文件不存在")

    if "similar" in st.session_state.step_errors:
        st.warning(st.session_state.step_errors["similar"])
    st.markdown("</div>", unsafe_allow_html=True)


def advice_card_color(priority: str) -> tuple[str, str]:
    """
    Map advice priority to border/background colors.

    Args:
        priority: Advice priority text.

    Returns:
        tuple[str, str]: (border_color, background_color)
    """
    if priority == "高":
        return "#EF4444", "#2A1215"
    if priority == "中":
        return "#F59E0B", "#2A1E12"
    return "#22C55E", "#0F2017"


def render_section_6() -> None:
    """
    Render section 6: prioritized advice cards and diagnosis summary.

    Returns:
        None
    """
    st.markdown('<div class="panel"><h4>区域6 — 优化建议与诊断概览</h4>', unsafe_allow_html=True)
    advice = st.session_state.get("advice", [])

    if not advice:
        st.info("尚无优化建议。点击“开始分析”后显示。")
        if "advice" in st.session_state.step_errors:
            st.warning(st.session_state.step_errors["advice"])
        st.markdown("</div>", unsafe_allow_html=True)
        return

    left, right = st.columns([3, 1.2])
    with left:
        for item in advice:
            priority = str(item.get("priority", "低"))
            border_color, background_color = advice_card_color(priority)
            st.markdown(
                f"""
<div class="advice-card" style="border-left-color:{border_color};background:{background_color};">
  <div style="font-size:12px;color:#94A3B8;">{priority}优先级 | {item.get("category", "")}</div>
  <div style="font-size:14px;color:#F8FAFC;margin-top:4px;">{item.get("issue", "")}</div>
  <div style="font-size:12px;color:#CBD5E1;margin-top:6px;">{item.get("suggestion", "")}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    with right:
        high = sum(1 for x in advice if x.get("priority") == "高")
        mid = sum(1 for x in advice if x.get("priority") == "中")
        low = sum(1 for x in advice if x.get("priority") == "低")
        st.markdown(
            f"""
<div style="background:#0B1220;border:1px solid #1E293B;border-radius:12px;padding:12px;">
  <div style="color:#94A3B8;font-size:12px;">诊断概览</div>
  <div style="color:#F8FAFC;">高优先级: {high}</div>
  <div style="color:#F8FAFC;">中优先级: {mid}</div>
  <div style="color:#F8FAFC;">低优先级: {low}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    if "advice" in st.session_state.step_errors:
        st.warning(st.session_state.step_errors["advice"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_empty_state() -> None:
    """
    Render guide view when no image is uploaded.

    Returns:
        None
    """
    st.markdown(
        """
<div style="padding:28px;border:1px solid #E2E8F0;border-radius:14px;background:#F8FAFC;">
  <h3 style="margin-top:0;">欢迎使用电商主图智能认知诊断系统</h3>
  <p>请在左侧选择品类并上传商品主图。系统将自动执行：</p>
  <ol>
    <li>视觉特征提取（熵、对比度、文字密度、亮度/饱和度）</li>
    <li>CTR 预测与百分位评估</li>
    <li>梯度热力图（Grad-CAM）解释</li>
    <li>相似爆款检索与优化建议生成</li>
  </ol>
  <p style="margin-bottom:0;color:#475569;">上传完成后点击“开始分析”。</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_main_content(uploaded_file: Any, dataset_key: str) -> None:
    """
    Render main page content with six required sections.

    Args:
        uploaded_file: Streamlit uploaded image.
        dataset_key: Current selected dataset key.

    Returns:
        None
    """
    st.title("电商主图智能认知诊断系统")
    st.caption(f"当前品类：{dataset_key}")

    if uploaded_file is None:
        render_empty_state()
        return

    # 按前端分区图采用纵向流程布局：区域1 -> 2 -> 3 -> 4 -> 5 -> 6
    render_section_1(uploaded_file)
    render_section_2()
    render_section_3(dataset_key)
    render_section_4()
    render_section_5(dataset_key)
    render_section_6()


def main() -> None:
    """
    Streamlit application entry point.

    Returns:
        None
    """
    st.set_page_config(
        page_title="电商主图智能认知诊断系统",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()
    inject_styles()

    dataset_key, uploaded_file, run_clicked = render_sidebar()

    if st.session_state.prev_dataset_key != dataset_key:
        clear_analysis_state()
        st.session_state.prev_dataset_key = dataset_key
        st.session_state.dataset_key = dataset_key
        st.info("品类已切换，已清空历史分析结果，请重新点击“开始分析”。")

    if run_clicked and uploaded_file is not None:
        run_analysis(uploaded_file=uploaded_file, dataset_key=dataset_key)

    render_main_content(uploaded_file=uploaded_file, dataset_key=dataset_key)


if __name__ == "__main__":
    main()
