@echo off
title WEB - E:\Robots\Indexing\main.py

cd /d "C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice"

"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe" "C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\main.py"

if %errorlevel% equ 0 (
    exit
) else (
    pause
)
