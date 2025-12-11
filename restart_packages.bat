@echo off
title RESTART

cd /d "C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice"

"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe" "C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\restart_dispatcher.py"

if %errorlevel% equ 0 (
    exit
) else (
    pause
)
