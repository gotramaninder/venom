@echo off
REM Lock screen mode: browser nahi khulta. Server + phone alerts + desktop voice ("Hey Venom") background mein chalte hain.
REM Laptop on rahe, sleep na ho, aur Windows lock ho to bhi chalta hai (unlock voice se nahi hota).
cd /d %~dp0
start "Venom Scout" /min python scout.py
start "Venom Server" /min python jarvis.py --nobrowser
start "Venom Voice" /min python venom.py
