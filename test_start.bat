@echo off
title Solonar

cd /d "C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice"

"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe" "C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\test_main.py"

if %errorlevel% equ 0 (
    exit
) else (
    pause
)
