@echo off
setlocal
cd /d "%~dp0"
title VENOM - ONE TIME SETUP
echo.
echo ==========================================
echo       VENOM - ONE TIME INSTALLATION
echo ==========================================
echo.

where py >nul 2>nul
if not errorlevel 1 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3 is not installed.
    echo Opening official Python download page.
    start "" "https://www.python.org/downloads/"
    echo Install Python and tick "Add Python to PATH", then run this file again.
    pause
    exit /b 1
  )
  set "PY=python"
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating isolated VENOM environment...
  %PY% -m venv .venv
  if errorlevel 1 goto failed
)

echo [2/4] Installing core packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo [3/4] Creating clean data folders...
if not exist "data" mkdir "data"
if not exist "logs" mkdir "logs"
if not exist "outputs" mkdir "outputs"
if not exist "outputs\uploads" mkdir "outputs\uploads"

echo [4/4] Secure API setup...
".venv\Scripts\python.exe" api_setup.py
if errorlevel 1 (
  echo.
  echo API setup was skipped or incomplete.
  echo You can run 3_API_SETUP.bat later.
)

echo.
echo ==========================================
echo SETUP COMPLETE
echo Next: double-click 2_START_VENOM.bat
echo Do not move individual Python files.
echo ==========================================
pause
exit /b 0

:failed
echo.
echo SETUP FAILED. Check internet connection and run 1_SETUP_VENOM.bat again.
pause
exit /b 1
