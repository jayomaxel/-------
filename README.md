# AI Analysis Addendum

- Process note: this README should be updated together with each implementation step.
- Current feature progress:
  1. Added dependency `openai>=1.0.0`.
  2. Added AI model config fields and environment variable override support.
  3. Added backend endpoint `POST /ai-analysis`.
  4. Replaced the frontend advice and psychology sections with one AI analysis card.
  5. Added `modules/ai_analyzer.py` and switched AI analysis to structured JSON output.
  6. Simplified `/ai-analysis` request body to `tone + features + ctr_score`.
  7. Added a root one-click startup script `start.bat`.
  8. Moved the frontend AI request into `src/api/ai.ts` and made the AI card self-managed.
  9. Documented the runtime interaction flow between `/analyze` and `/ai-analysis`.
  10. Cleaned up AI card UI copy and states to match the acceptance behavior.
  11. Removed leftover frontend copy related to the deprecated advice and psychology sections.
  12. Added AI setup modal, front-end API Key configuration, always-visible AI card, and same-tone cache.
- `requirements.txt` now includes `openai>=1.0.0`.
- `config.py` now exposes `AI_MODEL_BASE_URL`, `AI_MODEL_API_KEY`, `AI_MODEL_NAME`, `AI_MAX_TOKENS`, and `AI_TIMEOUT`.
- These AI settings support environment variable overrides, which is safer than committing a real API key.
- New endpoint: `POST /ai-analysis`
- Supported `tone` values: `professional`, `gentle`, `direct`, `marketing`
- Frontend now calls `/analyze` first, then reuses `features` and `ctr.score` to call `/ai-analysis`.
- The old advice and psychological report panels are replaced by one AI report card with four tone switches.
- `modules/ai_analyzer.py` is now the active backend analyzer and asks the model to return JSON with `summary`, `strengths`, `problems`, and `suggestions`.
- If `AI_MODEL_API_KEY` is missing or invalid, `/ai-analysis` now returns a friendly configuration error instead of exposing raw provider details.
- `/ai-analysis` now also accepts an optional `api_key` from the frontend and prefers that over the server default.
- `/analyze` keeps all original fields, including `advice`, as fallback data. The frontend simply no longer displays that block.
- Root startup entry: `start.bat`
- `start.bat` is a thin wrapper around `start_all.bat`, so users can double-click or run it directly from the repo root.
- Frontend AI API helper now lives in `src/api/ai.ts`.
- `AIAnalysisCard.tsx` now requests `/ai-analysis` by itself and is controlled by the selected tone and API Key state from the page.
- AI card copy and states now explicitly match the expected loading, success, and failure behavior.
- The AI card is always visible on the page, even before analysis starts.
- Clicking `开始分析` now opens an AI setup modal first, where the user picks tone and can input an API Key.
- After `/analyze` finishes, the AI card auto-runs `/ai-analysis` with the selected tone and API Key.
- Switching the tone button only reruns `/ai-analysis`, and cached results are reused for the same analysis fingerprint + API Key + tone.
- The old downgrade warning panel is no longer rendered on the frontend.
- `.gitignore` now ignores `.env`-style files and `config.local.py`.
- Recommended frontend flow:
  1. Call `/analyze` first.
  2. Reuse `features` and `ctr.score` to call `/ai-analysis`.
  3. Do not resend `heatmap_base64` or image base64 payloads to the LLM.
- Runtime interaction flow:
  1. User clicks `开始分析`.
  2. Frontend uploads the image with `POST /analyze`.
  3. After `/analyze` returns, the page immediately renders CTR, radar chart, feature cards, heatmap, and similar items.
  4. The AI card then automatically sends `POST /ai-analysis` with `features + ctr_score + tone`.
  5. When the user switches the tone button, only `/ai-analysis` is requested again; the image is not re-uploaded and `/analyze` is not rerun.

# compet

电商主图智能分析项目。当前仓库由两部分组成：

- 后端：仓库根目录下的 Python + FastAPI 服务
- 前端：[`网页界面设计 (1)`](./网页界面设计%20(1)) 目录下的 React + Vite 页面

系统会对上传的商品主图做视觉特征提取、CTR 预测、注意力热力图生成、跨品类相似竞品检索，并输出优化建议与心理学诊断文本。

## 当前实现概览

- 上传单张商品主图并返回分析结果
- 提取 8 个视觉特征
  - `entropy`
  - `text_density`
  - `brightness`
  - `contrast`
  - `saturation`
  - `subject_area_ratio`
  - `edge_density`
  - `color_saturation`
- 使用仓库内置的全局 CTR 模型做预测
- 生成注意力热力图
- 在 6 个品类的联合语料中检索 Top 5 相似竞品
- 输出规则化优化建议 `advice`
- 输出心理学诊断 `psychological_report`
- 前端展示上传预览、CTR 分数、热力图、雷达图、相似竞品、优化建议和降级提示

## 当前设计约束

这些行为已经写死在当前代码里，README 也按现状说明，不再假设“未来可能支持”：

- `/analyze` 当前不接收品类参数
- CTR 模型是 6 个品类混合训练后的全局模型
- 相似图检索默认跨 6 个品类统一检索，不是只在单一品类内检索
- `TOP_K_SIMILAR = 5`
- 热力图当前实现基于显著性 + 边缘融合，不是 Grad-CAM
- `ctr.percentile` 当前通常为 `null`
- `ctr.percentile_available` 当前通常为 `false`

最后两点的原因是：仓库内置模型只返回原始回归分数，没有随服务一起提供真实百分位基线。

## 技术栈

- 后端：FastAPI、Uvicorn、NumPy、Pandas、OpenCV、Pillow、XGBoost、scikit-learn、PyTorch、OpenAI CLIP
- 前端：React 18、Vite 5、TypeScript、Tailwind CSS 4
- 可选依赖：Tesseract OCR
- 前端额外通过 CDN 加载：Chart.js、Lucide

## 目录结构

```text
compet/
├─ api.py                         # FastAPI 入口
├─ config.py                      # 全局配置、数据集注册、路径常量
├─ precompute_vectors.py          # 预计算 CLIP 向量缓存
├─ requirements.txt               # Python 依赖
├─ start_all.bat                  # Windows 一键启动前后端
├─ cache/                         # 各数据集 CLIP 向量缓存
├─ data/                          # 本地运行所需数据目录
├─ heatmap/                       # CTR 模型与 scaler
├─ modules/                       # 后端核心模块
└─ 网页界面设计 (1)/              # React + Vite 前端
```

## 数据目录与 GitHub 压缩说明

`data/` 是本项目最重要的本地运行资源。后端健康检查、相似图检索和向量缓存生成都依赖它。

### 本地运行时要求

仓库根目录下需要有解压后的 `data/` 目录，结构必须类似：

```text
data/
├─ drink/
│  ├─ 功能性饮料_数据集.xlsx
│  └─ images_standard/
├─ lamp/
│  ├─ 桌面台灯_数据集.xlsx
│  └─ images_standard/
├─ phonecase/
├─ glass/
├─ scarf/
└─ lipstick/
```

每个品类目录至少需要：

- 1 个 Excel 数据表
- 1 个 `images_standard/` 图片目录

### 推送到 GitHub 前的约定

为了避免仓库体积过大，`data/` 不建议以“解压后的完整目录”直接推送到 GitHub。

推荐约定：

1. 本地开发时保留解压后的 `data/`
2. 推送到 GitHub 前，将 `data/` 压缩为压缩包保存
3. 其他机器拉取仓库后，先把压缩包解压还原为 `data/` 目录，再启动项目

如果仓库里看到的是 `data.zip`、`data.7z` 或其他压缩文件，而不是完整的 `data/` 目录，这是预期行为。使用前必须先解压回仓库根目录，最终目录名仍然要是 `data/`。

### 当前注册的数据集

| 目录 | 品类 | Excel 文件 | 图片前缀 | 样本数 |
| --- | --- | --- | --- | ---: |
| `data/drink` | 功能性饮料 | `功能性饮料_数据集.xlsx` | `drink_` | 2115 |
| `data/lamp` | 桌面台灯 | `桌面台灯_数据集.xlsx` | `lamp_` | 2681 |
| `data/phonecase` | ins风手机壳 | `ins风手机壳_数据集.xlsx` | `phonecase_` | 565 |
| `data/glass` | 创意玻璃杯 | `创意玻璃杯_数据集.xlsx` | `glass_` | 570 |
| `data/scarf` | 印花丝巾 | `印花丝巾_数据集.xlsx` | `scarf_` | 651 |
| `data/lipstick` | 口红 | `口红_数据集.xlsx` | `lipstick_` | 501 |

当前 6 个数据集总计 `7083` 张图片。

## 缓存与模型文件

### CLIP 向量缓存

项目当前使用以下缓存文件：

- `cache/drink_clip_vectors.npy`
- `cache/lamp_clip_vectors.npy`
- `cache/phonecase_clip_vectors.npy`
- `cache/glass_clip_vectors.npy`
- `cache/scarf_clip_vectors.npy`
- `cache/lipstick_clip_vectors.npy`

这些缓存用于相似图检索。如果缓存不存在，可以用脚本重新生成。

### CTR 模型文件

仓库当前按代码读取以下文件：

- `heatmap/ctr_xgboost_model_global.pkl`
- `heatmap/ctr_feature_scaler.pkl`

它们对应的是全局混合品类模型，不是按单品类切换的模型。

## 环境要求

- Python 3.10 到 3.12，推荐 3.12
- Node.js 18+，推荐 20+
- `pnpm` 10+
- Git
- 可选：Tesseract OCR

补充说明：

- `requirements.txt` 中包含 `git+https://github.com/openai/CLIP.git`，所以安装 Python 依赖时本机必须可用 `git`
- `pytesseract` 只是 Python 封装；如果系统没有安装 Tesseract OCR，可运行但 OCR 相关能力会降级
- 前端的雷达图与图标依赖 CDN 脚本。如果网络不能访问 `jsdelivr` 或 `unpkg`，页面中的图表或图标可能无法正常显示

## 安装依赖

### 1. 安装后端依赖

在仓库根目录执行：

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 安装前端依赖

```powershell
cd "网页界面设计 (1)"
corepack enable
pnpm install
```

如果本机还没有安装 `pnpm`：

```powershell
npm install -g pnpm
```

## 启动方式

### 方式一：Windows 一键启动

```powershell
start_all.bat
```

这个脚本会：

- 自动查找前端目录
- 优先使用 `.venv\Scripts\python.exe`
- 如果没有 `.venv`，再尝试 `venv\Scripts\python.exe`
- 最后回退到系统 `python`
- 检查 `pnpm` 是否存在
- 如果 `8000` 端口已经被占用，则跳过后端启动
- 如果当前项目的 Vite 进程已经存在，则跳过前端启动

仅预览启动行为，不实际启动：

```powershell
start_all.bat --dry-run
```

### 方式二：手动启动

后端：

```powershell
.venv\Scripts\activate
python api.py
```

前端：

```powershell
cd "网页界面设计 (1)"
pnpm dev
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/health`

前端默认请求 `http://127.0.0.1:8000`。如果后端地址变化，可用环境变量 `VITE_API_BASE` 覆盖。

## 向量缓存生成

生成全部数据集缓存：

```powershell
python precompute_vectors.py --dataset all
```

只生成单个数据集缓存时，`--dataset` 传入的是“中文数据集名”，不是目录 slug。例如：

```powershell
python precompute_vectors.py --dataset 功能性饮料
python precompute_vectors.py --dataset 桌面台灯
python precompute_vectors.py --dataset ins风手机壳
python precompute_vectors.py --dataset 创意玻璃杯
python precompute_vectors.py --dataset 印花丝巾
python precompute_vectors.py --dataset 口红
```

如果图片缺失或处理失败，脚本会打印 warning，并为该样本写入零向量。

## API 概览

### `GET /health`

返回服务健康状态与资源就绪情况。

示例响应：

```json
{
  "status": "ok",
  "ready": true,
  "mode": "full",
  "model_scope": "global",
  "components": {
    "ctr_model": true,
    "ctr_scaler": true,
    "vector_cache": true,
    "dataset_excel": true,
    "dataset_images": true,
    "retrieval": true
  }
}
```

字段说明：

- `status`：接口是否可响应，当前实现固定返回 `"ok"`
- `ready`：所有关键资源是否齐全
- `mode`：`"full"` 或 `"degraded"`
- `model_scope`：当前固定为 `"global"`
- `components`：分项检查结果

### `POST /analyze`

- 请求方式：`multipart/form-data`
- 表单字段：`file`
- 输入：单张图片文件

返回字段：

- `features`
- `ctr`
- `heatmap_base64`
- `similar`
- `advice`
- `psychological_report`
- `warnings`

简化示例：

```json
{
  "features": {
    "entropy": 6.12,
    "text_density": 0.08,
    "brightness": 0.61,
    "contrast": 43.8,
    "saturation": 0.47,
    "subject_area_ratio": 0.31,
    "edge_density": 0.09,
    "color_saturation": 0.44
  },
  "ctr": {
    "score": 0.63,
    "percentile": null,
    "percentile_available": false
  },
  "heatmap_base64": "<base64 png>",
  "similar": [
    {
      "rank": 1,
      "dataset_key": "功能性饮料",
      "dataset_name": "功能性饮料",
      "img_name": "drink_0067.jpg",
      "similarity": 0.884,
      "relative_ctr": 21.77,
      "price": 36.0,
      "img_base64": "<base64 png>"
    }
  ],
  "advice": [
    {
      "priority": "高",
      "category": "视觉复杂度",
      "issue": "...",
      "suggestion": "..."
    }
  ],
  "psychological_report": {
    "lines": ["..."],
    "text": "..."
  },
  "warnings": []
}
```

补充说明：

- `dataset_key` 当前来自 `config.DATASETS` 的注册键名，因此现在也是中文品类名
- `dataset_name` 当前与 `dataset_key` 基本一致，都是展示用中文名称

### `warnings` 可能出现的值

根据当前代码，常见警告包括：

- `ctr_fallback_legacy_model`
- `ctr_fallback_mock_value`
- `heatmap_fallback_original_image`
- `retrieval_disabled`
- `advice_generation_failed`
- `psychological_report_failed`

## 前端页面当前展示内容

当前前端页面会展示：

- 上传图片预览
- CTR 预测原始分数
- 原图与热力图对比
- 8 维视觉特征雷达图与数值面板
- Top 5 相似竞品卡片
- 优化建议列表
- 心理学诊断文本
- 系统降级提示 `warnings`

## 核心模块说明

`modules/` 目录当前包含：

- `feature_extractor.py`：基础视觉特征与 CLIP 向量提取
- `reference_pipeline.py`：OCR、CLIP、热力图、心理学诊断相关逻辑
- `ctr_predictor.py`：CTR 模型加载与预测降级逻辑
- `retriever.py`：相似图检索与跨品类语料聚合
- `advisor.py`：规则化优化建议生成
- `heatmap.py`：热力图对外适配层
- `preprocessor.py`：图像预处理

## 运行链路

一次 `/analyze` 请求的大致流程：

1. 接收上传图片并写入临时文件
2. 预处理图片
3. 提取基础视觉特征
4. 通过 `reference_pipeline` 补充 OCR、CLIP 和参考特征
5. 使用全局 CTR 模型预测原始 CTR 分数
6. 生成注意力热力图
7. 在 6 个品类的联合向量语料中检索 Top 5 相似图
8. 生成优化建议与心理学诊断
9. 组装 JSON 响应

## 排障说明

### `/health` 返回 `degraded`

优先检查：

- `heatmap/ctr_xgboost_model_global.pkl` 是否存在
- `heatmap/ctr_feature_scaler.pkl` 是否存在
- `data/` 是否已经正确解压
- 6 个数据集目录、Excel、图片目录是否完整
- `cache/` 下 6 个 `.npy` 向量缓存是否存在

如果缓存缺失，执行：

```powershell
python precompute_vectors.py --dataset all
```

### `text_density` 很低或恒为 `0`

通常表示系统没有正确安装 Tesseract OCR，或者没有加入 `PATH`。服务仍可运行，但 OCR 相关特征与部分建议会受影响。

### 相似图检索不可用

相似图检索依赖：

- 所有数据集的 Excel 文件
- 所有数据集的 `images_standard/`
- 所有数据集对应的 CLIP 向量缓存

任意一项缺失，都可能导致 `/health.components.retrieval = false`，并在 `/analyze` 的 `warnings` 中看到 `retrieval_disabled`。

### 前端打开但图标或雷达图不显示

当前前端通过 CDN 加载 Chart.js 和 Lucide。请检查网络是否可访问：

- `https://cdn.jsdelivr.net`
- `https://unpkg.com`

## 后续维护建议

- 如果数据集更新，优先同步更新 `config.py` 中的样本配置和 README 表格
- 如果重新训练并替换 CTR 模型，记得同步更新模型文件路径和“是否支持 percentile”的说明
- 如果将前端的 CDN 依赖改为本地安装，也应同步更新 README 中的网络要求
