@echo off
title mybotzhuli - API Service
echo 🚀 Starting FastAPI Service natively on Windows...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Error: Virtual environment not initialized. Please run setup_win.ps1 first!
    pause
    exit /b %errorlevel%
)
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
pause
