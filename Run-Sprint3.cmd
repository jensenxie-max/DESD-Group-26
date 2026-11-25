@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
python -u tools\run_sprint3_manual.py
echo.
pause
