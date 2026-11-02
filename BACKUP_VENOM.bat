@echo off
setlocal
cd /d "%~dp0"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%i"
set "DEST=VENOM_BACKUP_%STAMP%.zip"
powershell -NoProfile -Command "$items=@(); if(Test-Path '.env'){$items+= '.env'}; if(Test-Path 'data'){$items+= 'data'}; if(Test-Path 'outputs'){$items+= 'outputs'}; if($items.Count -eq 0){Write-Host 'Nothing to back up yet.'; exit 2}; Compress-Archive -Path $items -DestinationPath '%DEST%' -Force -ErrorAction Stop"
if errorlevel 1 (
 echo Backup failed. Check available disk space and try again.
 pause
 exit /b 1
)
echo Backup created: %DEST%
pause
