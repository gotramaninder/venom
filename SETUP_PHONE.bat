@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title VENOM PHONE SETUP
if not exist .env (
  echo Pehle 1_SETUP_VENOM.bat chala.
  pause
  exit /b
)
echo.
echo ===== PHONE SETUP =====
echo.

findstr /b /c:"VENOM_PIN=" .env >nul 2>nul
if errorlevel 1 (
  set "PIN="
  set /p "PIN=Phone ke liye PIN bana, kam se kam 6 akshar, yaad rakhna: "
  if "!PIN:~5,1!"=="" (
    echo PIN 6 akshar se chhota hai. Dobara chala.
    pause
    exit /b
  )
  >> .env echo.
  >> .env echo VENOM_PIN=!PIN!
) else (
  echo PIN pehle se set hai.
)

findstr /b /c:"NTFY_TOPIC=" .env >nul 2>nul
if errorlevel 1 (
  for /f "usebackq" %%i in (`powershell -NoProfile -Command "[guid]::NewGuid().ToString('N')"`) do set "TOPIC=venom-%%i"
  >> .env echo NTFY_TOPIC=!TOPIC!
  echo.
  echo Phone pe ntfy app install kar, usme + daba aur ye topic subscribe kar:
  echo.
  echo     !TOPIC!
  echo.
) else (
  echo Phone alert topic pehle se set hai. .env mein NTFY_TOPIC dekh le.
)

echo.
echo Tailscale install kar raha hu...
if exist "%ProgramFiles%\Tailscale\tailscale.exe" (
  echo Tailscale pehle se hai.
) else (
  winget install -e --id Tailscale.Tailscale --accept-source-agreements --accept-package-agreements
)

echo.
echo ----- AB YE KARNA HAI, sirf ek baar -----
echo 1. Taskbar mein Tailscale icon se Log in kar, Google se ho jata hai.
echo 2. Jo page khul raha hai usme MagicDNS aur HTTPS Certificates ON kar.
echo 3. Apne PHONE mein bhi Tailscale app install kar aur usi account se login kar.
echo.
start "" "https://login.tailscale.com/admin/dns"
pause

echo.
echo Laptop ka HTTPS link bana raha hu...
"%ProgramFiles%\Tailscale\tailscale.exe" serve --bg 8765
echo.
echo Upar jo https wala link dikha, wahi tera phone wala link hai.
echo Venom ko band karke desktop shortcut se dobara chala, tabhi PIN kaam karega.
echo Phir phone ke browser mein wo link khol, PIN daal, TAP TO ACTIVATE.
echo.
pause
