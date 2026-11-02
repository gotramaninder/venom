@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run 1_SETUP_VENOM.bat first.
 pause
 exit /b 1
)
start "VENOM Scout" /min ".venv\Scripts\python.exe" scout.py
start "VENOM Server" /min ".venv\Scripts\python.exe" jarvis.py --nobrowser
start "VENOM Voice" /min ".venv\Scripts\python.exe" venom.py
