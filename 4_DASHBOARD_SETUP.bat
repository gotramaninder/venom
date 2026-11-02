@echo off
cd /d "%~dp0"
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
echo Dashboard dependencies installed.
pause
