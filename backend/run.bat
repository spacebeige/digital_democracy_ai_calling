@echo off
REM Quick Start Script for Ticketing System (Windows)

echo.
echo 🚀 Starting Ticketing State Machine Backend...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+.
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip.
    pause
    exit /b 1
)

echo 📦 Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ✅ Dependencies installed successfully!
echo.
echo 🎯 Starting FastAPI server...
echo.
echo 📍 API Documentation: http://localhost:8000/docs
echo 📍 Alternative Docs: http://localhost:8000/redoc
echo.

REM Start uvicorn server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
