@echo off
cd /d "%~dp0"
if exist "runtime\python.exe" (
 echo The new VENOM Command Center already includes the main dashboard.
 echo The legacy Streamlit dashboard is optional and is not needed for daily use.
 echo Start VENOM with 2_START_VENOM.bat.
 pause
 exit /b 0
)
if not exist ".venv\Scripts\python.exe" (
 echo First run 1_SETUP_VENOM.bat.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r dashboard_requirements.txt
if errorlevel 1 (
 echo Dashboard setup failed. Check internet and retry.
 pause
 exit /b 1
)
echo Legacy dashboard dependencies installed.
pause
