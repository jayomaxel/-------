# requirements 配置指南

这份指南面向当前仓库的后端环境，说明 `requirements.txt` 应该怎么理解、怎么安装、以及后续怎么维护。

## 1. 先明确这个项目的依赖边界

当前仓库分为两部分：

- 后端依赖：根目录 [`requirements.txt`](../requirements.txt)
- 前端依赖：[`front/package.json`](../front/package.json)

也就是说，`requirements.txt` 只负责 Python 后端，不负责 React 前端。

## 2. 当前项目的 requirements 里都有什么

当前 [`requirements.txt`](../requirements.txt) 可以按职责分成 4 组：

### Web 服务

```txt
fastapi>=0.115.0
uvicorn>=0.30.0
python-multipart>=0.0.9
openai>=1.0.0
```

- `fastapi`：后端 API 框架
- `uvicorn`：ASGI 服务运行器
- `python-multipart`：支持文件上传
- `openai`：兼容 OpenAI 接口的模型调用客户端

### 数据与图像处理

```txt
numpy>=1.26.0
pandas>=2.0.0
openpyxl>=3.1.0
opencv-python>=4.9.0
Pillow>=10.0.0
pytesseract>=0.3.10
```

- `numpy` / `pandas` / `openpyxl`：读取和处理 Excel 与结构化数据
- `opencv-python` / `Pillow`：图像处理与热力图相关逻辑
- `pytesseract`：OCR 文本密度提取

### 机器学习

```txt
scikit-learn>=1.4.0
xgboost>=2.0.0
joblib>=1.3.0
```

- `scikit-learn`：特征缩放等基础能力
- `xgboost`：CTR 预测模型
- `joblib`：模型与对象加载

### 向量模型

```txt
torch>=2.0.0
torchvision>=0.15.0
git+https://github.com/openai/CLIP.git
```

- `torch` / `torchvision`：深度学习运行时
- `CLIP`：相似图检索使用的视觉语义向量模型

## 3. 推荐安装方式

推荐使用独立虚拟环境，不要直接装到系统 Python。

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 4. 当前项目的配置建议

### 建议 1：Python 版本优先使用 3.10 或 3.11

当前依赖组合里包含 `torch`、`xgboost`、`opencv-python`，这些包在 Python 3.10/3.11 上通常更稳。

推荐：

- 开发环境：Python 3.10
- 如果本机已有成熟的 3.11 环境，也可以继续使用

不建议默认上太新的小版本后再逐个排兼容问题。

### 建议 2：保留当前 `>=` 策略用于开发，部署时单独锁版本

当前 `requirements.txt` 使用的是下限约束，例如：

```txt
fastapi>=0.115.0
numpy>=1.26.0
torch>=2.0.0
```

这种写法适合：

- 本地开发
- 演示项目
- 需要尽快安装跑通

如果要做稳定部署，建议额外生成一个锁定文件，例如：

```powershell
pip freeze > requirements-lock.txt
```

然后部署机器优先安装：

```powershell
pip install -r requirements-lock.txt
```

这样能降低“昨天能跑、今天装出来不一样”的风险。

### 建议 3：把开发工具和运行依赖分开

如果后续需要补测试、格式化、静态检查，建议不要直接塞进当前 `requirements.txt`，而是拆成：

```txt
requirements.txt
requirements-dev.txt
```

其中：

- `requirements.txt`：只放运行时依赖
- `requirements-dev.txt`：放 `pytest`、`ruff`、`black` 等开发工具

例如：

```txt
# requirements-dev.txt
-r requirements.txt
pytest
ruff
black
```

## 5. 这个项目最容易踩的 4 个点

### 1. `CLIP` 依赖需要 Git

当前文件里有：

```txt
git+https://github.com/openai/CLIP.git
```

这意味着安装时本机必须满足：

- 已安装 Git
- 命令行可执行 `git`
- 网络能访问 GitHub

如果这里失败，通常会看到类似 “`git` not found” 或拉取仓库失败的报错。

### 2. `pytesseract` 不是 Tesseract 本体

`pip install pytesseract` 只会安装 Python 封装，不会自动安装系统 OCR 引擎。

如果系统没有安装 Tesseract：

- 项目大概率还能运行
- 但 `text_density` 可能长期为 `0.0`

Windows 安装后，还要确保 `tesseract.exe` 在系统 PATH 中，或者在代码里显式指定路径。

### 3. PyTorch 在部分机器上可能需要单独安装

如果 `pip install -r requirements.txt` 卡在 `torch`，或者下载到不合适的轮子，可以改成先按 PyTorch 官方方式安装，再装剩余依赖。

一个常见做法是：

```powershell
pip install torch torchvision
pip install -r requirements.txt
```

如果已经单独装过 `torch` / `torchvision`，再次执行 `requirements.txt` 时通常会直接复用已安装版本。

### 4. 服务器环境可能更适合 `opencv-python-headless`

当前项目使用的是：

```txt
opencv-python>=4.9.0
```

如果后续部署到纯服务端环境，遇到 GUI 相关依赖冲突，可以考虑改成：

```txt
opencv-python-headless>=4.9.0
```

注意不要同时安装 `opencv-python` 和 `opencv-python-headless`。

## 6. 建议保留的 requirements 模板

如果你想继续沿用当前结构，可以把根目录 `requirements.txt` 维持成下面这种分组写法，后续更容易维护：

```txt
# Web
fastapi>=0.115.0
uvicorn>=0.30.0
python-multipart>=0.0.9
openai>=1.0.0

# Data / Image
numpy>=1.26.0
pandas>=2.0.0
openpyxl>=3.1.0
opencv-python>=4.9.0
Pillow>=10.0.0
pytesseract>=0.3.10

# ML
scikit-learn>=1.4.0
xgboost>=2.0.0
joblib>=1.3.0

# Vision model
torch>=2.0.0
torchvision>=0.15.0
git+https://github.com/openai/CLIP.git
```

这份模板的优点是：

- 新人一眼能看懂依赖用途
- 后续排查安装问题更快
- 便于未来拆分 `requirements-dev.txt`

## 7. 配完以后怎么验证

安装完成后，建议至少做 3 步检查。

### 检查 1：确认关键包已装好

```powershell
pip show fastapi torch torchvision xgboost
```

### 检查 2：确认关键 import 正常

```powershell
python -c "import fastapi, torch, torchvision, clip, cv2, PIL; print('ok')"
```

如果输出 `ok`，说明核心 Python 依赖基本可用。

### 检查 3：启动服务并看健康状态

```powershell
python api.py
```

然后访问：

```txt
http://127.0.0.1:8000/health
```

如果依赖安装没问题，但 `/health` 仍显示 `degraded`，通常就不是 `requirements` 本身的问题，而是：

- 数据目录没整理好
- 向量缓存缺失
- 模型文件缺失

## 8. 后续维护建议

建议按下面这个顺序维护依赖：

1. 新增功能时，先确认依赖是不是运行时必需
2. 运行时必需依赖才加入 `requirements.txt`
3. 开发工具放进 `requirements-dev.txt`
4. 每次升级大包后重新跑一次 `python api.py` 和 `/health`
5. 准备发版时导出一份锁版本文件

## 9. 一句话结论

对当前仓库来说，`requirements.txt` 最稳妥的做法是：

- 保持它只负责后端运行依赖
- 本地开发继续使用当前 `>=` 下限策略
- 部署时额外生成锁版本文件
- 特别注意 `CLIP` 需要 Git、`pytesseract` 需要系统级 Tesseract
