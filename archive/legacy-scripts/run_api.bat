@echo off
REM FinSecAI v2 API Server Startup Script (Windows)
REM This script runs the FastAPI backend server

echo.
echo 🚀 Starting FinSecAI v2 FastAPI Backend
echo =========================================

REM Set environment variables if not already set
if not defined ENVIRONMENT set ENVIRONMENT=development
if not defined SERVER_HOST set SERVER_HOST=0.0.0.0
if not defined SERVER_PORT set SERVER_PORT=8000
if not defined LOG_LEVEL set LOG_LEVEL=INFO

echo 📋 Configuration:
echo    Environment: %ENVIRONMENT%
echo    Host: %SERVER_HOST%
echo    Port: %SERVER_PORT%
echo    Log Level: %LOG_LEVEL%
echo.

REM Check if FastAPI is installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FastAPI not installed. Installing dependencies...
    pip install -r requirements.txt
)

echo ✅ Dependencies ready
echo.
echo 🌐 Starting API server...
echo    API Docs: http://localhost:%SERVER_PORT%/docs
echo    Redoc: http://localhost:%SERVER_PORT%/redoc
echo.

REM Start the server
python -m uvicorn api.main:app --host %SERVER_HOST% --port %SERVER_PORT% --reload --log-level %LOG_LEVEL%
