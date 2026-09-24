@echo off
cd /d "%~dp0"

echo Starting UE to Arma Reforger Retargeter...

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv 2>nul || py -m venv venv
    if not exist venv\Scripts\python.exe (
        echo [ERROR] Python not found or failed to create venv.
        echo Please install Python and make sure 'Add Python to PATH' was checked.
        pause
        exit /b 1
    )
    echo Installing required libraries...
    venv\Scripts\python.exe -m pip install numpy scipy pyyaml customtkinter tkinterdnd2
)

echo Launching main GUI...
venv\Scripts\python.exe main_gui.py
if errorlevel 1 (
    echo.
    echo Application closed with error.
    pause
)
