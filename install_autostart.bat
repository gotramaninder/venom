@echo off
REM Ek baar chala: har baar Windows login hote hi Venom (lock-screen mode) apne aap start hoga.
REM Laptop ko plugged-in hone par sleep hone se bhi rokta hai (screen band ho sakti hai, laptop nahi).
cd /d %~dp0
schtasks /create /tn "VenomAutoStart" /tr "\"%~dp0start_venom_lock.bat\"" /sc onlogon /f
powercfg /change standby-timeout-ac 0
echo.
echo Done. Band karna ho to:  schtasks /delete /tn "VenomAutoStart" /f
pause
