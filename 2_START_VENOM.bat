@echo off
setlocal
cd /d "%~dp0"
title VENOM - START
set "PYTHON_EXE="
if exist "runtime\python.exe" set "PYTHON_EXE=runtime\python.exe"
if not defined PYTHON_EXE if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE (
  echo VENOM is not installed yet. Run 1_SETUP_VENOM.bat first.
  pause
  exit /b 1
)
if not exist ".env" (
  echo API keys are not configured. Run 3_API_SETUP.bat first.
  pause
  exit /b 1
)
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "outputs\uploads" mkdir outputs\uploads

echo Starting VENOM Scout and HUD...
start "VENOM Scout" /min "%PYTHON_EXE%" scout.py
timeout /t 2 /nobreak >nul
start "VENOM HUD" /min "%PYTHON_EXE%" jarvis.py --app
echo VENOM is starting. Your browser should open shortly.
