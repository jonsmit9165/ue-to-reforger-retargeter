@echo off
chcp 65001 > nul
echo =======================================================
echo   UE to Arma Reforger Animation Retargeter
echo =======================================================
echo.

if not exist venv (
    echo Создание виртуального окружения...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install numpy scipy pyyaml customtkinter tkinterdnd2
) else (
    call venv\Scripts\activate.bat
)

python main_gui.py
pause
