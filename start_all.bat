@echo off
setlocal
chcp 65001 >nul

if /i "%~1"=="--dry-run" set "DRY_RUN=1"

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "FRONTEND_DIR="

for /d %%D in ("%ROOT%\*") do (
  if exist "%%~fD\package.json" (
    if exist "%%~fD\src\main.tsx" (
      set "FRONTEND_DIR=%%~fD"
    )
  )
)

if not exist "%ROOT%\api.py" (
  echo [ERROR] api.py was not found in "%ROOT%".
  exit /b 1
)

if not defined FRONTEND_DIR (
  echo [ERROR] Frontend directory was not found under "%ROOT%".
  exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
  echo [ERROR] Frontend package.json was not found in "%FRONTEND_DIR%".
  exit /b 1
)

if exist "%ROOT%\.venv\Scripts\python.exe" (
  set "PYTHON_EXE=%ROOT%\.venv\Scripts\python.exe"
) else if exist "%ROOT%\venv\Scripts\python.exe" (
  set "PYTHON_EXE=%ROOT%\venv\Scripts\python.exe"
) else (
  set "PYTHON_EXE=python"
  where python >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python or create a local virtual environment first.
    exit /b 1
  )
)

where pnpm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] pnpm was not found. Install it first with: npm install -g pnpm
  exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo [WARN] "%FRONTEND_DIR%\node_modules" was not found.
  echo [WARN] Run "pnpm install" in the frontend directory before starting the UI.
)

echo [INFO] Root: "%ROOT%"
echo [INFO] Python: "%PYTHON_EXE%"
echo [INFO] Frontend: "%FRONTEND_DIR%"
echo.

powershell -NoProfile -Command "$p = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 8000 }; if ($p) { exit 0 } else { exit 1 }"
if errorlevel 1 (
  echo [INFO] Starting backend on http://127.0.0.1:8000 ...
  if defined DRY_RUN (
    echo [DRY RUN] start "Compet Backend" cmd /k chcp 65001 ^>nul ^&^& cd /d "%ROOT%" ^&^& set "PYTHONUTF8=1" ^&^& "%PYTHON_EXE%" api.py
  ) else (
    start "Compet Backend" cmd /k chcp 65001 ^>nul ^&^& cd /d "%ROOT%" ^&^& set "PYTHONUTF8=1" ^&^& "%PYTHON_EXE%" api.py
  )
) else (
  echo [INFO] Backend is already listening on port 8000. Skipping backend startup.
)

set "FRONTEND_DIR_PS=%FRONTEND_DIR%"
powershell -NoProfile -Command "$frontend = $env:FRONTEND_DIR_PS; $p = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -like '*vite*' -and $_.CommandLine -like ('*' + $frontend + '*') }; if ($p) { exit 0 } else { exit 1 }"
if errorlevel 1 (
  echo [INFO] Starting frontend with pnpm dev ...
  if defined DRY_RUN (
    echo [DRY RUN] start "Compet Frontend" cmd /k chcp 65001 ^>nul ^&^& cd /d "%FRONTEND_DIR%" ^&^& pnpm dev
  ) else (
    start "Compet Frontend" cmd /k chcp 65001 ^>nul ^&^& cd /d "%FRONTEND_DIR%" ^&^& pnpm dev
  )
) else (
  echo [INFO] Frontend Vite process is already running for this project. Skipping frontend startup.
)

echo.
if defined DRY_RUN (
  echo [DONE] Dry run complete.
) else (
  echo [DONE] Startup commands sent. Check the new terminal windows for logs.
)

exit /b 0
