@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE="
if exist "runtime\python.exe" set "PYTHON_EXE=runtime\python.exe"
if not defined PYTHON_EXE if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE (
 echo First run 1_SETUP_VENOM.bat.
 pause
 exit /b 1
)
"%PYTHON_EXE%" import_old_venom.py
pause
