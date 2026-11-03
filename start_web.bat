LK'I;[
    @n>:>echo off
title DEVRAKSHAK // AI IoT Intrusion & DDoS Defense System (Web Dashboard)
echo =========================================================================
echo  DEVRAKSHAK // AI IoT Intrusion & DDoS Defense System
echo  Dataset: Official CICIoT2023 Platform (63 Merged CSV Partitions)
echo =========================================================================
echo.
echo  [1] Starting Local Web Server at http://localhost:8000 ...
echo  [2] Opening your default web browser automatically...
echo.

:: Automatically open default browser after 1 second delay
start "" cmd /c "timeout /t 1 /nobreak >nul & start http://localhost:8000/"

:: Start python server
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0src\web_server.py" --host 127.0.0.1 --port 8000
) else (
    uv run python src/web_server.py --host 127.0.0.1 --port 8000
)

pause

