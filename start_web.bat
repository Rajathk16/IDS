@echo off
title DEVRAKSHAK // Next.js AI IoT Intrusion & DDoS Defense System
echo =========================================================================
echo  DEVRAKSHAK // Next.js + Python Full-Stack Defense System
echo  Dataset: Official CICIoT2023 Platform (63 Merged CSV Partitions)
echo =========================================================================
echo.

:: 1. Check if Next.js dependencies are installed
if not exist "%~dp0frontend\node_modules" (
    echo [INFO] First-time setup: Installing Next.js dependencies in frontend...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
    echo [INFO] Next.js dependencies installed!
    echo.
)

:: 2. Start Python AI Backend in background on port 8000
echo [1/3] Starting Python AI & REST API Backend on http://127.0.0.1:8000 ...
if exist "%~dp0.venv\Scripts\python.exe" (
    start "DEVRAKSHAK Python AI Engine" cmd /k ""%~dp0.venv\Scripts\python.exe" -m src.web.server --host 127.0.0.1 --port 8000"
) else (
    start "DEVRAKSHAK Python AI Engine" cmd /k "uv run python -m src.web.server --host 127.0.0.1 --port 8000"
)

:: 3. Launch default browser to Next.js app on port 3000
echo [2/3] Waiting for servers to initialize...
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:3000/"

:: 4. Start Next.js Development Server on port 3000
echo [3/3] Starting Next.js Frontend on http://localhost:3000 ...
cd /d "%~dp0frontend"
call npm run dev

pause
