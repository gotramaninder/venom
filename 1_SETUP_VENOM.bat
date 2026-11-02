@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title VENOM - ONE TIME SETUP
echo.
echo ==========================================
echo       VENOM - ONE TIME INSTALLATION
echo ==========================================
echo.

set "PYTHON_EXE="
if exist "runtime\python.exe" (
  set "PYTHON_EXE=runtime\python.exe"
  echo [1/4] Bundled Python runtime detected. No separate Python install needed.
) else (
  where py >nul 2>nul
  if not errorlevel 1 (
    set "PY=py -3"
  ) else (
    where python >nul 2>nul
    if errorlevel 1 (
      echo Python 3 is not installed and this package has no bundled runtime.
      echo Opening official Python download page.
      start "" "https://www.python.org/downloads/"
      pause
      exit /b 1
    )
    set "PY=python"
  )
  if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating isolated VENOM environment...
    !PY! -m venv .venv
    if errorlevel 1 goto failed
  )
  set "PYTHON_EXE=.venv\Scripts\python.exe"
  echo [2/4] Installing core packages...
  "!PYTHON_EXE!" -m pip install --upgrade pip
  if errorlevel 1 goto failed
  "!PYTHON_EXE!" -m pip install -r requirements.txt
  if errorlevel 1 goto failed
)

echo [3/4] Creating clean data folders...
if not exist "data" mkdir "data"
if not exist "logs" mkdir "logs"
if not exist "outputs" mkdir "outputs"
if not exist "outputs\uploads" mkdir "outputs\uploads"

echo [4/4] Secure API setup...
"!PYTHON_EXE!" api_setup.py
if errorlevel 1 (
  echo.
  echo API setup was skipped or incomplete.
  echo You can run 3_API_SETUP.bat later.
)

echo.
echo ==========================================
echo SETUP COMPLETE
echo Next: double-click 2_START_VENOM.bat
echo Do not move individual project files.
echo ==========================================
pause
exit /b 0

:failed
echo.
echo SETUP FAILED. Check the error above, then run 1_SETUP_VENOM.bat again.
pause
exit /b 1
