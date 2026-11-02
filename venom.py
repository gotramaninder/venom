"""
VENOM v2 - Maninder ka personal Jarvis.
Run:  python venom.py          (voice mode)
      python venom.py --text   (type karke test, mic ke bina)
"""
import os, sys, re, json, time, hashlib, subprocess, platform, webbrowser, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

import requests
try:
    import speech_recognition as sr
except ImportError:
    sr = None
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

BASE = Path(__file__).parent
TEXT_MODE = "--text" in sys.argv
OS = platform.system()

# ================= CONFIG =================
env_file = BASE / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

def collect_keys(prefix):
    # Exact env names only: GEMINI_API_KEY, GEMINI_API_KEY_2, etc.
    names = [name for name, value in os.environ.items()
             if (name == prefix or re.fullmatch(re.escape(prefix) + r"_\d+", name))
             and value.strip() and "yahan" not in value.lower()]
    names.sort(key=lambda name: (0, 0) if name == prefix else (1, int(name.rsplit("_", 1)[1])))
    return [os.environ[name].strip() for name in names]

# Free-first automatic provider chain. Duplicate keys in one project do not multiply quota.
PROVIDERS = ([( "gemini", k) for k in collect_keys("GEMINI_API_KEY")] +
             [("mistral", k) for k in collect_keys("MISTRAL_API_KEY")] +
             [("openrouter", k) for k in collect_keys("OPENROUTER_API_KEY")] +
             [("groq", k) for k in collect_keys("GROQ_API_KEY")] +
             [("openai", k) for k in collect_keys("OPENAI_API_KEY")] +
             [("claude", k) for k in collect_keys("ANTHROPIC_API_KEY")])
G_MODEL = os.getenv("VENOM_GEMINI_MODEL", "gemini-3.8-flash")
G_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
GROQ_MODEL = os.getenv("VENOM_GROQ_MODEL", "openai/gpt-oss-120b")
OPENROUTER_MODEL = os.getenv("VENOM_OPENROUTER_MODEL", "openrouter/free")
MISTRAL_MODEL = os.getenv("VENOM_MISTRAL_MODEL", "mistral-small-latest")
CLAUDE_MODEL = os.getenv("VENOM_CLAUDE_MODEL", "claude-sonnet-5-5")

# Runtime-only health state; secrets are never exposed through status().
_PROVIDER_HEALTH = {}
_PROVIDER_COOLDOWN = {}

def _provider_key_id(provider, key):
    return f"{provider}:{hashlib.sha256(key.encode('utf-8')).hexdigest()[:12]}"

def provider_status():
    names = []
    for name, _key in PROVIDERS:
        if name not in names:
            names.append(name)
    now = time.time()
    result = []
    for name in names:
        keys = [key for provider, key in PROVIDERS if provider == name]
        cooling = [_PROVIDER_COOLDOWN.get(_provider_key_id(name, key), 0) for key in keys]
        available = any(until <= now for until in cooling)
        health = _PROVIDER_HEALTH.get(name, "ready")
        status = "cooldown" if not available else (health if health in ("online", "degraded") else "ready")
        retry_in = min((int(until - now) for until in cooling if until > now), default=0)
        result.append({"provider": name, "configured": True, "status": status,
                       "retry_in": max(0, retry_in)})
    return result

PORTFOLIO_URL = os.getenv("PORTFOLIO_URL", "").strip()
SIGNATURE = os.getenv("VENOM_SIGNATURE", "Maninder").strip() or "Maninder"
if PORTFOLIO_URL:
    SIGNATURE += f"\nPortfolio: {PORTFOLIO_URL}"
if os.getenv("VENOM_INSTAGRAM", "").strip():
    SIGNATURE += f"\nInstagram: {os.getenv('VENOM_INSTAGRAM').strip()}"
if os.getenv("VENOM_PUBLIC_WHATSAPP", "").strip():
    SIGNATURE += f"\nWhatsApp: {os.getenv('VENOM_PUBLIC_WHATSAPP').strip()}"

# Keep source code at the project root, and keep all changing user data separate.
DATA_DIR = BASE / "data"
LOG_DIR = BASE / "logs"
OUT_DIR = BASE / "outputs"
for folder in (DATA_DIR, LOG_DIR, OUT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

# One-time, safe migration from older VENOM layouts. Never overwrite existing data.
def migrate_legacy_data():
    data_files = ("history.json", "meetings.json", "clients.json", "rates.json",
                  "apps.json", "notes.txt", ".sessions.json", ".push.json", "leads.json", "queue.json",
                  "briefs.json", "youtube_plan.json", "scout_config.json")
    log_files = ("venom.log", "scout.log")
    for name in data_files:
        old, new = BASE / name, DATA_DIR / name
        if old.exists() and not new.exists():
            try:
                old.replace(new)
            except OSError:
                pass
    for name in log_files:
        old, new = BASE / name, LOG_DIR / name
        if old.exists() and not new.exists():
            try:
                old.replace(new)
            except OSError:
                pass

migrate_legacy_data()
HISTORY_FILE = DATA_DIR / "history.json"
MEET_FILE = DATA_DIR / "meetings.json"
CLIENT_FILE = DATA_DIR / "clients.json"
RATE_FILE = DATA_DIR / "rates.json"
APPS_FILE = DATA_DIR / "apps.json"
NOTES_FILE = DATA_DIR / "notes.txt"
INTEG_FILE = DATA_DIR / ".integrity.json"
SEC_FILE = DATA_DIR / ".security_baseline.json"

WAKE = ["venom", "venum", "wenom", "vinom"]

SYSTEM = """Tu VENOM hai: Maninder ka personal AI partner, Venom symbiote ke andaaz mein. Dark, loyal, thoda sarcastic, \
kabhi kabhi "hum" bolta hai. Hamesha Hinglish (Roman script), chhote seedhe jawab. Maninder ko "sir" bol sakta hai jab \
briefing de raha ho.

Maninder: Ahmedabad, B.Com student (GLS University), UrbaNest Clothing ka founder, freelance graphic designer aur video \
editor, social media strategist, apna YouTube channel bhi hai. Freelance clients: Mesmereyes (salon), Taj Beauty (UK).
Sach proof points (outreach mein SIRF yahi use kar, kuch aur number mat bana): IMS Ahmedabad Instagram +2,800 followers, \
9M views with ads (2.5M organic); IMS Jaipur +250 followers in 25 din, 2.5M views with ads; IMS Bopal +500 followers, \
3M views (2 mahine handle).

Tera kaam: social media, design, YouTube (viral ideas, scripts), free tools (pehle free option), client dhundhna, \
outreach drafts, pricing, negotiation, client project briefing, meetings, trends, aur laptop help.

Rules:
- Normal sawal ka jawab 2-3 vakya. Script/plan/email jaisa lamba kaam poora likh.
- Fake facts, fake numbers, fake clients/contacts kabhi nahi. Pata nahi ya verify nahi hua to saaf bol.
- Tareef nahi, honest raay de, chahe Maninder ko pasand na aaye.
- Paisa/investment: koi guaranteed ya "pakka hit" claim nahi. Sirf verified facts, risk, aur final decision Maninder ka.
- Email/message tu bhejta nahi, sirf draft; bhejna Maninder karega.
Abhi ka samay: {now}"""

# ================= VOICE =================
DEV = {"क्लाइंट": "client", "पेमेंट": "payment", "सिक्योरिटी": "security", "स्कैन": "scan", "ट्रेंड": "trend",
       "ट्रेंडिंग": "trending", "न्यूज़": "news", "न्यूज": "news", "ईमेल": "email", "मेल": "mail",
       "व्हाट्सएप": "whatsapp", "व्हाट्सऐप": "whatsapp", "प्राइस": "price", "रेट": "rate", "लीड": "lead",
       "मीटिंग": "meeting", "यूट्यूब": "youtube", "इंस्टाग्राम": "instagram", "कैनवा": "canva", "जीमेल": "gmail",
       "लैपटॉप": "laptop", "कंप्यूटर": "computer", "बंद": "band", "बन्द": "band", "खोलो": "kholo", "खोल": "khol",
       "नोट": "note", "ड्राफ्ट": "draft", "बनाओ": "banao", "लिख": "likh", "कैलेंडर": "calendar",
       "ड्राइव": "drive", "स्टूडियो": "studio", "वेनम": "venom", "वेनोम": "venom", "ऑफ": "off", "सो": "so",
       "जा": "ja", "जाओ": "jao", "हाँ": "haan", "हां": "haan", "हा": "haan", "ठीक": "theek", "रुक": "ruk",
       "रद्द": "cancel", "कैंसिल": "cancel", "वायरस": "virus", "लॉक": "lock", "वॉल्यूम": "volume",
       "म्यूट": "mute", "इन्वेस्ट": "invest", "स्टॉक": "stock", "नेगोशिएट": "negotiate", "पैसे": "paise",
       "पैसा": "paisa", "बाकी": "baaki", "मिला": "mila", "कितना": "kitna", "ढूंढो": "dhundo", "खोजो": "dhundo"}

def norm(t):
    words = t.lower().split()
    return " ".join(DEV.get(w.strip(".,?!।"), w) for w in words)

def has(t, words):
    return any(w in t for w in words)

def clean_for_speech(t):
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[*#_`>|]", "", t)
    return re.sub(r"\s+", " ", t).strip()

def speak(text):
    print(f"\nVENOM: {text}\n")
    if TEXT_MODE or pyttsx3 is None:
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.say(clean_for_speech(text))
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("(voice error)", e)

recognizer = sr.Recognizer() if sr else None
if recognizer:
    recognizer.pause_threshold = 0.9

def listen(awake):
    if TEXT_MODE:
        return input("Tu: ").strip()
    if sr is None:
        return ""
    try:
        with sr.Microphone() as source:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=15 if awake else 5)
        return recognizer.recognize_google(audio, language="hi-IN" if awake else "en-IN")
    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return ""
    except sr.RequestError:
        print("(internet ya speech service issue)")
        time.sleep(2)
        return ""

def confirm(question):
    speak(question)
    return has(norm(listen(True)), ["haan", "yes", "kar do", "kar de", "ok", "theek", "sure"])

# ================= AI (multi-key, auto fallback) =================
history = []
if HISTORY_FILE.exists():
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        history = []

def _call_gemini_model(G_MODEL, key, system, contents, search):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{G_MODEL}:generateContent"
    body = {"system_instruction": {"parts": [{"text": system}]}, "contents": contents}
    if search:
        body["tools"] = [{"google_search": {}}]
    r = requests.post(url, params={"key": key}, json=body, timeout=90)
    if r.status_code != 200 and search:
        body.pop("tools")
        search = False
        r = requests.post(url, params={"key": key}, json=body, timeout=90)
    if r.status_code != 200:
        raise RuntimeError(f"gemini {r.status_code}")
    cand = r.json()["candidates"][0]
    text = "".join(p.get("text", "") for p in cand["content"]["parts"]).strip()
    if search:
        seen, srcs = set(), []
        for ch in cand.get("groundingMetadata", {}).get("groundingChunks", []):
            w = ch.get("web", {})
            if w.get("uri") and w["uri"] not in seen:
                seen.add(w["uri"])
                srcs.append(f"- {w.get('title', 'source')}: {w['uri']}")
        if srcs:
            text += "\n\nSources (khud check kar lena):\n" + "\n".join(srcs[:6])
    return text

def call_gemini(key, system, contents, search):
    """Model 404 aaye to agla model try karta hai aur jo chale use yaad rakhta hai."""
    global G_MODEL
    err = None
    for m in dict.fromkeys([G_MODEL] + G_MODELS):
        try:
            text = _call_gemini_model(m, key, system, contents, search)
            G_MODEL = m
            return text
        except RuntimeError as e:
            err = e
            if "404" not in str(e):
                raise
    raise err

def flat(contents):
    return [{"role": "assistant" if c["role"] == "model" else "user", "content": c["parts"][0]["text"]} for c in contents]

def _compat_chat(provider, key, endpoint, model, system, contents):
    payload = {"model": model, "messages": [{"role": "system", "content": system}] + flat(contents)}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/gotramaninder/venom"
        headers["X-Title"] = "VENOM Assistant"
    r = requests.post(endpoint, headers=headers, json=payload, timeout=(10, 60))
    if r.status_code != 200:
        raise RuntimeError(f"{provider} HTTP {r.status_code}")
    data = r.json()
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()

def call_groq(key, system, contents):
    return _compat_chat("groq", key, "https://api.groq.com/openai/v1/chat/completions",
                        GROQ_MODEL, system, contents)

def call_openai(key, system, contents):
    return _compat_chat("openai", key, "https://api.openai.com/v1/chat/completions",
                        OPENAI_MODEL, system, contents)

def call_openrouter(key, system, contents):
    return _compat_chat("openrouter", key, "https://openrouter.ai/api/v1/chat/completions",
                        OPENROUTER_MODEL, system, contents)

def call_mistral(key, system, contents):
    return _compat_chat("mistral", key, "https://api.mistral.ai/v1/chat/completions",
                        MISTRAL_MODEL, system, contents)

def call_claude(key, system, contents):
    r = requests.post("https://api.anthropic.com/v1/messages",
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                      json={"model": CLAUDE_MODEL, "max_tokens": 2500, "system": system, "messages": flat(contents)},
                      timeout=(10, 60))
    if r.status_code != 200:
        raise RuntimeError(f"claude HTTP {r.status_code}")
    return "".join(b.get("text", "") for b in r.json()["content"]).strip()

def _cooldown(provider, error, key=None):
    match = re.search(r"(?:HTTP\s*)?(\d{3})", str(error))
    code = int(match.group(1)) if match else 0
    key_id = _provider_key_id(provider, key) if key else provider
    if code == 429:
        _PROVIDER_COOLDOWN[key_id] = time.time() + 60
    elif code in (401, 403):
        _PROVIDER_COOLDOWN[key_id] = time.time() + 300
    elif code >= 500 or not code:
        _PROVIDER_COOLDOWN[key_id] = time.time() + 30
    provider_keys = [k for p, k in PROVIDERS if p == provider]
    all_cooling = bool(provider_keys) and all(
        time.time() < _PROVIDER_COOLDOWN.get(_provider_key_id(provider, k), 0)
        for k in provider_keys
    )
    _PROVIDER_HEALTH[provider] = "cooldown" if all_cooling else "degraded"

def ask(prompt, search=False, keep=True):
    system = SYSTEM.replace("{now}", datetime.now().strftime("%A %d %B %Y, %I:%M %p"))
    contents = (history[-14:] if keep else []) + [{"role": "user", "parts": [{"text": prompt}]}]
    if not PROVIDERS:
        return "Koi API key nahi mili. VENOM API setup wizard chala."
    last_err = ""
    attempted = 0
    for prov, key in PROVIDERS:
        key_id = _provider_key_id(prov, key)
        if time.time() < _PROVIDER_COOLDOWN.get(key_id, 0):
            continue
        attempted += 1
        try:
            c2 = contents
            if search and prov != "gemini":
                c2 = contents[:-1] + [{"role": "user", "parts": [{"text": prompt +
                    "\n\n(Note: is provider par live web search available nahi hai. Apni knowledge se jawab de aur live verification ka daawa mat kar.)"}]}]
            if prov == "gemini":
                answer = call_gemini(key, system, contents, search)
            elif prov == "groq":
                answer = call_groq(key, system, c2)
            elif prov == "openai":
                answer = call_openai(key, system, c2)
            elif prov == "openrouter":
                answer = call_openrouter(key, system, c2)
            elif prov == "mistral":
                answer = call_mistral(key, system, c2)
            else:
                answer = call_claude(key, system, c2)
            if answer:
                _PROVIDER_HEALTH[prov] = "online"
                _PROVIDER_COOLDOWN.pop(key_id, None)
                if keep:
                    history.append({"role": "user", "parts": [{"text": prompt}]})
                    history.append({"role": "model", "parts": [{"text": answer}]})
                    del history[:-30]
                    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False), encoding="utf-8")
                return answer
            last_err = f"{prov}: empty response"
        except requests.RequestException as e:
            last_err = f"{prov}: network error"
            _cooldown(prov, e, key)
        except Exception as e:
            last_err = f"{prov}: {e}"
            _cooldown(prov, e, key)
    if attempted == 0:
        return "Saare configured AI providers abhi cooldown mein hain. Thodi der baad try kar."
    return f"AI providers abhi unavailable hain ({last_err}). Internet ya provider limits check kar; VENOM dobara try kar sakta hai."

def extract_json(prompt):
    raw = ask(prompt + "\nSirf valid JSON de. Koi explanation ya backticks nahi.", keep=False)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None

def deliver(reply, label="reply"):
    if len(reply) <= 380:
        speak(reply)
        return
    path = OUT_DIR / f"{label}_{datetime.now():%Y%m%d_%H%M%S}.txt"
    path.write_text(reply, encoding="utf-8")
    print("\n" + reply + "\n")
    short = " ".join(re.split(r"(?<=[.!?।])\s+", clean_for_speech(reply))[:2])
    speak(f"{short} Poora jawab screen pe hai aur outputs folder mein save hai.")

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

def num(x):
    try:
        return float(str(x).replace(",", "").replace("₹", "").strip())
    except Exception:
        return 0.0

def inr(x):
    return f"{int(x):,}"

# ================= CLIENTS + PAYMENTS (local ledger, AI se hisaab nahi) =================
CLIENTS = load_json(CLIENT_FILE, [])
RATES = load_json(RATE_FILE, {})

def get_client(name):
    n = (name or "").lower().strip()
    if not n:
        return None
    for c in CLIENTS:
        cn = c["name"].lower()
        if n in cn or cn in n:
            return c
    return None

def client_in_text(t):
    for c in CLIENTS:
        if c["name"].lower() in t.lower():
            return c
    return None

def add_client(text):
    d = extract_json('Is text se client details nikaal: "' + text + '". Schema: '
                     '{"name":"","work":"","price":null,"phone":"","email":"","deadline":""}')
    if not d or not d.get("name"):
        speak("Client ka naam samajh nahi aaya. Aise bol: naya client Rahul hai, uska logo design ka kaam hai, price 3000.")
        return
    c = get_client(d["name"])
    if c:
        for k in ("work", "phone", "email", "deadline"):
            if d.get(k):
                c[k] = d[k]
        if num(d.get("price")):
            c["price"] = num(d["price"])
    else:
        c = {"name": d["name"], "work": d.get("work", ""), "price": num(d.get("price")), "paid": 0,
             "phone": d.get("phone", ""), "email": d.get("email", ""), "deadline": d.get("deadline", ""),
             "payments": [], "created": datetime.now().strftime("%Y-%m-%d")}
        CLIENTS.append(c)
    save_json(CLIENT_FILE, CLIENTS)
    prompt = (f"Maninder ne naya client liya: {json.dumps(c, ensure_ascii=False)}. Uske rates: {json.dumps(RATES, ensure_ascii=False)}. "
              "Tu uska executive assistant hai. 'Sir,' se shuru karke briefing de: 1) kaam kya hai, 2) deliverables checklist, "
              "3) client se kaunse sawal poochne hain, 4) timeline, 5) price rates ke hisaab se theek hai ya nahi (rates na ho to bol), "
              "6) pehle 3 actions. Aakhir mein poochh: 'Sir, kya karna hai?'")
    deliver(ask(prompt), "client")

def payment_received(text):
    d = extract_json('Is text se payment details nikaal: "' + text + '". Schema: {"name":"","amount":0}')
    if not d:
        speak("Samajh nahi aaya. Aise bol: Rahul ka 2000 payment mila.")
        return
    c = get_client(d.get("name")) or (CLIENTS[0] if len(CLIENTS) == 1 else None)
    amt = num(d.get("amount"))
    if not c or not amt:
        speak("Client ka naam ya amount clear nahi hua.")
        return
    c["paid"] = num(c.get("paid")) + amt
    c.setdefault("payments", []).append({"date": datetime.now().strftime("%Y-%m-%d"), "amount": amt})
    save_json(CLIENT_FILE, CLIENTS)
    pending = max(num(c.get("price")) - c["paid"], 0)
    speak(f"{c['name']} se {inr(amt)} rupaye note kar liye. Total mila {inr(c['paid'])}, baaki {inr(pending)}.")

def list_pending():
    if not CLIENTS:
        speak("Abhi koi client save nahi hai.")
        return
    month = datetime.now().strftime("%Y-%m")
    got = sum(p["amount"] for c in CLIENTS for p in c.get("payments", []) if p["date"].startswith(month))
    rows = [(c["name"], num(c.get("price")) - num(c.get("paid"))) for c in CLIENTS if num(c.get("price")) > num(c.get("paid"))]
    msg = f"Is mahine {inr(got)} rupaye aaye hain. "
    if rows:
        msg += "Baaki: " + ", ".join(f"{n} {inr(p)}" for n, p in rows) + f". Total pending {inr(sum(p for _, p in rows))} rupaye."
    else:
        msg += "Kisi ka paisa baaki nahi hai."
    speak(msg)

def client_status(text):
    c = client_in_text(text)
    if not c:
        if not CLIENTS:
            speak("Abhi koi client save nahi hai.")
            return
        speak("Active clients: " + ", ".join(f"{x['name']} ({x.get('work', '')})" for x in CLIENTS))
        return
    pending = max(num(c.get("price")) - num(c.get("paid")), 0)
    deliver(ask(f"Client record: {json.dumps(c, ensure_ascii=False)}. Pending paisa: {inr(pending)}. 'Sir,' se short status briefing de "
                "aur next actions bata. Aakhir mein poochh: 'Sir, kya karna hai?'"), "client")

# ================= PRICING + NEGOTIATION =================
def set_rate(text):
    d = extract_json('Is text se kaam ka naam aur rate nikaal: "' + text + '". Schema: {"work":"","amount":0}')
    if not d or not d.get("work") or not num(d.get("amount")):
        speak("Aise bol: rate set reel editing 1500.")
        return
    RATES[d["work"].lower()] = num(d["amount"])
    save_json(RATE_FILE, RATES)
    speak(f"{d['work']} ka rate {inr(num(d['amount']))} rupaye save kar liya.")

def show_rates():
    if not RATES:
        speak("Tera rate card khali hai. Bol: rate set logo design 2500. Ya 'price batao reel editing' bol, market range dekhte hain.")
        return
    speak("Tere rates: " + ", ".join(f"{k} {inr(v)}" for k, v in RATES.items()))

def price_advice(text):
    deliver(ask(f"Maninder (India, freelance) ke liye ye kaam ka price: {text}. Uske apne rates: {json.dumps(RATES, ensure_ascii=False)}. "
                "Low / standard / premium range de, sirf search sources ke basis pe. Pakka range na mile to saaf bol, number mat bana. "
                "Quote karne ka tareeka, kya include/exclude kare, aur negotiation ke liye floor price bhi de.", search=True), "price")

def negotiate(text):
    c = client_in_text(text)
    deliver(ask(f"Client ne ye bola/offer kiya: {text}. Client record: {json.dumps(c, ensure_ascii=False) if c else 'nahi'}. "
                f"Maninder ke rates: {json.dumps(RATES, ensure_ascii=False)}. Tu Maninder ki taraf se negotiator hai. Output: "
                "1) offer theek hai ya nahi, 2) minimum floor price (rates na ho to pooch), 3) counter-offer, "
                "4) 3 reply drafts WhatsApp style: firm, friendly, walk-away, 5) discount ki jagah scope kam karne ka option. "
                "Sirf drafts, bhejna Maninder karega."), "negotiate")

# ================= LEADS + OUTREACH =================
def find_leads(text):
    deliver(ask(f"Maninder ke liye potential clients dhundh: {text}. Social media, design, ya video editing ki need wale local ya online businesses. "
                "SIRF wahi businesses likh jo search results mein mile. Har ek ke saath source link, kya need dikhi, aur approach angle. "
                "Contact number/email tabhi do jab source mein likha ho, warna 'contact source page pe dekh'. Kam leads sahi hain, fake nahi. "
                "Aakhir mein bata ki kise pehle approach kare aur kyun.", search=True), "leads")

def open_gmail(subject, body):
    url = ("https://mail.google.com/mail/?view=cm&fs=1&su=" + urllib.parse.quote(subject) + "&body=" + urllib.parse.quote(body[:1500]))
    webbrowser.open(url)

def copy_clip(text):
    try:
        import tkinter as tk
        root = tk.Tk(); root.withdraw()
        root.clipboard_clear(); root.clipboard_append(text); root.update(); root.destroy()
    except Exception:
        pass

def with_portfolio(t):
    t = t.replace("{PORTFOLIO}", PORTFOLIO_URL)
    return t

def outreach(text):
    phone = re.search(r"(?<!\d)(\d{10})(?!\d)", text)
    reply = ask("Cold outreach likh. Target aur offer is text se samajh: \"" + text + "\". Do versions de, exact in markers ke saath:\n"
                "###WHATSAPP\n(3-5 line, friendly Hinglish, personal, spammy nahi)\n###EMAIL\nSubject: ...\n(professional English, max 120 words, "
                "signature mat likh)\nSirf sach proof points use kar. Portfolio link ki jagah {PORTFOLIO} likh.", keep=False)
    wa, em = "", ""
    if "###EMAIL" in reply:
        parts = reply.split("###EMAIL")
        wa, em = parts[0].replace("###WHATSAPP", "").strip(), parts[1].strip()
    else:
        wa = reply
    wa = with_portfolio(wa)
    if PORTFOLIO_URL and PORTFOLIO_URL not in wa:
        wa += f"\nPortfolio: {PORTFOLIO_URL}"
    subject, body = "", with_portfolio(em)
    if body.lower().startswith("subject:"):
        first, _, body = body.partition("\n")
        subject, body = first.split(":", 1)[1].strip(), body.strip()
    full = f"WHATSAPP:\n{wa}\n\nEMAIL:\nSubject: {subject}\n{body}\n\n{SIGNATURE}"
    (OUT_DIR / f"outreach_{datetime.now():%Y%m%d_%H%M%S}.txt").write_text(full, encoding="utf-8")
    print("\n" + full + "\n")
    number = ("91" + phone.group(1)) if phone else ""
    webbrowser.open(f"https://wa.me/{number}?text=" + urllib.parse.quote(wa))
    if em:
        open_gmail(subject, body + "\n\n" + SIGNATURE)
    note = "" if PORTFOLIO_URL else " Dhyan rakh, .env mein PORTFOLIO_URL nahi hai, link nahi judega."
    speak("WhatsApp aur email dono draft ready. Dono khul gaye hain, bas receiver check karke tu bhej dena." + note)

def draft_email(text):
    reply = ask("Ye email draft kar, ready-to-send, English, professional par human. Pehli line 'Subject: ...' phir body. Signature mat likh. "
                "Kaam: " + text, keep=False)
    subject, body = "", reply
    if reply.lower().startswith("subject:"):
        first, _, body = reply.partition("\n")
        subject, body = first.split(":", 1)[1].strip(), body.strip()
    body = with_portfolio(body) + "\n\n" + SIGNATURE
    (OUT_DIR / f"email_{datetime.now():%Y%m%d_%H%M%S}.txt").write_text(f"Subject: {subject}\n\n{body}", encoding="utf-8")
    copy_clip(f"Subject: {subject}\n\n{body}")
    open_gmail(subject, body)
    print(f"\nSubject: {subject}\n\n{body}\n")
    speak("Email draft ready. Clipboard mein copy hai aur Gmail khul gaya. Receiver daal ke bhejna tera kaam.")

# ================= TRENDS + MONEY NEWS =================
def trends(text):
    deliver(ask(f"Abhi ke trends dhundh: {text}. Maninder ka niche: social media, reels, design, video editing, YouTube, clothing brand. "
                "Sirf search results ke basis pe. Har trend ke saath: kya hai, kaise use kare (content idea), aur source. "
                "Jo pakka nahi, usse 'unverified' likh.", search=True), "trends")

def invest_news(text):
    deliver(ask(f"Maninder paisa lagane se pehle news dekhna chahta hai: {text}. Strict rules: sirf search results mein jo mila wahi. "
                "Har news ke saath source aur date. Alag alag likh: CONFIRMED (official/reputed source) aur RUMOR/UNVERIFIED. "
                "Koi 'ye pakka hit hoga' ya buy/sell call mat de. Risk aur kya check karna chahiye (company filings, regulator) bata. "
                "Maninder student + business owner hai, pehle capital safety. Aakhir mein: 'Ye financial advice nahi hai, final faisla tera.'", search=True), "invest")

def money_plan():
    month = datetime.now().strftime("%Y-%m")
    got = sum(p["amount"] for c in CLIENTS for p in c.get("payments", []) if p["date"].startswith(month))
    pend = sum(max(num(c.get("price")) - num(c.get("paid")), 0) for c in CLIENTS)
    deliver(ask(f"Maninder ka is mahine ka freelance income: {inr(got)} rupaye aaya, {inr(pend)} pending. Paise kahan lagaye uska framework de "
                "(emergency fund, tools/skills, UrbaNest ya business reinvest, phir investing) as OPTIONS with example ranges jo wo badal sake. "
                "Uska monthly kharcha poochh. Specific stock ya 'guaranteed return' mat bol."), "money")

# ================= MEETINGS =================
def load_meetings():
    return load_json(MEET_FILE, [])

def add_meeting(text):
    now = datetime.now().strftime("%Y-%m-%d %H:%M, %A")
    d = extract_json(f'Abhi: {now}. Is text se meeting/reminder ka title aur time nikaal: "{text}". Schema: {{"title":"","when":"YYYY-MM-DD HH:MM"}}')
    try:
        when = datetime.strptime(d["when"], "%Y-%m-%d %H:%M")
    except Exception:
        speak("Time samajh nahi aaya. Aise bol: kal shaam 5 baje client call set kar.")
        return
    m = load_meetings()
    m.append({"title": d["title"], "when": d["when"], "notified": False})
    save_json(MEET_FILE, m)
    speak(f"Done. {d['title']}, {when:%d %B, %I:%M %p} pe. 10 minute pehle yaad dilaunga.")

def list_meetings():
    now = datetime.now()
    up = sorted([m for m in load_meetings() if datetime.strptime(m["when"], "%Y-%m-%d %H:%M") >= now], key=lambda m: m["when"])[:5]
    if not up:
        speak("Koi upcoming meeting nahi hai.")
        return
    speak("Aage ki meetings: " + ". ".join(f"{m['title']} {datetime.strptime(m['when'], '%Y-%m-%d %H:%M'):%d %b, %I:%M %p}" for m in up))

def check_reminders():
    m, changed, now = load_meetings(), False, datetime.now()
    for x in m:
        when = datetime.strptime(x["when"], "%Y-%m-%d %H:%M")
        if not x.get("notified") and when - timedelta(minutes=10) <= now <= when + timedelta(minutes=5):
            speak(f"Sir, yaad dila raha hu. {x['title']}, {when:%I:%M %p} pe hai.")
            x["notified"], changed = True, True
    if changed:
        save_json(MEET_FILE, m)

# ================= APPS + SYSTEM CONTROL =================
APPS = {"chrome": ("chrome", "chrome.exe"), "edge": ("msedge", "msedge.exe"), "notepad": ("notepad", "notepad.exe"),
        "calculator": ("calc", "CalculatorApp.exe"), "vscode": ("code", "Code.exe"), "spotify": ("spotify", "Spotify.exe"),
        "word": ("winword", "WINWORD.EXE"), "excel": ("excel", "EXCEL.EXE"), "powerpoint": ("powerpnt", "POWERPNT.EXE"),
        "paint": ("mspaint", "mspaint.exe"), "whatsapp": ("whatsapp:", "WhatsApp.exe"), "capcut": ("capcut", "CapCut.exe")}
# apps.json example: {"premiere": ["C:\\Program Files\\Adobe\\Adobe Premiere Pro 2025\\Adobe Premiere Pro.exe", "Adobe Premiere Pro.exe"]}
for k, v in load_json(APPS_FILE, {}).items():
    APPS[k.lower()] = tuple(v)

def match_app(n):
    for name in APPS:
        if f" {name} " in f" {n} ":
            return name
    return None

def open_app(name):
    cmd = APPS[name][0]
    try:
        if OS == "Windows":
            subprocess.Popen(f'start "" "{cmd}"', shell=True)
        elif OS == "Darwin":
            subprocess.Popen(["open", "-a", cmd])
        else:
            subprocess.Popen([cmd])
        speak(f"{name} khol diya.")
    except Exception:
        speak(f"{name} nahi khul paya. apps.json mein sahi path daal.")

def close_app(name):
    if OS != "Windows":
        speak("App close abhi sirf Windows pe hai.")
        return
    if confirm(f"{name} band kar du? Unsaved kaam ud sakta hai."):
        subprocess.run(["taskkill", "/IM", APPS[name][1], "/F"], capture_output=True)
        speak(f"{name} band kar diya.")
    else:
        speak("Theek hai, chhod diya.")

def ps(cmd, timeout=90):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=timeout)
    return r.stdout

def pj(cmd):
    try:
        out = ps(cmd).strip()
        data = json.loads(out) if out else []
        return [data] if isinstance(data, dict) else data
    except Exception:
        return []

def volume(n):
    if OS != "Windows":
        speak("Volume control abhi sirf Windows pe hai.")
        return
    if has(n, ["mute"]):
        key, times = 173, 1
    elif has(n, ["up", "badha", "zyada", "increase", "tez"]):
        key, times = 175, 5
    else:
        key, times = 174, 5
    ps(f"$w=New-Object -ComObject WScript.Shell; 1..{times}|%{{$w.SendKeys([char]{key})}}")
    speak("Done.")

def lock_screen():
    if OS == "Windows":
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    elif OS == "Darwin":
        subprocess.run(["pmset", "displaysleepnow"])
    speak("Laptop lock kar diya.")

def shutdown_laptop():
    speak("Theek hai. 10 second mein laptop band ho raha hai. Rokna ho to bol cancel.")
    if OS == "Windows":
        subprocess.run(["shutdown", "/s", "/t", "10"])
    elif OS == "Darwin":
        subprocess.Popen(["sh", "-c", "sleep 10 && osascript -e 'tell app \"System Events\" to shut down'"])
    else:
        subprocess.Popen(["sh", "-c", "sleep 10 && systemctl poweroff"])
    t0 = time.time()
    while time.time() - t0 < 8:
        if has(norm(listen(True)), ["cancel", "ruk", "mat karo", "nahi"]):
            if OS == "Windows":
                subprocess.run(["shutdown", "/a"])
            speak("Cancel kar diya. Laptop chalu hi rahega.")
            return
    sys.exit(0)

# ================= SECURITY (defensive, aggressive monitoring) =================
SYS_PROCS = {"svchost", "system", "lsass", "wininit", "services", "idle", ""}

def security_check():
    if OS != "Windows":
        speak("Ye security check abhi sirf Windows ke liye hai.")
        return
    speak("Security check shuru. Thoda time lagega.")
    issues, lines = [], []
    mp = pj("Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled,AntivirusSignatureAge | ConvertTo-Json")
    if mp:
        rt = bool(mp[0].get("RealTimeProtectionEnabled"))
        age = mp[0].get("AntivirusSignatureAge", 0) or 0
        lines.append(f"Defender real-time: {'ON' if rt else 'OFF'}, signature {age} din purani")
        if not rt:
            issues.append("Windows Defender real-time protection band hai")
        if age > 7:
            issues.append(f"Antivirus definitions {age} din purani hain")
    else:
        lines.append("Defender status nahi mila (koi aur antivirus ho sakta hai)")
    for p in pj("Get-NetFirewallProfile | Select-Object Name,Enabled | ConvertTo-Json"):
        on = str(p.get("Enabled")).lower() in ("true", "1")
        lines.append(f"Firewall {p.get('Name')}: {'ON' if on else 'OFF'}")
        if not on:
            issues.append(f"Firewall {p.get('Name')} band hai")
    startup = {s.get("Name"): s.get("Command") for s in pj("Get-CimInstance Win32_StartupCommand | Select-Object Name,Command | ConvertTo-Json")}
    base = load_json(SEC_FILE, None)
    if base is None:
        save_json(SEC_FILE, sorted(startup))
        lines.append(f"Startup baseline save kiya ({len(startup)} items). Aage se naya item aaya to alert dunga.")
    else:
        new = [s for s in startup if s not in base]
        if new:
            issues.append("Naye startup items: " + ", ".join(new))
    ports = pj("Get-NetTCPConnection -State Listen | ForEach-Object { $p=Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "
               "[pscustomobject]@{Port=$_.LocalPort;Addr=$_.LocalAddress;Proc=$p.ProcessName} } | ConvertTo-Json")
    exposed = sorted({f"{p.get('Proc')}:{p.get('Port')}" for p in ports if p.get("Addr") in ("0.0.0.0", "::")
                      and str(p.get("Proc") or "").lower() not in SYS_PROCS})
    lines.append(f"Network pe khule ports (non-system): {', '.join(exposed) if exposed else 'koi nahi'}")
    report = "\n".join(lines + ["ISSUES: " + ("; ".join(issues) if issues else "koi bada issue nahi")])
    print("\n" + report + "\n")
    speak("Issues mile: " + "; ".join(issues) if issues else "Basic checks theek lag rahe hain.")
    ai = ask("Ye mere Windows laptop ki security report hai:\n" + report + f"\nStartup items: {list(startup.items())[:25]}\n"
             "Sirf wahi flag kar jo sach mein sandigdh ho aur kyun. Panic mat failao. Safe next steps de (Defender full scan, "
             "Autoruns se check, suspicious app uninstall, password change). Jo samajh nahi aaya use 'pata nahi' bol.", keep=False)
    deliver(ai, "security")

def quick_scan():
    if OS != "Windows":
        speak("Scan abhi sirf Windows Defender ke liye hai.")
        return
    subprocess.Popen(["powershell", "-NoProfile", "-Command", "Update-MpSignature; Start-MpScan -ScanType QuickScan"])
    speak("Defender update karke quick scan background mein shuru kar diya. Result Windows Security mein dikhega.")

def lockdown():
    speak("Lockdown. Laptop lock aur virus scan.")
    quick_scan()
    lock_screen()

WATCH = [BASE / "venom.py", BASE / ".env"]
_alerted = set()
_last_integ = 0

def hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in WATCH if p.exists()}

def integrity_update():
    save_json(INTEG_FILE, hashes())
    speak("Integrity baseline update kar diya.")

def check_integrity():
    global _last_integ
    if time.time() - _last_integ < 60:
        return
    _last_integ = time.time()
    base = load_json(INTEG_FILE, None)
    if base is None:
        save_json(INTEG_FILE, hashes())
        return
    cur = hashes()
    changed = [k for k in cur if base.get(k) != cur[k]]
    new = [k for k in changed if k not in _alerted]
    if new:
        _alerted.update(new)
        speak(f"Alert. {', '.join(new)} badli hui hai. Agar tune nahi badli to kuch gadbad hai. Tune badli ho to bol integrity update.")

# ================= ROUTER =================
SITES = {"youtube studio": "https://studio.youtube.com", "youtube": "https://www.youtube.com",
         "instagram": "https://www.instagram.com", "canva": "https://www.canva.com", "gmail": "https://mail.google.com",
         "calendar": "https://calendar.google.com", "drive": "https://drive.google.com", "figma": "https://www.figma.com",
         "chatgpt": "https://chatgpt.com", "claude": "https://claude.ai"}

def reload_data():
    CLIENTS[:] = load_json(CLIENT_FILE, [])
    RATES.clear()
    RATES.update(load_json(RATE_FILE, {}))

def handle(text):
    n = norm(text)
    if not n:
        return None
    reload_data()
    if "shutdown" in n or "shut down" in n or (has(n, ["laptop", "computer"]) and has(n, ["band", "bandh", "bund", "off"])):
        shutdown_laptop(); return None
    if "lockdown" in n:
        lockdown(); return None
    if has(n, ["laptop lock", "screen lock", "lock kar", "lock karo"]):
        lock_screen(); return None
    if has(n, ["so ja", "so jao", "bye venom", "good night"]) or n.strip() == "sleep":
        speak("Theek hai. Jab chahiye, bas Venom bol dena.")
        return "sleep"
    if has(n, ["security", "virus", "malware", "hacker"]) and has(n, ["check", "dekh", "scan", "status", "hua", "safe"]):
        security_check(); return None
    if has(n, ["scan"]):
        quick_scan(); return None
    if "integrity update" in n:
        integrity_update(); return None
    if "volume" in n or n.strip() == "mute":
        volume(n); return None
    app = match_app(n)
    if app and has(n, ["close", "band", "bandh", "kill", "exit"]):
        close_app(app); return None
    if app and has(n, ["kholo", "khol", "open", "start", "chalu"]):
        open_app(app); return None
    if has(n, ["kholo", "khol", "open"]):
        for name, url in SITES.items():
            if name in n:
                webbrowser.open(url)
                speak(f"{name} khol diya.")
                return None
    if has(n, ["note kar", "note karo"]):
        note = re.split(r"note kar[o]?", text, maxsplit=1, flags=re.I)[-1].strip(" :,-")
        note = note or re.split(r"नोट कर[ो]?", text, maxsplit=1)[-1].strip(" :,-")
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%d-%m %H:%M}] {note}\n")
        speak("Note kar liya.")
        return None
    if has(n, ["whatsapp", "outreach", "pitch", "approach"]) and has(n, ["draft", "message", "msg", "likh", "banao", "bana", "pitch", "outreach"]):
        outreach(text); return None
    if has(n, ["email", "mail"]) and has(n, ["draft", "likh", "banao", "bana"]):
        draft_email(text); return None
    if has(n, ["dhundo", "dhoondh", "find", "search"]) and has(n, ["client", "lead", "customer"]):
        find_leads(text); return None
    if has(n, ["invest", "stock", "share market", "sensex", "nifty", "crypto", "mutual fund", "sip", "gold", "paise lagau", "paise lagana", "paisa lagau"]):
        invest_news(text); return None
    if has(n, ["money plan", "budget", "kharcha", "savings", "allocate"]):
        money_plan(); return None
    if has(n, ["payment", "paise", "paisa", "received"]):
        if has(n, ["mila", "received", "aaya", "paid", "diya"]) and re.search(r"\d", n):
            payment_received(text); return None
        if has(n, ["baaki", "pending", "kitna", "list", "kiska", "due", "status"]):
            list_pending(); return None
    if "rate" in n and has(n, ["set", "add", "fix", "save"]):
        set_rate(text); return None
    if has(n, ["price chart", "rate card", "mere rates", "my rates"]):
        show_rates(); return None
    if has(n, ["price", "charge", "quote", "kitna lu", "kitna lun"]):
        price_advice(text); return None
    if has(n, ["negotiat", "bargain", "discount", "kam kar"]):
        negotiate(text); return None
    if "trend" in n:
        trends(text); return None
    if "client" in n and has(n, ["naya", "new", "add", "hai", "kaam", "project"]):
        add_client(text); return None
    if "client" in n and has(n, ["status", "update", "sab", "kya chal", "kaun"]):
        client_status(text); return None
    if client_in_text(text) and has(n, ["status", "update", "kya", "kaise"]):
        client_status(text); return None
    if "meeting" in n or "reminder" in n:
        if has(n, ["kab", "kitni", "list", "dikha", "batao", "aaj"]):
            list_meetings()
        else:
            add_meeting(text)
        return None
    live = has(n, ["trending", "viral", "news", "aaj kal", "latest"])
    label = "youtube" if "youtube" in n else "reply"
    deliver(ask(text, search=live), label)
    return None

# ================= MAIN =================
def main():
    if not PROVIDERS:
        print("Koi API key nahi mili. .env mein GEMINI_API_KEY=... daal (aistudio.google.com se free).")
        sys.exit(1)
    if not PORTFOLIO_URL:
        print("(Tip: .env mein PORTFOLIO_URL=https://... daal, outreach mein portfolio link judega)")
    if not TEXT_MODE and sr is None:
        print("SpeechRecognition/PyAudio install nahi hai. Ya to unhe install kar, ya jarvis.py (browser HUD) chala.")
        sys.exit(1)
    if not TEXT_MODE:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.5)
    check_integrity()
    speak(f"Venom online. {len(PROVIDERS)} AI key active. Hum tumhare saath hain, Maninder.")
    awake = TEXT_MODE
    last = time.time()
    while True:
        check_reminders()
        check_integrity()
        text = listen(awake)
        if not text:
            if awake and not TEXT_MODE and time.time() - last > 90:
                awake = False
                print("(so gaya, 'Hey Venom' bol ke jagao)")
            continue
        print(f"Tu: {text}")
        n = norm(text)
        if not awake:
            if has(n, WAKE):
                awake, last = True, time.time()
                rest = re.sub(r"(hey|hay|heyo|hello|hi)?\s*(venom|venum|wenom|vinom)", "", n, count=1).strip()
                if len(rest) > 3 and has(rest, ["laptop", "shutdown", "lock"]):
                    handle(rest)
                else:
                    speak("Haan Maninder, bol. Kya kaam hai?")
            continue
        last = time.time()
        if handle(text) == "sleep":
            awake = False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nVenom band.")
