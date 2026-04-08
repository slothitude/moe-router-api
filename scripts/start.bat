@echo off
REM MoE Router API Startup Script for Windows

echo Starting MoE Router API...

REM Set Python path
set PYTHONPATH=%PYTHONPATH%;%~dp0..

REM Change to project directory
cd /d "%~dp0.." || exit /b 1

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist ".installed" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo. > .installed
)

REM Check if Ollama is running
echo Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Warning: Ollama does not appear to be running.
    echo Please start Ollama first.
    echo Continuing anyway...
)

REM Start the server
echo.
echo =========================================
echo MoE Router API starting on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo =========================================
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
