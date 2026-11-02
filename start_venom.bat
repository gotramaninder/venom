@echo off
REM Venom ek click mein: background scout + HUD (screen wali window)
cd /d %~dp0
start "Venom Scout" /min python scout.py
start "Venom HUD" /min python jarvis.py --app
