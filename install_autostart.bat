@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE="
if exist "runtime\python.exe" set "PYTHON_EXE=runtime\python.exe"
if not defined PYTHON_EXE if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE (
 echo Run 1_SETUP_VENOM.bat first.
 pause
 exit /b 1
)
echo This enables optional VENOM background startup at every Windows login.
echo The HUD opens when you manually open http://127.0.0.1:8765.
set "OK="
set /p "OK=Type YES to continue: "
if /i not "%OK%"=="YES" exit /b 0
schtasks /create /tn "VenomAutoStart" /tr "\"%~dp0start_venom_lock.bat\"" /sc onlogon /f
if errorlevel 1 (
 echo Could not create the scheduled task.
 pause
 exit /b 1
)
echo.
echo To disable: schtasks /delete /tn "VenomAutoStart" /f
pause
