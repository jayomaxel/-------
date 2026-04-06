# compet

电商主图智能分析演示项目。上传一张商品主图后，系统会先执行本地视觉特征提取、CTR 预测、注意力热力图生成和跨品类相似竞品检索，再基于同一组结构化特征调用大模型生成认知心理学风格的 AI 诊断。

当前仓库由两部分组成：

- 后端：仓库根目录下的 FastAPI 服务
- 前端：[`front/`](./front) 目录下的 React + Vite 单页演示页面

## 当前能力

- 上传单张商品主图并调用 `POST /analyze`
- 返回 5 个当前真实输出的视觉特征：
  - `entropy`
  - `text_density`
  - `subject_area_ratio`
  - `edge_density`
  - `color_saturation`
- 使用全局混合品类 XGBoost 模型预测 CTR 原始分
- 生成基于显著性 + 边缘融合的注意力热力图
- 在 6 个数据集的联合语料中检索 Top 5 相似竞品
- 返回规则建议 `advice` 和规则心理学报告 `psychological_report`
- 调用 `POST /ai-analysis` 生成四种语气的 AI 智能分析

## 运行流程

1. 前端上传图片并弹出 AI 设置弹窗。
2. 用户选择 AI 语气，可选填写临时 API Key。
3. 前端调用 `POST /analyze` 上传图片。
4. 页面展示 CTR 分数、热力图、雷达图、5 个视觉特征和相似竞品卡片。
5. 前端复用 `/analyze` 返回的特征和 `ctr.score`，自动调用 `POST /ai-analysis`。
6. 切换 AI 语气时，只会重新请求 `/ai-analysis`，不会重新上传图片。

## 技术栈

- 后端：FastAPI、Uvicorn、NumPy、Pandas、OpenCV、Pillow、XGBoost、scikit-learn、PyTorch、OpenAI CLIP
- 前端：React 18、Vite 5、TypeScript、Tailwind CSS 4
- 可选能力：Tesseract OCR
- 外部 CDN：Chart.js、Lucide

## 仓库结构

```text
compet/
├─ api.py                         # FastAPI 入口，暴露 /health /analyze /ai-analysis
├─ config.py                      # 全局配置、数据集注册、AI 配置
├─ precompute_vectors.py          # 预计算各数据集 CLIP 向量缓存
├─ requirements.txt               # Python 依赖
├─ start_all.bat                  # Windows 一键启动脚本
├─ cache/                         # CLIP 向量缓存
├─ data/                          # 运行时数据目录
├─ docs/                          # 补充文档
├─ front/                         # React + Vite 前端
├─ heatmap/                       # CTR 模型、scaler 和实验资源
└─ modules/                       # 后端核心模块
```

补充文档：

- [`docs/ai_prompt_acceptance.md`](./docs/ai_prompt_acceptance.md)：AI 提示词与心理学框架验收记录

## 数据准备

### 代码期望的数据目录

后端代码当前读取的是 `data/<slug>/...`，不是 `data/data/<slug>/...`。最终目录应为：

```text
data/
├─ drink/
├─ glass/
├─ lamp/
├─ lipstick/
├─ phonecase/
└─ scarf/
```

每个品类目录至少需要：

- 1 个 Excel 数据表
- 1 个 `images_standard/` 图片目录

### 当前仓库状态说明

当前工作区里的数据已经被解压到了 `data/data/*`。但 `config.py` 实际读取的是：

- `data/drink`
- `data/glass`
- `data/lamp`
- `data/lipstick`
- `data/phonecase`
- `data/scarf`

如果保持双层 `data/data` 结构不变，`/health` 会显示：

- `dataset_excel = false`
- `dataset_images = false`
- `retrieval = false`

也就是说，运行前需要把 6 个品类目录上移一级。

可手动整理，也可以在 PowerShell 中执行：

```powershell
Move-Item .\data\data\drink,.\data\data\glass,.\data\data\lamp,.\data\data\lipstick,.\data\data\phonecase,.\data\data\scarf .\data\
```

整理完成后，确保以下路径存在：

```text
data/drink/images_standard
data/glass/images_standard
data/lamp/images_standard
data/lipstick/images_standard
data/phonecase/images_standard
data/scarf/images_standard
```

`data/数据收集` 当前不在运行时主链路中使用。

### 数据集注册信息

`config.py` 当前注册了 6 个数据集，总计 7083 张图片：

| slug | 品类 | Excel 文件 | 样本数 |
| --- | --- | --- | ---: |
| `drink` | 功能性饮料 | `功能性饮料_数据集.xlsx` | 2115 |
| `lamp` | 桌面台灯 | `桌面台灯_数据集.xlsx` | 2681 |
| `phonecase` | ins风手机壳 | `ins风手机壳_数据集.xlsx` | 565 |
| `glass` | 创意玻璃杯 | `创意玻璃杯_数据集.xlsx` | 570 |
| `scarf` | 印花丝巾 | `印花丝巾_数据集.xlsx` | 651 |
| `lipstick` | 口红 | `口红_数据集.xlsx` | 501 |

如果你当前只有仓库根目录的 `data.zip`，请先解压，再确认不要产生双层 `data/data` 嵌套。

## 环境要求

- Python 3.10+
- Node.js 18+
- `pnpm` 10+
- Git
- 可选：Tesseract OCR

说明：

- `requirements.txt` 里包含 `git+https://github.com/openai/CLIP.git`，因此安装 Python 依赖时本机必须能使用 `git`
- `pytesseract` 只是 Python 封装；如果系统未安装 Tesseract，可运行，但 `text_density` 可能长期为 `0.0`
- 图标和雷达图依赖 CDN，如果无法访问 `jsdelivr` 或 `unpkg`，前端仍可打开，但图表或图标可能缺失

## 安装依赖

### 1. 安装后端依赖

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 安装前端依赖

```powershell
cd front
corepack enable
pnpm install
```

如果本机没有 `pnpm`：

```powershell
npm install -g pnpm
```

## 启动项目

### 方式一：Windows 一键启动

当前仓库只有 `start_all.bat`，没有独立的 `start.bat` 包装脚本。

```powershell
start_all.bat
```

脚本会自动：

- 查找前端目录
- 优先使用 `.venv\Scripts\python.exe`
- 回退到 `venv\Scripts\python.exe` 或系统 `python`
- 检查 `pnpm` 是否可用
- 如果 `8000` 端口已被监听，则跳过后端启动
- 如果当前项目的 Vite 进程已存在，则跳过前端启动

仅预览脚本行为：

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
cd front
pnpm dev
```

默认地址：

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:5173`

后端和前端都监听 `0.0.0.0`，局域网内可访问。

## 环境变量与配置

### 后端 AI 配置

`config.py` 当前直接通过 `os.getenv()` 读取环境变量，不会自动加载 `.env` 文件。

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `AI_MODEL_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `AI_MODEL_API_KEY` | `YOUR_API_KEY` | 服务端默认 API Key |
| `AI_MODEL_NAME` | `deepseek-chat` | 模型名 |
| `AI_MAX_TOKENS` | `1500` | 最大输出 token |
| `AI_TIMEOUT` | `30` | 请求超时秒数 |

PowerShell 示例：

```powershell
$env:AI_MODEL_BASE_URL = "https://api.deepseek.com"
$env:AI_MODEL_API_KEY = "your-real-key"
$env:AI_MODEL_NAME = "deepseek-chat"
python api.py
```

如果你是直接双击 `start_all.bat`，请优先使用系统环境变量，或直接修改 `config.py` 默认值。

### 前端配置

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `VITE_API_BASE` | `http://127.0.0.1:8000` | 前端请求的后端地址 |

如果后端不在本机 `8000` 端口，需要在启动前设置 `VITE_API_BASE`。

## 向量缓存

相似图检索依赖以下缓存文件：

- `cache/drink_clip_vectors.npy`
- `cache/lamp_clip_vectors.npy`
- `cache/phonecase_clip_vectors.npy`
- `cache/glass_clip_vectors.npy`
- `cache/scarf_clip_vectors.npy`
- `cache/lipstick_clip_vectors.npy`

如果缓存缺失，可重新生成：

```powershell
python precompute_vectors.py --dataset all
```

也可以只生成单个数据集，例如：

```powershell
python precompute_vectors.py --dataset 桌面台灯
```

`--dataset` 当前支持 `all` 或 `config.py` 中注册的中文数据集名称。

## API 说明

### `GET /health`

用于检查服务是否已完整就绪。典型返回结构：

```json
{
  "status": "ok",
  "ready": false,
  "mode": "degraded",
  "model_scope": "global",
  "components": {
    "ctr_model": true,
    "ctr_scaler": true,
    "vector_cache": true,
    "dataset_excel": false,
    "dataset_images": false,
    "retrieval": false
  }
}
```

字段含义：

- `ready`: 所有关键组件是否齐备
- `mode`: `full` 或 `degraded`
- `model_scope`: 当前固定为 `global`
- `components`: 分项可用性

### `POST /analyze`

请求类型：`multipart/form-data`

字段：

- `file`: 上传图片

示例：

```powershell
curl -X POST http://127.0.0.1:8000/analyze `
  -F "file=@D:\path\to\image.jpg"
```

返回字段：

- `features`
  - `entropy`
  - `text_density`
  - `subject_area_ratio`
  - `edge_density`
  - `color_saturation`
- `ctr`
  - `score`
  - `percentile`
  - `percentile_available`
- `heatmap_base64`
- `similar[]`
  - `rank`
  - `dataset_key`
  - `dataset_name`
  - `img_name`
  - `similarity`
  - `relative_ctr`
  - `price`
  - `img_base64`
- `advice[]`
- `psychological_report`
- `warnings[]`

说明：

- 前端当前真实渲染的是 `features`、`ctr`、`heatmap_base64`、`similar` 和 AI 卡片
- `advice` 与 `psychological_report` 仍由后端返回，但当前页面没有单独展示
- `warnings` 可能出现：
  - `ctr_fallback_mock_value`
  - `heatmap_fallback_original_image`
  - `retrieval_disabled`
  - `advice_generation_failed`
  - `psychological_report_failed`

### `POST /ai-analysis`

请求体：

```json
{
  "tone": "professional",
  "features": {
    "entropy": 6.12,
    "text_density": 0.08,
    "subject_area_ratio": 0.31,
    "edge_density": 0.12,
    "color_saturation": 0.48
  },
  "ctr_score": 0.73,
  "api_key": "optional-temporary-key"
}
```

支持的 `tone`：

- `professional`
- `gentle`
- `direct`
- `marketing`

返回字段：

- `tone`
- `summary`
- `strengths[]`
- `problems[]`
- `suggestions[]`
- `success`
- `error`

说明：

- `api_key` 为可选；如果传入，会优先于服务端默认 `AI_MODEL_API_KEY`
- 当前前端不会把图片 base64、热力图 base64 再次发送给大模型，只会发送 `/analyze` 产出的特征和 `ctr.score`
- 如果 API Key 未配置或无效，会返回友好的错误信息，而不是直接暴露原始供应商报错

## 前端当前行为

- 点击“开始分析”会先打开 AI 设置弹窗
- 用户选择的 AI 语气和 API Key 会保存在浏览器本地存储中
- AI 卡片始终可见；未分析前显示占位提示
- `/analyze` 成功后，AI 卡片会自动触发 `/ai-analysis`
- 相同的 `features + ctrScore + tone + apiKey` 组合会命中前端缓存，避免重复请求
- 如果前端启动快于后端，首次 `/analyze` 失败后会先轮询 `/health`，等待就绪后自动重试一次

## 当前限制

- `/analyze` 当前只返回 5 个同源视觉特征，不返回 `brightness`、`contrast`、`saturation`
- CTR 模型是 6 个品类混合训练后的全局模型，不区分单独类目
- 相似图检索默认跨 6 个数据集联合检索，不做单类目过滤
- `TOP_K_SIMILAR = 5`
- 热力图实现是显著性 + 边缘融合，不是 Grad-CAM
- `ctr.percentile` 当前通常为 `null`，`ctr.percentile_available` 通常为 `false`
- 如果系统未安装 Tesseract OCR，`text_density` 可能始终偏低或为 `0.0`

## 排障

### `/health` 一直是 `degraded`

优先检查：

- `heatmap/ctr_xgboost_model_global.pkl` 和 `heatmap/ctr_feature_scaler.pkl` 是否存在
- 数据目录是否已经整理成 `data/<slug>`，而不是 `data/data/<slug>`
- `cache/*.npy` 是否齐全

### 相似图检索不可用

相似图检索依赖三类文件同时存在：

- Excel 数据表
- `images_standard/` 图片目录
- CLIP 向量缓存

任意一项缺失都可能导致：

- `/health.components.retrieval = false`
- `/analyze.warnings` 中出现 `retrieval_disabled`

### AI 分析不可用

优先检查：

- `AI_MODEL_API_KEY` 是否有效
- `AI_MODEL_BASE_URL` 是否指向兼容的模型服务
- `AI_MODEL_NAME` 是否正确
- 网络是否允许访问对应模型服务

### 前端图标或雷达图不显示

请检查是否能访问：

- `https://cdn.jsdelivr.net`
- `https://unpkg.com`

## 维护建议

- 更新数据集后，同步更新 `config.py` 和本 README 中的数据表
- 更换 CTR 模型或 scaler 后，同步检查 `model_scope`、模型路径和 percentile 说明
- 如果未来把 CDN 依赖改成本地 npm 依赖，也应同步更新 README 的网络要求
