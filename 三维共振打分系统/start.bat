@echo off
chcp 65001 >nul
echo ==========================================
echo    三维共振打分系统
echo    高志强工作室专属
echo ==========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not detected. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo [1/3] Python detected

REM Check and install dependencies
echo [2/3] Checking dependencies...
set MISSING=0
pip show flask >nul 2>&1 || set MISSING=1
pip show flask-cors >nul 2>&1 || set MISSING=1
pip show requests >nul 2>&1 || set MISSING=1
pip show tushare >nul 2>&1 || set MISSING=1
pip show pandas >nul 2>&1 || set MISSING=1
pip show numpy >nul 2>&1 || set MISSING=1

if %MISSING%==1 (
    echo Installing dependencies, please wait...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [Error] Dependency installation failed.
        pause
        exit /b 1
    )
)

echo [3/3] Starting Web Application...
echo.
echo ==========================================
echo Application started. Please visit:
echo http://127.0.0.1:5000
echo ==========================================
echo.
echo Press Ctrl+C to stop the program
echo.

python app.py

pause
