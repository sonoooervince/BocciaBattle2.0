@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
    goto :check
)

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo Python non trovato nel PATH.
    echo Installa Python e riapri il terminale.
    echo.
    pause
    exit /b 1
)

python main.py

:check
if errorlevel 1 (
    echo.
    echo Avvio non riuscito.
    echo Se manca pip:
    echo   python -m ensurepip --upgrade
    echo.
    echo Poi installa le dipendenze:
    echo   python -m pip install -r requirements.txt
    echo.
    pause
)
