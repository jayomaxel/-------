# ImageIQ

电商主图智能诊断路演项目，面向 `2026 计算机设计大赛` 演示场景。

项目当前由两部分组成：

- 后端：仓库根目录下的 FastAPI 服务
- 前端：[`front/index.html`](./front/index.html) 单文件静态页面，纯 HTML + CSS + 原生 JavaScript

上传一张商品主图后，系统会完成以下流程：

1. 提取图像视觉特征
2. 预测 CTR 分数
3. 生成注意力热力图
4. 检索 Top 5 相似竞品
5. 生成规则建议
6. 调用大模型生成 AI 分析与优化建议

## 系统架构与运行机制

系统当前采用轻量化的前后端分离架构。后端以 Python 为核心，使用 FastAPI 对外提供 `/health`、`/analyze` 与 `/ai-analysis` 接口，并由 Uvicorn 承载服务运行；同时通过 CORS 中间件开放跨域访问，便于前端页面直接调用。前端并非 React/Vite/TypeScript 工程，而是位于 [`front/index.html`](./front/index.html) 的单文件静态页面，使用原生 HTML、CSS 与 JavaScript 实现七屏路演式交互，并通过 CDN 引入 `Chart.js` 完成特征雷达图绘制。为降低本地部署门槛，项目提供了 [`start_all.bat`](./start_all.bat) 一键启动脚本，可自动检查前端入口、后端入口、Python 解释器及 `8000/8080` 端口占用情况，并支持 `--dry-run` 预览启动命令。

系统底层资源主要由全局 CTR 预测模型、特征标准化器、CLIP 向量缓存以及多品类商品数据集构成。`config.py` 通过 `_build_dataset_config()` 工厂函数和 `DATASETS` 全局注册表统一管理六类数据集，分别为功能性饮料、桌面台灯、ins 风手机壳、创意玻璃杯、印花丝巾和口红，共计 `7083` 条样本。检索链路依赖各数据集的 Excel 元数据、`images_standard/` 图片目录以及 `cache/*.npy` 向量缓存，离线预计算脚本 [`precompute_vectors.py`](./precompute_vectors.py) 与在线分析主链路复用同一套 CLIP 特征提取逻辑。在计算资源适配方面，图像编码模块会在运行时根据 `torch.cuda.is_available()` 自动选择 CUDA 或 CPU，因此无论是在普通本地设备还是具备 GPU 的服务器环境下，系统都能保持一致的执行流程。

在稳定性与可用性方面，系统提供了显式的健康检查和优雅降级机制。`GET /health` 会逐项探测 CTR 模型、特征标准化器、向量缓存、数据表、图片目录与检索语料的就绪状态，并据此返回 `full` 或 `degraded` 服务模式。核心的 `POST /analyze` 链路按“图像处理、CTR 预测、热力图生成、相似检索、规则建议、心理学报告”的顺序串行执行，同时对各子模块分别进行异常隔离：当 CTR 模型不可用时回退为默认分值 `0.5`，当热力图生成失败时回退原图，检索、规则建议或心理学报告失败时则仅在 `warnings` 字段中标记异常而不阻断主请求。这样的设计保证了系统即使在部分资源缺失或局部模块异常时，也能持续输出基础诊断结果。

## 当前能力

- `GET /health`：检查模型、数据集、向量缓存是否就绪
- `POST /analyze`：
  - 上传商品主图
  - 返回视觉特征、CTR、热力图、相似竞品、规则建议、心理学报告
- `POST /ai-analysis`：
  - 接收结构化特征与 CTR 分数
  - 生成 `professional / gentle / direct / marketing` 四种语气的 AI 分析

前端当前支持：

- 7 屏全屏滚动路演页面
- 首页眼睛滚动开合动画
- 上传图预览与分析流程
- 热力图对比展示
- 五项指标展示
- Top 5 相似竞品卡片
- AI 建议页语气切换
- 前端 AI 缓存
- 浏览器本地保存 API Key 与语气配置

## 技术栈

后端：

- FastAPI
- Uvicorn
- NumPy / Pandas
- OpenCV / Pillow
- scikit-learn / XGBoost / joblib
- PyTorch / torchvision / OpenAI CLIP
- OpenAI Python SDK
- pytesseract

前端：

- 单文件静态页
- 原生 HTML / CSS / JavaScript
- `Chart.js` 通过 CDN 渲染数据雷达图

## 仓库结构

```text
compet/
├─ api.py
├─ config.py
├─ precompute_vectors.py
├─ requirements.txt
├─ start_all.bat
├─ README.md
├─ cache/                     # CLIP 向量缓存
├─ data/                      # 运行时数据目录
├─ docs/                      # 补充说明
├─ front/
│  └─ index.html              # 单文件前端
├─ heatmap/                   # CTR 模型与实验资源
├─ modules/                   # 后端核心模块
└─ scripts/                   # 辅助脚本
```

## 环境要求

- Python 3.10+
- Windows 环境下建议使用 PowerShell 或直接双击 `start_all.bat`
- 本机可用 `git`
  - 因为 `requirements.txt` 中包含 `git+https://github.com/openai/CLIP.git`
- 可选：本机安装 Tesseract OCR
  - 未安装时项目仍可运行，但 `text_density` 可能偏低或接近 `0`

前端不再依赖 Node.js、pnpm、Vite 或 React。

## 安装依赖

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 启动方式

### 方式一：一键启动

```powershell
start_all.bat
```

当前脚本会自动：

- 优先使用 `.venv\Scripts\python.exe`
- 启动 FastAPI 后端：`http://127.0.0.1:8000`
- 启动静态前端：`http://127.0.0.1:8080`
- 前端通过 `python -m http.server` 提供静态页面
- 自动在浏览器打开前端地址

如果只想预览启动命令：

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
python -m http.server 8080 --bind 127.0.0.1
```

默认地址：

- 前端：`http://127.0.0.1:8080`
- 后端：`http://127.0.0.1:8000`

## 数据准备

项目运行期读取的是：

```text
data/<slug>/
```

而不是：

```text
data/data/<slug>/
```

当前 `config.py` 注册了 6 个数据集：

- `drink` 功能性饮料
- `lamp` 桌面台灯
- `phonecase` ins 风手机壳
- `glass` 创意玻璃杯
- `scarf` 印花丝巾
- `lipstick` 口红

每个数据集目录至少应包含：

- Excel 数据表
- `images_standard/` 图片目录

例如：

```text
data/
├─ drink/
│  ├─ 功能性饮料_数据集.xlsx
│  └─ images_standard/
├─ lamp/
│  ├─ 桌面台灯_数据集.xlsx
│  └─ images_standard/
└─ ...
```

如果目录放成 `data/data/...`，`/health` 会显示检索相关组件未就绪。

## 向量缓存

相似图检索依赖 `cache/*.npy`：

- `cache/drink_clip_vectors.npy`
- `cache/lamp_clip_vectors.npy`
- `cache/phonecase_clip_vectors.npy`
- `cache/glass_clip_vectors.npy`
- `cache/scarf_clip_vectors.npy`
- `cache/lipstick_clip_vectors.npy`

如缓存缺失，可重新生成：

```powershell
python precompute_vectors.py --dataset all
```

也可以只生成单个数据集，例如：

```powershell
python precompute_vectors.py --dataset 桌面台灯
```

## 接口说明

### `GET /health`

返回服务整体就绪状态。典型返回：

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

### `POST /analyze`

请求类型：`multipart/form-data`

字段：

- `file`

典型返回字段：

```json
{
  "features": {
    "entropy": 6.18,
    "text_density": 0.08,
    "subject_area_ratio": 0.31,
    "edge_density": 0.12,
    "color_saturation": 0.48
  },
  "ctr": {
    "score": 0.73
  },
  "heatmap_base64": "...",
  "similar": [
    {
      "rank": 1,
      "dataset_key": "lamp",
      "dataset_name": "桌面台灯",
      "title": "商品名称",
      "img_name": "lamp_0001.png",
      "similarity": 0.86,
      "relative_ctr": 2.08,
      "price": 37.0,
      "img_base64": "..."
    }
  ],
  "advice": [],
  "psychological_report": {
    "lines": [],
    "text": ""
  },
  "warnings": []
}
```

说明：

- 后端当前真实返回的视觉特征是：
  - `entropy`
  - `text_density`
  - `subject_area_ratio`
  - `edge_density`
  - `color_saturation`
- 前端“五项图像特征”页面展示的是：
  - `brightness`
  - `contrast`
  - `saturation`
  - `entropy`
  - `text_density`
- 其中 `brightness / contrast / saturation` 由前端本地从上传图像补算，`entropy / text_density` 来自后端结果

### `POST /ai-analysis`

请求体示例：

```json
{
  "tone": "professional",
  "features": {
    "entropy": 6.18,
    "text_density": 0.08,
    "subject_area_ratio": 0.31,
    "edge_density": 0.12,
    "color_saturation": 0.48
  },
  "ctr_score": 0.73,
  "api_key": "optional"
}
```

支持的语气：

- `professional`
- `gentle`
- `direct`
- `marketing`

返回字段：

- `summary`
- `strengths`
- `problems`
- `suggestions`
- `success`
- `error`
- `fallback`

## 前端当前行为

- 分析前可通过右上角齿轮配置 AI API Key
- 若未配置 API Key 就点击“开始分析”，会先弹出配置弹窗
- AI 语气支持切换，切换后只会重新请求 `/ai-analysis`
- 不会重新上传图片
- 同一组 `features + ctr_score + tone + api_key` 会命中前端缓存
- 相似竞品默认展示 Top 5
- 最后一屏展示 AI 摘要、亮点、问题和 AI 延展建议

## 配置项

当前后端通过环境变量读取 AI 配置：

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `AI_MODEL_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `AI_MODEL_API_KEY` | `YOUR_API_KEY` | 服务端默认 API Key |
| `AI_MODEL_NAME` | `deepseek-chat` | 模型名 |
| `AI_MAX_TOKENS` | `1500` | 最大输出 token |
| `AI_TIMEOUT` | `30` | 请求超时秒数 |

PowerShell 示例：

```powershell
$env:AI_MODEL_API_KEY = "your-real-key"
python api.py
```

## 排障

### `/health` 一直是 `degraded`

优先检查：

- `heatmap/ctr_xgboost_model_global.pkl` 是否存在
- `heatmap/ctr_feature_scaler.pkl` 是否存在
- `data/<slug>/...` 目录是否正确
- `cache/*.npy` 是否齐全

### 相似竞品不显示

优先检查：

- 数据集 Excel 是否存在
- `images_standard/` 是否存在
- 对应向量缓存是否存在
- `/health.components.retrieval` 是否为 `true`

### AI 分析不可用

优先检查：

- `AI_MODEL_API_KEY` 是否有效
- `AI_MODEL_BASE_URL` 是否正确
- `AI_MODEL_NAME` 是否正确
- 模型服务网络是否可达

### 前端页面打开了但接口失败

确认：

- 前端地址是否为 `http://127.0.0.1:8080`
- 后端地址是否为 `http://127.0.0.1:8000`
- 浏览器控制台是否有请求超时或跨域错误

## 文档维护建议

如果后续继续改项目，请同步更新以下两处：

- [`README.md`](./README.md)
- [`requirements.txt`](./requirements.txt)

尤其是以下变化很容易让文档过期：

- 前端启动方式变化
- 接口字段变化
- 数据集目录变化
- AI 配置方式变化
- 前端是否仍然为单文件静态页
