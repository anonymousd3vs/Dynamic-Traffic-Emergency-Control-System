@echo off
REM Traffic Signal Dashboard Backend Startup Script (Windows)

echo.
echo ========================================
echo Traffic Signal Dashboard Backend
echo ========================================
echo.

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo WARNING: Virtual environment not found
)

echo.
echo Starting Flask API server...
echo API will be available at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python dashboard/backend/app.py

pause
