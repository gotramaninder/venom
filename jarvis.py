"""
VENOM HUD server v3.
Laptop pe:   python jarvis.py     (browser mein http://127.0.0.1:8765)
Phone pe:    .env mein VENOM_PIN (6+ akshar) aur VENOM_HOST=0.0.0.0 daal, phir Tailscale se (SETUP.md dekh).
"""
import hmac
import logging
import math
import os
import re
import secrets
import struct
import subprocess
import sys
import threading
import time
import webbrowser
import zlib
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, Response, abort, jsonify, redirect, request

import venom as V          # .env yahin load hoti hai
import notify
import studio

try:
    import psutil
except ImportError:
    psutil = None

BASE = V.BASE
PORT = int(os.getenv("VENOM_PORT", "8765"))
HOST = os.getenv("VENOM_HOST", "127.0.0.1").strip() or "127.0.0.1"
PIN = os.getenv("VENOM_PIN", "").strip()
TOKEN = secrets.token_hex(16)
UP_DIR = V.OUT_DIR / "uploads"
UP_DIR.mkdir(exist_ok=True)
SESS_F = BASE / ".sessions.json"
PUSH_F = BASE / ".push.json"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.basicConfig(filename=str(BASE / "venom.log"), level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(threadName)s %(message)s")

LOCK = threading.Lock()
ALERT_LOCK = threading.Lock()
REPLIES, ALERTS = [], []
PENDING = {}
SHUT = {"proc": None}
LAST = {"path": None, "t": 0}
SESSIONS = set(V.load_json(SESS_F, []))
FAILS = {"n": 0, "until": 0}

# ---------- venom.py ke patches ----------
def _has(t, words):
    """Pehle substring tha ('sip' description mein mil jata tha). Ab shabd ki shuruaat match hoti hai."""
    t = (t or "").lower()
    return any(re.search(r"(?<![a-z0-9])" + re.escape(w), t) for w in words)

V.has = _has
V.SYSTEM += ("\nLanguage rule: Maninder jis language mein bole (Hinglish, Hindi, Gujarati, English ya koi aur) usi mein jawab de. "
             "Default Hinglish (Roman). Jawab voice mein bola jayega: chhote saaf vakya, bina emoji, bina markdown symbols.")
V.DEV.update({"क्रोम": "chrome", "नोटपैड": "notepad", "स्पॉटिफाई": "spotify", "एक्सेल": "excel", "वर्ड": "word",
              "करो": "karo", "कर": "kar", "दो": "do", "चेक": "check", "देख": "dekh", "दिखाओ": "dikhao", "बताओ": "batao",
              "कब": "kab", "है": "hai", "कल": "kal", "नया": "naya", "काम": "kaam", "प्रोजेक्ट": "project",
              "रिमाइंडर": "reminder", "बढ़ाओ": "badhao", "आवाज़": "awaaz", "मेरे": "mere", "कार्ड": "card", "सेट": "set",
              "रील": "reel", "कैप्शन": "caption", "हैशटैग": "hashtag", "स्क्रिप्ट": "script", "आइडिया": "idea",
              "प्लान": "plan", "कंटेंट": "content", "पेंडिंग": "pending", "लिस्ट": "list", "लॉकडाउन": "lockdown",
              "रिव्यू": "review", "ऑडिट": "audit"})


def _speak(text):
    REPLIES.append({"say": text, "show": text})


def _deliver(reply, label="reply"):
    if len(reply) <= 380:
        REPLIES.append({"say": reply, "show": reply})
        return
    path = V.OUT_DIR / f"{label}_{datetime.now():%Y%m%d_%H%M%S}.txt"
    path.write_text(reply, encoding="utf-8")
    short = " ".join(re.split(r"(?<=[.!?।])\s+", V.clean_for_speech(reply))[:2])
    REPLIES.append({"say": short + " Poora jawab screen pe hai aur outputs folder mein save hai.", "show": reply})


V.speak = _speak
V.deliver = _deliver

# ---------- security ----------
FWD = ("X-Forwarded-For", "X-Forwarded-Host", "Forwarded", "Tailscale-User-Login", "CF-Connecting-IP")


def is_local():
    return (request.host in (f"127.0.0.1:{PORT}", f"localhost:{PORT}") and request.remote_addr in ("127.0.0.1", "::1")
            and not any(h in request.headers for h in FWD))


def authed():
    if is_local():
        return True
    return bool(PIN) and request.cookies.get("vsess") in SESSIONS


def auth():
    if not authed() or not hmac.compare_digest(request.headers.get("X-Venom-Token", ""), TOKEN):
        abort(403)


def _https():
    return request.is_secure or request.headers.get("X-Forwarded-Proto", "") == "https"


LOGIN_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VENOM</title><style>body{margin:0;height:100vh;background:#04050a;color:#e9eef5;font-family:system-ui;display:flex;
flex-direction:column;align-items:center;justify-content:center;gap:16px}h1{letter-spacing:.5em;font-family:Consolas,monospace}
input,button{padding:14px;font-size:16px;background:#0b0e16;color:#fff;border:1px solid #333;text-align:center}
button{cursor:pointer}p{color:#ff6b6b;min-height:20px}</style></head><body><h1>VENOM</h1>
<form method="post"><input name="pin" type="password" placeholder="PIN" autofocus autocomplete="current-password"> <button>ENTER</button></form>
<p>__MSG__</p></body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if not PIN:
        abort(404)
    msg = ""
    if request.method == "POST":
        if time.time() < FAILS["until"]:
            msg = "Zyada galat try. 5 minute baad aana."
        elif hmac.compare_digest(request.form.get("pin", "").encode(), PIN.encode()):
            FAILS["n"] = 0
            sid = secrets.token_urlsafe(24)
            SESSIONS.add(sid)
            V.save_json(SESS_F, list(SESSIONS)[-20:])
            resp = redirect("/")
            resp.set_cookie("vsess", sid, max_age=30 * 86400, httponly=True, samesite="Lax", secure=_https())
            return resp
        else:
            FAILS["n"] += 1
            msg = "Galat PIN."
            if FAILS["n"] >= 5:
                FAILS["n"], FAILS["until"] = 0, time.time() + 300
    return Response(LOGIN_HTML.replace("__MSG__", msg), mimetype="text/html")


# ---------- PWA (phone pe app jaisa install) ----------
_PNG = {}


def make_png(size):
    if size in _PNG:
        return _PNG[size]
    c, rows = size / 2, bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            if d < 0.22:
                px = (255, 255, 255)
            elif d < 0.30:
                px = (179, 136, 255)
            elif 0.52 < d < 0.58:
                px = (230, 236, 245)
            elif 0.72 < d < 0.75:
                px = (120, 130, 145)
            else:
                px = (4, 5, 10)
            rows += bytes(px)

    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF)

    _PNG[size] = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) +
                  chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))
    return _PNG[size]


@app.get("/icon.png")
def icon():
    s = request.args.get("s", "512", type=int)
    return Response(make_png(s if s in (180, 192, 512) else 512), mimetype="image/png")


@app.get("/manifest.json")
def manifest():
    return jsonify(name="VENOM", short_name="Venom", start_url="/", display="standalone", background_color="#04050a",
                   theme_color="#04050a", icons=[{"src": "/icon.png?s=192", "sizes": "192x192", "type": "image/png"},
                                                  {"src": "/icon.png?s=512", "sizes": "512x512", "type": "image/png"}])


@app.get("/sw.js")
def sw():
    return Response("self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('fetch',()=>{});",
                    mimetype="application/javascript")


# ---------- shutdown (confirm + countdown + cancel) ----------
def is_shutdown(n):
    return "shutdown" in n or "shut down" in n or (V.has(n, ["laptop", "computer"]) and V.has(n, ["band", "bandh", "bund", "off"]))


def start_shutdown():
    if V.OS == "Windows":
        subprocess.run(["shutdown", "/s", "/t", "15"])
    elif V.OS == "Darwin":
        SHUT["proc"] = subprocess.Popen(["sh", "-c", "sleep 15 && osascript -e 'tell app \"System Events\" to shut down'"])
    else:
        SHUT["proc"] = subprocess.Popen(["sh", "-c", "sleep 15 && systemctl poweroff"])
    _speak("Theek hai. 15 second mein laptop band ho raha hai. Rokna ho to bol cancel.")
    return {"countdown": 15}


def do_close(name):
    if V.OS != "Windows":
        _speak("App close abhi sirf Windows pe hai.")
        return
    subprocess.run(["taskkill", "/IM", V.APPS[name][1], "/F"], capture_output=True)
    _speak(f"{name} band kar diya.")


# ---------- studio routing ----------
def studio_route(text, n):
    """True deta hai agar studio ne handle kar liya."""
    if V.has(n, ["client", "rate", "payment", "price", "paise", "paisa", "meeting", "reminder"]):
        return False
    if LAST["path"] and time.time() - LAST["t"] < 1800 and V.has(n, ["review", "critique", "feedback", "check", "dekh", "kaisa", "kaisi"]) \
            and V.has(n, ["ye", "isko", "this", "design", "video", "edit", "thumbnail", "post"]):
        V.deliver(studio.critique_media(LAST["path"], text), "review")
        return True
    if V.has(n, ["content calendar", "content plan", "posting plan", "post schedule", "calendar bana", "calendar banao"]):
        V.deliver(studio.content_calendar(text), "calendar")
        return True
    if V.has(n, ["caption", "hashtag"]):
        V.deliver(studio.caption_pack(text), "caption")
        return True
    if V.has(n, ["audit", "growth plan", "profile check", "page check"]):
        V.deliver(studio.growth_audit(text), "audit")
        return True
    if V.has(n, ["reel", "short", "script", "video idea"]) and V.has(n, ["idea", "script", "plan", "bana", "banao", "likh", "hook"]):
        V.deliver(studio.reel_plan(text), "reel")
        return True
    if V.has(n, ["review", "critique", "feedback"]) and V.has(n, ["design", "video", "edit", "thumbnail", "reel", "post"]):
        _speak("Design ya video neeche 📎 se attach kar, main dekh ke honest review dunga.")
        return True
    return False


# ---------- routes ----------
@app.get("/")
def index():
    if not authed():
        return redirect("/login") if PIN else abort(403)
    hud_file = BASE / "static" / "jarvis.html"
    if not hud_file.is_file():
        hud_file = BASE / "jarvis.html"  # backward-compatible fallback for older folder layouts
    if not hud_file.is_file():
        app.logger.error("HUD file missing: checked %s and %s", BASE / "static" / "jarvis.html", BASE / "jarvis.html")
        abort(500, description="VENOM HUD file missing. Restore static/jarvis.html from the repository.")
    html = hud_file.read_text(encoding="utf-8").replace("__TOKEN__", TOKEN)
    return Response(html, mimetype="text/html", headers={"Cache-Control": "no-store"})


@app.post("/api/command")
def command():
    auth()
    text = ((request.get_json(silent=True) or {}).get("text") or "").strip()
    if not text:
        return jsonify(replies=[], sleep=False)
    extra, sleep = {}, False
    with LOCK:
        REPLIES.clear()
        n = V.norm(text)
        try:
            if PENDING.get("close"):
                name = PENDING.pop("close")
                if V.has(n, ["haan", "yes", "kar do", "kar de", "ok", "theek", "sure"]):
                    do_close(name)
                else:
                    _speak("Theek hai, chhod diya.")
            elif PENDING.get("shutdown"):
                PENDING.pop("shutdown")
                if V.has(n, ["haan", "yes", "kar do", "kar de", "ok", "theek", "sure"]):
                    extra = start_shutdown()
                else:
                    _speak("Theek hai, laptop chalu rahega.")
            elif is_shutdown(n):
                PENDING["shutdown"] = True
                _speak("Laptop band kar du? Pakka? Haan bol.")
            elif V.match_app(n) and V.has(n, ["close", "band", "bandh", "kill", "exit"]):
                name = V.match_app(n)
                PENDING["close"] = name
                _speak(f"{name} band kar du? Unsaved kaam ud sakta hai. Haan bol.")
            elif V.has(n, ["notification test", "whatsapp test", "test notification", "phone test"]):
                if notify.configured():
                    ok = notify.send("VENOM test: sir, phone alert chal raha hai.", bg=False)
                    _speak("Test bhej diya. Phone check kar." if ok else "Bheja par pahunchta nahi dikh raha. Key ya number check kar.")
                else:
                    _speak("Phone alert set nahi hai. SETUP.md mein WhatsApp ya ntfy wala step dekh.")
            elif studio_route(text, n):
                pass
            else:
                V.reload_data()
                sleep = V.handle(text) == "sleep"
        except Exception as e:
            _speak(f"Kuch gadbad hui: {e}")
        replies = list(REPLIES)
        REPLIES.clear()
    return jsonify(replies=replies, sleep=sleep, **extra)


@app.post("/api/upload")
def upload():
    auth()
    f = request.files.get("file")
    note = (request.form.get("note") or "").strip()
    if not f:
        abort(400)
    ext = Path(f.filename or "").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm", ".mkv", ".m4v"}:
        return jsonify(replies=[{"say": "Sirf image ya video bhej.", "show": "Sirf image (jpg/png/webp) ya video (mp4/mov) bhej."}])
    path = UP_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{secrets.token_hex(4)}{ext}"
    f.save(path)
    LAST["path"], LAST["t"] = path, time.time()
    with LOCK:
        REPLIES.clear()
        try:
            _deliver(studio.critique_media(path, note), "review")
        except Exception as e:
            _speak(f"Review mein gadbad hui: {e}")
        replies = list(REPLIES)
        REPLIES.clear()
    return jsonify(replies=replies)


@app.post("/api/shutdown/cancel")
def cancel_shutdown():
    auth()
    if V.OS == "Windows":
        subprocess.run(["shutdown", "/a"], capture_output=True)
    elif SHUT["proc"]:
        SHUT["proc"].kill()
    return jsonify(ok=True)


@app.get("/api/status")
def status():
    auth()
    clients = V.load_json(V.CLIENT_FILE, [])
    month = datetime.now().strftime("%Y-%m")
    got = sum(p["amount"] for c in clients for p in c.get("payments", []) if p["date"].startswith(month))
    pend = sum(max(V.num(c.get("price")) - V.num(c.get("paid")), 0) for c in clients)
    leads = V.load_json(BASE / "leads.json", [])
    queue = V.load_json(BASE / "queue.json", [])
    briefs = V.load_json(BASE / "briefs.json", [])
    now = datetime.now()
    meets = sorted([m for m in V.load_meetings() if datetime.strptime(m["when"], "%Y-%m-%d %H:%M") >= now], key=lambda m: m["when"])
    stats = {}
    if psutil:
        stats = {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent}
        try:
            b = psutil.sensors_battery()
            if b:
                stats.update(battery=int(b.percent), plugged=bool(b.power_plugged))
        except Exception:
            pass
    with ALERT_LOCK:
        alerts = list(ALERTS)
        ALERTS.clear()
    return jsonify(stats=stats, keys=len(V.PROVIDERS), ai_providers=V.provider_status(), received=got, pending=pend,
                   leads=sum(1 for x in leads if x.get("status") == "new"),
                   queue=sum(1 for x in queue if x.get("status") in ("pending", "approved")),
                   meeting=(f"{meets[0]['title']} — {meets[0]['when']}" if meets else ""),
                   brief=(briefs[-1]["text"][:420] if briefs else ""), alerts=alerts, portfolio=bool(V.PORTFOLIO_URL),
                   phone_alerts=notify.configured(), remote=bool(PIN))


# ---------- background: reminders, integrity, phone push ----------
def push_due_meetings():
    if not notify.configured():
        return
    pushed = set(V.load_json(PUSH_F, {}).get("meet", []))
    now, changed = datetime.now(), False
    for m in V.load_meetings():
        key = f"{m['title']}|{m['when']}"
        when = datetime.strptime(m["when"], "%Y-%m-%d %H:%M")
        if key not in pushed and when - timedelta(minutes=10) <= now <= when + timedelta(minutes=5):
            notify.send(f"Sir, yaad dila raha hu. {m['title']}, {when:%I:%M %p} pe hai.")
            pushed.add(key)
            changed = True
    if changed:
        st = V.load_json(PUSH_F, {})
        st["meet"] = sorted(pushed)[-50:]
        V.save_json(PUSH_F, st)


def morning_push():
    now = datetime.now()
    st = V.load_json(PUSH_F, {})
    day = now.strftime("%Y-%m-%d")
    if now.hour < 9 or st.get("day") == day or not notify.configured():
        return
    clients = V.load_json(V.CLIENT_FILE, [])
    pend = sum(max(V.num(c.get("price")) - V.num(c.get("paid")), 0) for c in clients)
    leads = sum(1 for x in V.load_json(BASE / "leads.json", []) if x.get("status") == "new")
    today = [m for m in V.load_meetings() if m["when"].startswith(day)]
    msg = (f"Good morning sir. Aaj {len(today)} meeting" + (": " + ", ".join(m["title"] for m in today) if today else "") +
           f". Pending payment ₹{V.inr(pend)}. Naye leads {leads}.")
    notify.send(msg, bg=False)
    st["day"] = day
    V.save_json(PUSH_F, st)


def monitor():
    while True:
        time.sleep(20)
        try:
            with LOCK:
                REPLIES.clear()
                V.check_reminders()
                rem = list(REPLIES)
                REPLIES.clear()
                V.check_integrity()
                integ = list(REPLIES)
                REPLIES.clear()
            if rem or integ:
                with ALERT_LOCK:
                    ALERTS.extend(rem + integ)
            for a in integ:
                notify.send(a["say"])
            push_due_meetings()
            morning_push()
        except Exception:
            logging.exception("VENOM background monitor cycle failed")


def open_ui():
    url = f"http://127.0.0.1:{PORT}"
    if "--app" in sys.argv and V.OS == "Windows":
        subprocess.Popen(f'start "" msedge --app={url}', shell=True)
    else:
        webbrowser.open(url)


if __name__ == "__main__":
    if not V.PROVIDERS:
        print("Koi API key nahi mili. .env mein GEMINI_API_KEY daal.")
        sys.exit(1)
    if PIN and len(PIN) < 6:
        print("VENOM_PIN kam se kam 6 akshar ka rakh. Remote access band hai.")
        PIN = ""
    if HOST != "127.0.0.1" and not PIN:
        print("VENOM_HOST bahar khola hai par VENOM_PIN nahi hai. Bina PIN ke start nahi karunga.")
        sys.exit(1)
    threading.Thread(target=monitor, daemon=True).start()
    if "--nobrowser" not in sys.argv:
        threading.Timer(1.2, open_ui).start()
    print(f"VENOM HUD chal raha hai: http://127.0.0.1:{PORT}  (host {HOST}, remote {'ON' if PIN else 'OFF'}). Band karne ke liye Ctrl+C")
    app.run(host=HOST, port=PORT, threaded=True)
