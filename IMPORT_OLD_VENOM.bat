@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo First run 1_SETUP_VENOM.bat.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" import_old_venom.py
pause
