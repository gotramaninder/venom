@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title VENOM SETUP
echo.
echo ===== VENOM SETUP =====
echo.

python --version >nul 2>nul
if errorlevel 1 (
  where winget >nul 2>nul
  if errorlevel 1 (
    echo Python nahi mila aur winget bhi nahi hai.
    echo python.org se Python download kar, install karte waqt "Add Python to PATH" tick kar, phir ye file dobara chala.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b
  )
  echo Python nahi mila. Abhi install kar raha hu, 2-3 minute lagenge...
  winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
  echo.
  echo Python install ho gaya. Ye window band kar aur SETUP_VENOM.bat dobara double click kar.
  pause
  exit /b
)

echo [1/6] Zaroori packages install ho rahe hain...
python -m pip install --upgrade pip >nul 2>nul
python -m pip install flask requests psutil
if errorlevel 1 (
  echo.
  echo Install fail hua. Internet check kar aur dobara chala.
  pause
  exit /b
)

echo.
echo [2/6] Voice packages try kar raha hu...
set "VOICE=yes"
python -m pip install SpeechRecognition pyttsx3
if errorlevel 1 set "VOICE=no"
python -m pip install pyaudio
if errorlevel 1 set "VOICE=no"
if "!VOICE!"=="no" echo Voice packages poore install nahi hue. Koi baat nahi, browser wali voice chalegi. Lock screen voice baad mein dekhenge.

echo.
echo [3/6] Video review ke liye ffmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
  where winget >nul 2>nul
  if not errorlevel 1 winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
)

echo.
echo [4/6] Settings, .env file
if exist .env (
  echo .env pehle se hai, usko chhed nahi raha.
  goto envdone
)
echo.
echo Ab Gemini key chahiye, free milti hai. Browser khul raha hai.
echo   1. Google se login kar
echo   2. Create API key daba
echo   3. Key copy kar
start "" "https://aistudio.google.com/apikey"
echo.
set "GKEY="
set /p "GKEY=Key yahan paste kar aur Enter daba: "
set "PURL="
set /p "PURL=Portfolio link paste kar, nahi hai to sirf Enter daba: "
> .env echo GEMINI_API_KEY=!GKEY!
>> .env echo PORTFOLIO_URL=!PURL!
if "!GKEY!"=="" echo WARNING: key khali rahi. .env ko Notepad se kholke GEMINI_API_KEY ke aage key bhar de.
:envdone

echo.
echo [5/6] Desktop pe Venom shortcut bana raha hu...
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Venom.lnk');$s.TargetPath='%~dp0start_venom.bat';$s.WorkingDirectory='%~dp0';$s.Save()"

echo.
echo [6/6] Laptop on hote hi Venom apne aap chale aur Hey Venom sune?
echo      Ye lock screen mode hai, isko voice packages chahiye.
set "AS="
set /p "AS=y ya n likh aur Enter daba: "
if /i "!AS!"=="y" (
  if "!VOICE!"=="no" (
    echo Voice packages install nahi hue the, isliye abhi skip kar raha hu.
  ) else (
    call install_autostart.bat
  )
)

echo.
echo ===== SETUP KHATAM =====
echo Venom abhi chalu ho raha hai. Edge khulega.
echo TAP TO ACTIVATE daba aur mic Allow kar.
echo Aage se desktop ka Venom shortcut daba.
echo Phone pe chalane ke liye SETUP_PHONE.bat chala.
echo.
call start_venom.bat
pause
