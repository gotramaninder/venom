"""
VENOM Scout: background mein leads dhundta hai aur roz ka brief banata hai.
Run:  python scout.py        (laptop on rahe tab tak chalta rahega)
Ye kuch bhejta nahi. Sirf leads.json aur briefs.json mein likhta hai. Bhejna tu approve karke karega.
"""
import json, re, sys, time, traceback
from datetime import datetime

import venom as V

BASE = V.BASE
LEADS_F = V.DATA_DIR / "leads.json"
CFG_F = V.DATA_DIR / "scout_config.json"
BRIEF_F = V.DATA_DIR / "briefs.json"
LOG_F = V.LOG_DIR / "scout.log"
DEFAULT_CFG = {"niches": ["salons and beauty studios Ahmedabad", "clothing and fashion brands Gujarat",
                          "coaching institutes Gujarat"], "interval_hours": 8, "max_new_per_run": 6}

def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    with open(LOG_F, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def find_leads(niche):
    raw = V.ask(
        f"Maninder (social media, design, video editing freelancer, Ahmedabad) ke liye '{niche}' mein 3 potential clients dhundh jinhe "
        "abhi social media/design/video ki need dikhti hai (jaise inconsistent Instagram, purane creatives). SIRF wahi businesses jo search "
        "results mein mile. Sirf JSON array de: "
        '[{"business":"","source":"url","need":"","angle":"","contact":""}]. Contact tabhi jab source mein likha ho, warna "".',
        search=True, keep=False)
    raw = raw.split("\n\nSources")[0]
    m = re.search(r"\[.*\]", raw, re.S)
    if not m:
        raise ValueError("JSON array nahi mila")
    return [x for x in json.loads(m.group(0)) if isinstance(x, dict) and x.get("business")]

def run_leads(cfg):
    leads = V.load_json(LEADS_F, [])
    known = {x["business"].lower() for x in leads}
    added = 0
    for niche in cfg["niches"]:
        if added >= cfg.get("max_new_per_run", 6):
            break
        try:
            for ld in find_leads(niche):
                if ld["business"].lower() in known or added >= cfg.get("max_new_per_run", 6):
                    continue
                ld.update(status="new", found=datetime.now().strftime("%Y-%m-%d"), niche=niche)
                leads.append(ld)
                known.add(ld["business"].lower())
                added += 1
            V.save_json(LEADS_F, leads)
            log(f"'{niche}' done, total new this run: {added}")
        except Exception as e:
            log(f"'{niche}' fail: {e}")
        time.sleep(25)  # free API limit ka dhyan
    return added

def daily_brief():
    briefs = V.load_json(BRIEF_F, [])
    today = datetime.now().strftime("%Y-%m-%d")
    if briefs and briefs[-1]["date"].startswith(today):
        return
    leads = V.load_json(LEADS_F, [])
    clients = V.load_json(V.CLIENT_FILE, [])
    pend = sum(max(V.num(c.get("price")) - V.num(c.get("paid")), 0) for c in clients)
    txt = V.ask("Maninder (social media + design + video editing freelancer, Ahmedabad) ke liye aaj ka brief: 1) 3-5 trends jo abhi chal rahe "
                f"hain (search se, source ke saath), 2) uske paas {sum(1 for x in leads if x.get('status') == 'new')} naye leads hain aur "
                f"₹{V.inr(pend)} pending hai, 3) aaj ke top 3 kaam, 4) apne kaam ko better karne ke 2 reasons/tareeke. Short rakh.",
                search=True, keep=False)
    briefs.append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "text": txt})
    V.save_json(BRIEF_F, briefs[-30:])
    log("daily brief saved")

def main():
    if not V.PROVIDERS:
        print("Koi API key nahi mili. .env check kar.")
        sys.exit(1)
    log("Scout online")
    while True:
        try:
            cfg = V.load_json(CFG_F, DEFAULT_CFG)
            run_leads(cfg)
            daily_brief()
        except Exception:
            log("cycle error:\n" + traceback.format_exc())
        hrs = max(1, int(V.load_json(CFG_F, DEFAULT_CFG).get("interval_hours", 8)))
        log(f"Agla cycle {hrs} ghante baad")
        time.sleep(hrs * 3600)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScout band.")
