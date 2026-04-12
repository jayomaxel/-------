@echo off
setlocal
chcp 65001 >nul

if /i "%~1"=="--dry-run" set "DRY_RUN=1"

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "FRONTEND_DIR=%ROOT%\front"
set "FRONTEND_FILE=%FRONTEND_DIR%\index.html"
set "FRONTEND_PORT=8080"
set "FRONTEND_URL=http://127.0.0.1:%FRONTEND_PORT%/"

if not exist "%ROOT%\api.py" (
  echo [ERROR] api.py was not found in "%ROOT%".
  exit /b 1
)

if not exist "%FRONTEND_FILE%" (
  echo [ERROR] Frontend entry file was not found in "%FRONTEND_FILE%".
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

echo [INFO] Root: "%ROOT%"
echo [INFO] Python: "%PYTHON_EXE%"
echo [INFO] Frontend: "%FRONTEND_FILE%"
echo [INFO] Frontend URL: %FRONTEND_URL%
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

powershell -NoProfile -Command "$p = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq %FRONTEND_PORT% }; if ($p) { exit 0 } else { exit 1 }"
if errorlevel 1 (
  echo [INFO] Starting static frontend on %FRONTEND_URL% ...
  if defined DRY_RUN (
    echo [DRY RUN] start "Compet Frontend" cmd /k chcp 65001 ^>nul ^&^& cd /d "%FRONTEND_DIR%" ^&^& set "PYTHONUTF8=1" ^&^& "%PYTHON_EXE%" -m http.server %FRONTEND_PORT% --bind 127.0.0.1
  ) else (
    start "Compet Frontend" cmd /k chcp 65001 ^>nul ^&^& cd /d "%FRONTEND_DIR%" ^&^& set "PYTHONUTF8=1" ^&^& "%PYTHON_EXE%" -m http.server %FRONTEND_PORT% --bind 127.0.0.1
  )
) else (
  echo [INFO] Frontend is already listening on port %FRONTEND_PORT%. Skipping frontend startup.
)

if defined DRY_RUN (
  echo [DRY RUN] start "" "%FRONTEND_URL%"
) else (
  start "" "%FRONTEND_URL%"
)

echo.
if defined DRY_RUN (
  echo [DONE] Dry run complete.
) else (
  echo [DONE] Startup commands sent. Check the new terminal windows for logs.
)

exit /b 0
