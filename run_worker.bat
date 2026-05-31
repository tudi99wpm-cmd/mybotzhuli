@echo off
title mybotzhuli - Worker Service
echo 🤖 Starting AI Agent Worker natively on Windows...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Error: Virtual environment not initialized. Please run setup_win.ps1 first!
    pause
    exit /b %errorlevel%
)
python -m apps.worker.main
pause
