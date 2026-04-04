# compet

这是一个电商主图分析项目，当前仓库由两部分组成：

- 后端：根目录下的 Python + FastAPI 服务
- 前端：`网页界面设计 (1)` 目录下的 React + Vite 页面

后端会对上传图片做特征提取、CTR 预测、热力图生成、相似图检索和优化建议输出；前端负责把结果展示出来。

## 目录结构

```text
compet/
├─ api.py                      # 后端启动入口
├─ config.py                   # 路径、模型和数据集配置
├─ modules/                    # 后端核心模块
├─ precompute_vectors.py       # 预计算 CLIP 向量缓存
├─ cache/                      # 已生成的向量缓存
├─ heatmap/                    # 当前仓库自带的全局 CTR 模型和 scaler
├─ start_all.bat               # 一键启动前后端
├─ requirements.txt            # Python 依赖
└─ 网页界面设计 (1)/            # 前端项目
```

## 环境要求

- Python 3.10 - 3.12，推荐 3.12
- Node.js 18+，推荐 20+
- `pnpm` 10+
- Git
- Tesseract OCR

说明：

- `requirements.txt` 里包含了 `git+https://github.com/openai/CLIP.git`，所以机器上需要能用 `git`
- `pytesseract` 只是 Python 封装，真正 OCR 还需要系统里安装 `Tesseract OCR` 并加入 PATH

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

在前端目录执行：

```powershell
cd "网页界面设计 (1)"
corepack enable
pnpm install
```

如果本机还没装 `pnpm`，也可以先执行：

```powershell
npm install -g pnpm
```

## 启动方式

### 方式一：一键启动

在仓库根目录执行：

```powershell
start_all.bat
```

这个脚本会：

- 自动寻找前端目录
- 启动后端 `api.py`
- 启动前端 `pnpm dev`

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

前端默认请求 `http://127.0.0.1:8000`。如果后端地址变了，可以通过环境变量 `VITE_API_BASE` 覆盖。

## 常用命令

重新生成向量缓存：

```powershell
python precompute_vectors.py --dataset all
```

只启动后端做接口调试：

```powershell
python api.py
```

只启动前端开发页面：

```powershell
cd "网页界面设计 (1)"
pnpm dev
```

## API 简述

- `GET /health`
  - 查看服务是否启动，以及模型、缓存、数据目录是否就绪
- `POST /analyze`
  - 表单上传字段名为 `file`
  - 返回特征、CTR 预测、热力图、相似图和建议

## 当前仓库交接时要注意

这份仓库当前不是“完整训练数据全量版”，有几点需要提前告诉接手的人：

- 仓库里有 `cache/*.npy` 和 `heatmap/` 下的全局模型文件，所以后端可以启动
- `config.py` 里引用了 `data/` 目录，但当前仓库快照里没有 `data/` 目录
- `config.py` 里还保留了 `models/` 下的旧版模型路径，但当前仓库里也没有 `models/` 目录，需要的模型在文件夹'/heatmap' 下

这意味着：

- `/health` 很可能显示 `degraded`
- 相似图检索依赖的数据表和图片目录不完整时会不可用
- 如果缺少数据源，`precompute_vectors.py` 也无法重新生成缓存
- 如果机器上没有装好 Tesseract，OCR 相关特征和热力图会降级，但接口仍然能返回结果

## 已安装/需要安装的依赖说明

### Python 依赖

根目录 `requirements.txt` 已整理为当前代码实际需要的依赖：

- `fastapi`
- `uvicorn`
- `python-multipart`
- `numpy`
- `pandas`
- `openpyxl`
- `opencv-python`
- `Pillow`
- `pytesseract`
- `scikit-learn`
- `xgboost`
- `joblib`
- `torch`
- `torchvision`
- `CLIP`（通过 GitHub 源安装）

### 前端依赖

前端依赖由 `网页界面设计 (1)/package.json` 管理，安装命令是：

```powershell
cd "网页界面设计 (1)"
pnpm install
```

核心依赖包括：

- `react`
- `react-dom`
- `vite`
- `typescript`
- `tailwindcss`
- `@vitejs/plugin-react`
- `@tailwindcss/vite`

## 补充说明

- 热力图逻辑目前是基于遮挡敏感性和 OCR 融合，不是 Grad-CAM
- CPU 下单张图热力图生成可能比较慢，几十秒是正常现象
- 如果只是改前端样式或接口结构，通常不需要重新训练模型
