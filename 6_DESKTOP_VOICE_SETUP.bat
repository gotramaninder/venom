@echo off
cd /d "%~dp0"
if exist "runtime\python.exe" (
 echo Browser wake-word and push-to-talk voice are included in the VENOM HUD.
 echo The optional legacy desktop microphone listener is not bundled.
 echo You can use VOICE in the HUD without installing extra packages.
 pause
 exit /b 0
)
if not exist ".venv\Scripts\python.exe" (
 echo First run 1_SETUP_VENOM.bat.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r voice_requirements.txt
if errorlevel 1 (
 echo Desktop wake-word voice packages did not install completely.
 echo Browser voice will still work in the HUD.
 pause
 exit /b 1
)
echo Optional desktop voice packages installed.
pause
