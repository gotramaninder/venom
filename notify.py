"""
VENOM notifications: tere phone pe alert bhejta hai.
 - WhatsApp (free, CallMeBot): .env mein WHATSAPP_PHONE=+91XXXXXXXXXX aur CALLMEBOT_KEY=...
 - Push (free, ntfy app, iPhone + Android): .env mein NTFY_TOPIC=koi-lamba-random-naam
Dono set hon to dono pe jayega.
"""
import os
import threading

import requests


def configured():
    return bool((os.getenv("WHATSAPP_PHONE") and os.getenv("CALLMEBOT_KEY")) or os.getenv("NTFY_TOPIC"))


def _callmebot(msg):
    phone, key = os.getenv("WHATSAPP_PHONE", "").strip(), os.getenv("CALLMEBOT_KEY", "").strip()
    if not (phone and key):
        return False
    try:
        r = requests.get("https://api.callmebot.com/whatsapp.php",
                         params={"phone": phone, "text": msg[:1000], "apikey": key}, timeout=20)
        return r.ok
    except Exception:
        return False


def _ntfy(msg):
    topic = os.getenv("NTFY_TOPIC", "").strip()
    if not topic:
        return False
    try:
        r = requests.post(f"https://ntfy.sh/{topic}", data=msg[:1000].encode("utf-8"),
                          headers={"Title": "VENOM"}, timeout=15)
        return r.ok
    except Exception:
        return False


def send(msg, bg=True):
    """Message tere khud ke number/phone pe bhejta hai. Kisi aur ko nahi."""
    def run():
        a = _callmebot(msg)
        b = _ntfy(msg)
        return a or b
    if bg:
        threading.Thread(target=run, daemon=True).start()
        return True
    return run()
