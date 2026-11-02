@echo off
setlocal
cd /d "%~dp0"
title VENOM - BACKGROUND START
set "PYTHON_EXE="
if exist "runtime\python.exe" set "PYTHON_EXE=runtime\python.exe"
if not defined PYTHON_EXE if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE exit /b 1
start "VENOM Scout" /min "%PYTHON_EXE%" scout.py
start "VENOM Server" /min "%PYTHON_EXE%" jarvis.py --nobrowser
