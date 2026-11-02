"""
VENOM Studio: social media, design aur video editing ka kaam.
Content calendar, reel plan, captions, profile audit, aur tere design/video ka honest review (image ya video bhej).
"""
import base64
import mimetypes
import shutil
import subprocess
from pathlib import Path

import requests

import venom as V

WHO = ("Maninder: Ahmedabad, social media strategist + graphic designer + video editor, UrbaNest Clothing ka founder, "
       "apna YouTube channel. Clients: salons, clothing brands, coaching institutes. ")
HONEST = "Viral ya followers ki guarantee mat de. Jo verify nahi hua use 'unverified' likh. Fake numbers nahi."


def content_calendar(text):
    return V.ask(WHO + f"Content calendar bana: {text}. Din na bole to 7 din. Har din: platform, format (reel/carousel/story/post), topic, "
                 "hook (pehli line), CTA, posting time (India). Chhoti saaf list. Abhi ke trends search se le, source ke saath. " + HONEST,
                 search=True, keep=False)


def reel_plan(text):
    return V.ask(WHO + f"Reel/short ka poora plan: {text}. De: 1) 3 hook options (pehle 2 second), 2) script (seconds ke saath), "
                 "3) shot list, 4) on-screen text, 5) editing notes (cuts, transitions, music vibe), 6) caption + 10 hashtags, "
                 "7) best posting time. Pehle free tools suggest kar (CapCut, Canva). " + HONEST, keep=False)


def caption_pack(text):
    return V.ask(WHO + f"Captions bana: {text}. 3 versions (short, storytelling, CTA-heavy), har ek ke saath 10 relevant hashtags, "
                 "aur ek pinned comment idea. Hinglish ya jo language bole. " + HONEST, keep=False)


def growth_audit(text):
    return V.ask(WHO + f"Is profile/page ka audit kar: {text}. Jo maine nahi bataya wo guess mat kar, pooch. De: bio, grid/consistency, "
                 "content pillars, posting frequency, engagement ke sudhaar, 5 quick wins, 30 din ka plan. " + HONEST, search=True, keep=False)


def _gem_keys():
    return [k for p, k in V.PROVIDERS if p == "gemini"]


def _vision(prompt, images):
    parts = [{"text": prompt}] + [{"inline_data": {"mime_type": m, "data": base64.b64encode(d).decode()}} for m, d in images]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{V.G_MODEL}:generateContent"
    system = V.SYSTEM.replace("{now}", "")
    err = ""
    for key in _gem_keys():
        try:
            r = requests.post(url, params={"key": key},
                              json={"system_instruction": {"parts": [{"text": system}]},
                                    "contents": [{"role": "user", "parts": parts}]}, timeout=150)
            if r.status_code == 200:
                return "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"]).strip()
            err = f"gemini {r.status_code}"
        except Exception as e:
            err = str(e)
    return f"Review nahi ho paya ({err}). Key ya limit check kar."


def _frames(path, n=6):
    if not shutil.which("ffmpeg"):
        return [], 0, "ffmpeg install nahi hai (video review ke liye chahiye)"
    dur = 0.0
    if shutil.which("ffprobe"):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                           capture_output=True, text=True)
        try:
            dur = float(r.stdout.strip())
        except Exception:
            dur = 0.0
    tmp = V.OUT_DIR / "frames"
    tmp.mkdir(exist_ok=True)
    out = []
    for i in range(n):
        t = dur * (i + 0.5) / n if dur else i * 2
        f = tmp / f"f{i}.jpg"
        if f.exists():
            f.unlink()
        subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1", "-vf", "scale=720:-2", str(f)],
                       capture_output=True)
        if f.exists() and f.stat().st_size > 0:
            out.append(f)
    return out, dur, ""


def critique_media(path, note=""):
    if not _gem_keys():
        return "Design/video review ke liye Gemini key chahiye. .env mein GEMINI_API_KEY daal."
    path = Path(path)
    mime = mimetypes.guess_type(str(path))[0] or ""
    extra = ""
    if mime.startswith("image/"):
        if path.stat().st_size > 15 * 1024 * 1024:
            return "Image 15MB se badi hai. Chhoti karke bhej."
        images = [(mime, path.read_bytes())]
    elif mime.startswith("video/"):
        files, dur, why = _frames(path)
        if not files:
            return why or "Video se frames nahi nikal paya."
        images = [("image/jpeg", f.read_bytes()) for f in files]
        extra = f"Ye video ke {len(files)} frames hain (shuruaat se end tak), video lagbhag {dur:.0f} second ka hai. Audio frames se nahi dikhta, uska judge mat kar. "
    else:
        return "Sirf image ya video bhej."
    prompt = (WHO + extra + "Tu senior art director + video editor hai. Maninder ka kaam honest review kar, tareef nahi. Format: "
              "1) Score /10, 2) Kya acha hai (2-3 points), 3) Kya kamzor hai, specific (composition, typography, colour, hierarchy, contrast, "
              "Instagram safe zones; video ho to hook, pacing, cuts, captions, colour grade), 4) Top 5 fixes priority order mein, "
              "5) Kaunsa free tool use kare. " + HONEST + (f" Maninder ka note: {note}" if note else ""))
    return _vision(prompt, images)
