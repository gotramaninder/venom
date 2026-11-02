# VENOM v3 setup

## 1. Files rakhne ka tareeka
Purane folder mein ye files overwrite kar (venom.py, scout.py, dashboard.py waise hi rehne de):
- `jarvis.py`, `notify.py`, `studio.py`, `start_venom.bat`, `start_venom_lock.bat`, `install_autostart.bat`, `requirements.txt`
- `jarvis.html` ko `static` folder ke andar daal (purani file replace kar)
- `env.example` dekh ke apni `.env` mein naye lines add kar

```
venom/
  venom.py  jarvis.py  scout.py  dashboard.py  notify.py  studio.py
  start_venom.bat  start_venom_lock.bat  install_autostart.bat
  .env
  static/jarvis.html
```

## 2. Laptop pe
1. `pip install flask requests psutil`
2. Video review ke liye ffmpeg chahiye: Windows pe `winget install ffmpeg`
3. `python jarvis.py` ya `start_venom.bat` dabake chala. Chrome/Edge mein TAP TO ACTIVATE, mic allow.
4. Pehle test: `security check`, `7 din ka content plan bana`, `reel idea bana`, aur 📎 se koi design ya video bhej.

## 3. Lock screen / laptop on hote hi "Hey Venom"
1. `pip install SpeechRecognition pyttsx3 pyaudio` (pyaudio fail ho to `pip install pipwin` phir `pipwin install pyaudio`)
2. `install_autostart.bat` ek baar chala. Ab har login pe Venom background mein start hoga (browser nahi khulega).
3. Laptop on rahe aur sleep na ho. Lid band karne pe sleep na ho: Control Panel, Power Options, "Lid close = Do nothing".

Sach: lock screen pe Venom sun bhi lega aur apps bhi chalu kar dega, par Windows ko voice se unlock nahi kar sakta (aur karna bhi nahi chahiye, warna koi bhi tere laptop me ghus jaata). Apps lock ke peeche khulenge, unlock karte hi dikhenge.

## 4. Phone pe (iPhone + Android, dono)
Tera data laptop pe hai, isliye private raste se jaa. Public internet pe khula mat chhodna.

1. Laptop aur phone dono pe **Tailscale** install kar (free), same account se login.
2. `.env` mein daal: `VENOM_PIN=koi6+akshar` (VENOM_HOST mat daal, zaroorat nahi). Ya bas SETUP_PHONE.bat chala
3. Laptop pe Tailscale ke naam se HTTPS chalu kar (mic ke liye HTTPS zaroori hai):
   `tailscale serve --bg 8765`
   Ye tujhe `https://laptop-naam.tailnet-naam.ts.net` jaisa link dega.
4. Phone ke browser mein wo link khol, PIN daal, TAP TO ACTIVATE.
5. App jaisa banane ke liye: iPhone Safari, Share, "Add to Home Screen". Android Chrome, menu, "Install app".

Phone pe kya chalta hai: chat, voice jawab, business ledger, studio, design/video review, laptop ka shutdown/lock/app open (laptop on ho tab).

- **Android (Chrome):** orb pe tap karke bol, ya VOICE ON karke "Hey Venom" (screen on aur page khula ho tab).
- **iPhone:** Apple background mic nahi chalne deta. Orb pe tap karke bol ya type kar. Home Screen app mein voice input kabhi kabhi nahi chalta, to Safari tab mein khol ya keyboard ka mic use kar.

## 5. Phone pe WhatsApp / push alerts
Meeting se 10 minute pehle, subah 9 baje ka brief (pending payment, leads), aur security alert tere phone pe aayenge.

**WhatsApp (free, CallMeBot):** callmebot.com/blog/free-api-whatsapp-messages pe jaake steps follow kar (ek baar message bhejne par tujhe API key milti hai). Phir `.env`:
```
WHATSAPP_PHONE=+91XXXXXXXXXX
CALLMEBOT_KEY=jo_key_mili
```
**Push (zyada reliable, free):** ntfy app install kar (iPhone/Android), ek lamba random topic naam subscribe kar, `.env` mein `NTFY_TOPIC=wahi_naam`.

Test: HUD mein bol ya type kar `notification test`.

## 6. Social media, design, video editing
- `7 din ka content plan bana`, `reel idea aur script bana: salon ke liye`, `caption aur hashtags bana`, `audit: mera instagram ...`
- 📎 se design/thumbnail/reel bhej: Venom honest review dega (score, kamzoriyan, top 5 fixes). Video ke 6 frames dekhta hai, audio nahi sunta.
- Review ke baad bol "isko aur dekh" ya "design kaisa laga" to wahi file dobara dekhega (30 min tak).

## 7. Languages
Upar dropdown se language chun. Jawab usi language mein aayega aur bola bhi jayega (voice device pe installed honi chahiye; Windows Settings, Time & Language, Speech se add kar). Laptop ke commands (app kholna, shutdown, payment) Hinglish, English aur Hindi mein pakke chalte hain. Gujarati ya doosri language mein chat aur studio chalta hai.

## Jo abhi nahi hai
- Instagram/YouTube pe khud post ya analytics padhna (Meta/YouTube API approval chahiye).
- WhatsApp pe Venom ko message bhejke command dena (do-tarfa). Iske liye Twilio ya Meta Cloud API lagegi, agla step.
- Video ko khud edit karna (cut/caption). Abhi sirf review aur plan.

## Safety
`.env`, `.sessions.json`, `clients.json`, `leads.json` kisi ko mat bhej, GitHub pe mat daal.
