@echo off
setlocal

REM ==========================================================
REM 文件用途:
REM   一键启动 Streamlit 前端服务（app.py）。
REM 主要入口:
REM   本脚本自身（双击或命令行执行）。
REM 输入 / 输出:
REM   输入: 无（可选传递额外 streamlit 参数）。
REM   输出: 启动本地 Web 服务，默认访问 http://localhost:8501
REM ==========================================================

REM 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

REM 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] 未检测到 Python，请先安装并配置到 PATH。
  pause
  exit /b 1
)

REM 检查 app.py 是否存在
if not exist "app.py" (
  echo [ERROR] 未找到 app.py，请确认在项目根目录执行本脚本。
  pause
  exit /b 1
)

echo [INFO] 正在启动 Streamlit...
echo [INFO] 访问地址: http://localhost:8501
python -m streamlit run app.py %*

REM 仅在异常退出时暂停，便于查看报错
if errorlevel 1 (
  echo [ERROR] Streamlit 启动失败，请检查依赖是否安装完成。
  pause
  exit /b 1
)

endlocal
