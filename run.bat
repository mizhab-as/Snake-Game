@echo off
setlocal
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

:: Check for virtual environment, offer to create it if missing
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Setting up now...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Python not found. Please install Python 3.11+ from https://python.org
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo Setup complete!
) else (
    call venv\Scripts\activate.bat
)

echo Starting Snake Game...
python src\main.py
endlocal
