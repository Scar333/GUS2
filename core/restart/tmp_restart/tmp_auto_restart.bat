@echo off
title TMP Auto Restart

cd /d "C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\tmp_restart"

"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe" "C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\tmp_restart\tmp_auto_restart.py"

if %errorlevel% equ 0 (
    exit
) else (
    pause
)
