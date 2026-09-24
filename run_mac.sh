#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Создание окружения..."
    python3 -m venv venv
    ./venv/bin/pip install numpy scipy pyyaml customtkinter tkinterdnd2
fi

./venv/bin/python main_gui.py
