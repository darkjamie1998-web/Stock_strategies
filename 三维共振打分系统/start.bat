@echo off
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
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies, please wait...
    pip install -r requirements.txt
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
