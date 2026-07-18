@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
if not exist "venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found in "venv".
    echo Please run setup first or ensure python is installed in venv.
    pause
    exit /b 1
)
echo Launching Snake Game...
venv\Scripts\python.exe src\main.py
