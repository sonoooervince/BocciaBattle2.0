@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    py main.py
)

if errorlevel 1 (
    echo.
    echo Avvio non riuscito. Se manca Pygame esegui:
    echo   py -m pip install -r requirements.txt
    echo.
    pause
)
