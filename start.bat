@echo off
REM AI Grievance System - Quick Start for Windows
REM Run this file to set up and start the application

echo.
echo ==========================================
echo AI Grievance System - Quick Start
echo ==========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo Visit: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Check PostgreSQL
echo Checking PostgreSQL...
where psql >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL not found in PATH
    echo Please start PostgreSQL manually:
    echo   1. Start PostgreSQL service
    echo   2. Run: psql -U postgres -f database_setup.sql
) else (
    echo [OK] PostgreSQL found
    echo Setting up database...
    psql -U postgres -f database_setup.sql >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Database setup may have issues
        echo Make sure PostgreSQL is running and password is correct
    ) else (
        echo [OK] Database setup complete
    )
)
echo.

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements_hackathon.txt >nul 2>&1
echo [OK] Dependencies installed
echo.

REM Start server
echo Starting FastAPI server...
echo.
echo ==========================================
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ==========================================
echo.
echo Open these URLs in your browser:
echo   * User Page: file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/user.html
echo   * Officer Dashboard: file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/officer.html
echo   * Compliance Dashboard: file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/compliance.html
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

python main.py
pause
