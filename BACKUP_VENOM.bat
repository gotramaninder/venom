@echo off
setlocal
cd /d "%~dp0"
if not exist "data" mkdir data
if not exist "outputs" mkdir outputs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%i"
set "DEST=VENOM_BACKUP_%STAMP%.zip"
powershell -NoProfile -Command "Compress-Archive -Path '.env','data','outputs' -DestinationPath '%DEST%' -Force -ErrorAction Stop"
if errorlevel 1 (
 echo Backup failed. Make sure .env, data and outputs folders are available.
 pause
 exit /b 1
)
echo Backup created: %DEST%
pause
