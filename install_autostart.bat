@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run 1_SETUP_VENOM.bat first.
 pause
 exit /b 1
)
echo This enables optional background startup at every Windows login.
echo It also disables AC sleep. Continue only if you want this.
set "OK="
set /p "OK=Type YES to continue: "
if /i not "%OK%"=="YES" exit /b 0
schtasks /create /tn "VenomAutoStart" /tr "\"%~dp0start_venom_lock.bat\"" /sc onlogon /f
echo.
echo To disable: schtasks /delete /tn "VenomAutoStart" /f
pause
