@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d "%~dp0"

echo =======================================================
echo   UE to Arma Reforger Retargeter
echo =======================================================
echo.

:: Поиск Python
set "PYTHON_CMD="

:: 1. Проверяем py лаунчер
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
) else (
    :: 2. Проверяем системный python
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
    )
)

:: 3. Если не найден в PATH, проверяем стандартные папки установки Windows
if "%PYTHON_CMD%"=="" (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%ProgramFiles%\Python312\python.exe"
        "%ProgramFiles%\Python311\python.exe"
        "%ProgramFiles%\Python310\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python310\python.exe"
    ) do (
        if exist %%P (
            set "PYTHON_CMD=%%P"
            goto :found_python
        )
    )
)

:found_python
if "%PYTHON_CMD%"=="" (
    echo [ОШИБКА] Python не найден на вашем компьютере!
    echo.
    echo Пожалуйста, установите Python с официального сайта:
    echo https://www.python.org/downloads/
    echo.
    echo ВАЖНО: При установке обязательно поставьте галочку "Add Python to PATH"!
    echo.
    pause
    exit /b 1
)

echo Используется Python: %PYTHON_CMD%

if not exist venv (
    echo.
    echo [1/2] Создание виртуального окружения...
    %PYTHON_CMD% -m venv venv
    if not exist venv\Scripts\python.exe (
        echo [ОШИБКА] Не удалось создать venv.
        pause
        exit /b 1
    )
    echo [2/2] Установка необходимых библиотек (customtkinter, numpy, scipy)...
    venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
    venv\Scripts\python.exe -m pip install numpy scipy pyyaml customtkinter tkinterdnd2
)

echo.
echo Запуск программы...
venv\Scripts\python.exe main_gui.py
if %errorlevel% neq 0 (
    echo.
    echo Программа завершилась с кодом ошибки: %errorlevel%
    pause
)
