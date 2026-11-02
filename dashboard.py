"""
VENOM Command Center (easy interface).
Run:  streamlit run dashboard.py
Voice app (venom.py) aur ye dashboard same data files use karte hain.
"""
import json, re, time, urllib.parse
from datetime import datetime

import streamlit as st
import venom as V

BASE = V.BASE
LEADS_F = V.DATA_DIR / "leads.json"
QUEUE_F = V.DATA_DIR / "queue.json"
YT_F = V.DATA_DIR / "youtube_plan.json"
BRIEF_F = V.DATA_DIR / "briefs.json"
CFG_F = V.DATA_DIR / "scout_config.json"
DEFAULT_CFG = {"niches": ["salons and beauty studios Ahmedabad", "clothing and fashion brands Gujarat",
                          "coaching institutes Gujarat"], "interval_hours": 8, "max_new_per_run": 6}

st.set_page_config(page_title="Venom", page_icon="🖤", layout="wide")
V.reload_data()
QS = st.session_state

# ---------- helpers ----------
def L(path, default):
    return V.load_json(path, default)

def S(path, data):
    V.save_json(path, data)

def ai(prompt, search=False):
    with st.spinner("Venom soch raha hai..."):
        return V.ask(prompt, search=search, keep=False)

def jget(prompt, search=False):
    with st.spinner("Venom dhundh raha hai..."):
        raw = V.ask(prompt + "\nSirf valid JSON de, koi explanation ya backticks nahi.", search=search, keep=False)
    raw = raw.split("\n\nSources")[0]
    m = re.search(r"[\[{].*[\]}]", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None

def wa_url(to, text):
    d = re.sub(r"\D", "", to or "")
    if len(d) == 10:
        d = "91" + d
    return f"https://wa.me/{d}?text=" + urllib.parse.quote(text)

def gmail_url(to, subject, body):
    return ("https://mail.google.com/mail/?view=cm&fs=1&to=" + urllib.parse.quote(to or "") + "&su=" +
            urllib.parse.quote(subject) + "&body=" + urllib.parse.quote(body[:1500]))

def split_pitch(raw):
    wa, em = raw, ""
    if "###EMAIL" in raw:
        a, b = raw.split("###EMAIL", 1)
        wa, em = a.replace("###WHATSAPP", "").strip(), b.strip()
    wa = wa.replace("{PORTFOLIO}", V.PORTFOLIO_URL)
    if V.PORTFOLIO_URL and V.PORTFOLIO_URL not in wa:
        wa += f"\nPortfolio: {V.PORTFOLIO_URL}"
    subject, body = "", em.replace("{PORTFOLIO}", V.PORTFOLIO_URL)
    if body.lower().startswith("subject:"):
        first, _, body = body.partition("\n")
        subject, body = first.split(":", 1)[1].strip(), body.strip()
    return wa, subject, (body + "\n\n" + V.SIGNATURE) if body else ""

def queue_add(title, channel, to, subject, body):
    q = L(QUEUE_F, [])
    q.append({"id": int(time.time() * 1000) + len(q), "title": title, "channel": channel, "to": to,
              "subject": subject, "body": body, "status": "pending", "created": datetime.now().strftime("%Y-%m-%d %H:%M")})
    S(QUEUE_F, q)

def make_pitch(lead):
    raw = ai("Cold outreach likh is lead ke liye: " + json.dumps(lead, ensure_ascii=False) + ". Exact in markers ke saath:\n"
             "###WHATSAPP\n(3-5 line friendly Hinglish, personal, spammy nahi, lead ki need ka zikr)\n###EMAIL\nSubject: ...\n"
             "(professional English, max 120 words, signature mat likh)\nSirf sach proof points use kar. Portfolio link ki jagah {PORTFOLIO} likh.")
    wa, subject, body = split_pitch(raw)
    contact = lead.get("contact", "") or ""
    phone = (re.search(r"\d[\d\s\-+]{8,}\d", contact) or [""])[0] if re.search(r"\d{10}", contact) else ""
    mail = (re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", contact) or [""])[0] if "@" in contact else ""
    queue_add(lead.get("business", "lead"), "whatsapp", phone, "", wa)
    if body:
        queue_add(lead.get("business", "lead"), "email", mail, subject, body)

# ---------- header ----------
st.title("🖤 VENOM Command Center")
if not V.PROVIDERS:
    st.error("Koi API key nahi mili. .env mein GEMINI_API_KEY daal aur dashboard dobara chala.")
tabs = st.tabs(["🏠 Home", "💰 Quote", "👥 Clients & Payments", "📨 Leads & Approval", "🎯 Meeting Prep", "▶️ YouTube", "⚙️ Setup"])

# ================= HOME =================
with tabs[0]:
    clients = L(V.CLIENT_FILE, [])
    month = datetime.now().strftime("%Y-%m")
    got = sum(p["amount"] for c in clients for p in c.get("payments", []) if p["date"].startswith(month))
    pend = sum(max(V.num(c.get("price")) - V.num(c.get("paid")), 0) for c in clients)
    leads, queue = L(LEADS_F, []), L(QUEUE_F, [])
    a, b, c_, d = st.columns(4)
    a.metric("Is mahine aaya", f"₹{V.inr(got)}")
    b.metric("Baaki (pending)", f"₹{V.inr(pend)}")
    c_.metric("Naye leads", sum(1 for x in leads if x.get("status") == "new"))
    d.metric("Approval ka wait", sum(1 for x in queue if x.get("status") in ("pending", "approved")))

    left, right = st.columns(2)
    with left:
        st.subheader("Meetings")
        now = datetime.now()
        up = sorted([m for m in V.load_meetings() if datetime.strptime(m["when"], "%Y-%m-%d %H:%M") >= now], key=lambda m: m["when"])[:6]
        for m in up:
            st.write(f"• **{m['title']}** — {m['when']}")
        if not up:
            st.caption("Koi upcoming meeting nahi.")
        with st.form("meet"):
            t = st.text_input("Meeting / reminder")
            dd = st.date_input("Date")
            tt = st.time_input("Time")
            if st.form_submit_button("Add") and t:
                ms = V.load_meetings()
                ms.append({"title": t, "when": f"{dd:%Y-%m-%d} {tt:%H:%M}", "notified": False})
                S(V.MEET_FILE, ms)
                st.rerun()
    with right:
        st.subheader("Venom ka brief")
        briefs = L(BRIEF_F, [])
        if briefs:
            st.caption(briefs[-1]["date"])
            st.markdown(briefs[-1]["text"])
        else:
            st.caption("Abhi koi brief nahi. Neeche button daba, ya scout.py chala ke background mein rakh.")
        if st.button("Aaj ka brief banao (trends + kya karna chahiye)"):
            txt = ai("Maninder (social media + design + video editing freelancer, Ahmedabad) ke liye aaj ka brief: 1) 3-5 trends jo abhi chal rahe "
                     f"hain (search se, source ke saath), 2) uski ledger: is mahine ₹{V.inr(got)} aaya, ₹{V.inr(pend)} pending, "
                     f"{sum(1 for x in leads if x.get('status') == 'new')} naye leads, 3) aaj ke top 3 kaam, 4) apne kaam ko better karne ke 2 reasons/tareeke. "
                     "Short rakh.", search=True)
            briefs.append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "text": txt})
            S(BRIEF_F, briefs[-30:])
            st.rerun()

# ================= QUOTE =================
with tabs[1]:
    st.subheader("Kaam ka rate, timeline aur approach")
    with st.sidebar:
        st.header("Quote settings")
        st.caption("Ye multipliers mere defaults hain, apne experience se badal.")
        cx_map = {"Simple": st.slider("Simple", 0.5, 1.5, 1.0, 0.05), "Medium": st.slider("Medium", 0.8, 2.0, 1.3, 0.05),
                  "Complex": st.slider("Complex", 1.0, 3.0, 1.7, 0.05)}
        ct_map = {"Chhota local business": st.slider("Chhota local", 0.5, 1.5, 0.9, 0.05),
                  "Startup / brand": st.slider("Startup/brand", 0.8, 2.0, 1.0, 0.05),
                  "Badi company": st.slider("Badi company", 1.0, 3.0, 1.3, 0.05),
                  "International": st.slider("International", 1.0, 3.0, 1.5, 0.05)}
        rush_mult = st.slider("Rush multiplier", 1.0, 2.0, 1.3, 0.05)
    q1, q2 = st.columns(2)
    work = q1.text_input("Kaam (jaise: Instagram reel editing, logo design, social media handling)")
    unit = q1.text_input("Unit", "per reel")
    qty = q1.number_input("Kitne units", 1, 500, 1)
    override = q1.number_input("Apna unit price ₹ (0 = auto)", 0, 1000000, 0, step=100)
    cx = q2.selectbox("Complexity", list(cx_map), index=1)
    ct = q2.selectbox("Client type", list(ct_map), index=1)
    rush = q2.checkbox("Urgent / rush")
    revs = q2.number_input("Revisions included", 0, 10, 2)

    if st.button("Calculate karo", type="primary") and work.strip():
        own = next((v for k, v in V.RATES.items() if k in work.lower() or work.lower() in k), None)
        std = low = prem = 0.0
        src = ""
        if override:
            std, low, prem, src = override, override * 0.85, override * 1.3, "Tera diya hua unit price"
        elif own:
            std, low, prem, src = own, own * 0.85, own * 1.3, "Tera rate card"
        else:
            mk = jget(f"India ke freelance market mein '{work}' ({unit}) ka INR price, 2026. Schema: "
                      '{"low":0,"standard":0,"premium":0,"confidence":"low|medium|high","note":"source ya kaise nikala"}. '
                      "Sirf search results ke basis pe. Pakka na mile to numbers 0 rakh aur confidence low.", search=True)
            if isinstance(mk, dict) and V.num(mk.get("standard")):
                std = V.num(mk["standard"])
                low = V.num(mk.get("low")) or std * 0.7
                prem = V.num(mk.get("premium")) or std * 1.5
                src = f"Market search (confidence: {mk.get('confidence', '?')}). {mk.get('note', '')}"
        if not std:
            st.warning("Market rate pakka nahi mila, fake number nahi dunga. 'Apna unit price' daal ke dobara calculate kar.")
        else:
            mult = cx_map[cx] * ct_map[ct] * (rush_mult if rush else 1.0)
            plan = ai(f"Kaam: {work}, {qty} {unit}, complexity {cx}, client type {ct}, rush {rush}, {revs} revisions included. "
                      "Maninder ke liye markdown mein de: **Timeline** (din ke breakdown ke saath), **Approach** (step by step), "
                      "**Client se ye poochh**, **Scope mein kya include/exclude**, **Risk/red flags**. Short aur practical.")
            QS["quote"] = {"work": work, "qty": qty, "unit": unit, "floor": low * qty * cx_map[cx], "quote": std * qty * mult,
                           "stretch": prem * qty * mult, "src": src, "plan": plan, "revs": revs, "cx": cx, "ct": ct}
    qd = QS.get("quote")
    if qd:
        m1, m2, m3 = st.columns(3)
        m1.metric("Floor (isse kam nahi)", f"₹{V.inr(qd['floor'])}")
        m2.metric("Quote karne ka price", f"₹{V.inr(qd['quote'])}")
        m3.metric("Stretch (best case)", f"₹{V.inr(qd['stretch'])}")
        st.caption(f"Base: {qd['src']}. Advance 50% rakhna common practice hai: ₹{V.inr(qd['quote'] * 0.5)} (tu badal sakta hai).")
        st.markdown(qd["plan"])
        p1, p2 = st.columns(2)
        if p1.button("Proposal draft banao → Approval Queue"):
            body = ai(f"Short client proposal message (WhatsApp style, Hinglish) likh: kaam {qd['work']}, {qd['qty']} {qd['unit']}, "
                      f"price ₹{V.inr(qd['quote'])}, {qd['revs']} revisions included, 50% advance. Timeline is plan se le:\n{qd['plan']}\nSirf sach, {{PORTFOLIO}} link ke saath.")
            body = body.replace("{PORTFOLIO}", V.PORTFOLIO_URL)
            queue_add(f"Proposal: {qd['work']}", "whatsapp", "", "", body)
            st.success("Queue mein daal diya. 'Leads & Approval' tab mein dekh.")
        cname = p2.text_input("Client ka naam (save karne ke liye)")
        if p2.button("Is quote se client save karo") and cname:
            cl = L(V.CLIENT_FILE, [])
            cl.append({"name": cname, "work": qd["work"], "price": round(qd["quote"]), "paid": 0, "phone": "", "email": "",
                       "deadline": "", "payments": [], "created": datetime.now().strftime("%Y-%m-%d")})
            S(V.CLIENT_FILE, cl)
            st.success(f"{cname} save ho gaya.")

# ================= CLIENTS =================
with tabs[2]:
    cl = L(V.CLIENT_FILE, [])
    st.subheader("Clients")
    if cl:
        st.dataframe([{"Client": c["name"], "Kaam": c.get("work", ""), "Price": V.num(c.get("price")), "Mila": V.num(c.get("paid")),
                       "Baaki": max(V.num(c.get("price")) - V.num(c.get("paid")), 0), "Deadline": c.get("deadline", "")} for c in cl],
                     use_container_width=True)
    else:
        st.caption("Abhi koi client nahi.")
    f1, f2 = st.columns(2)
    with f1.form("addc"):
        st.markdown("**Naya client**")
        n = st.text_input("Naam")
        w = st.text_input("Kaam")
        p = st.number_input("Price ₹", 0, 10000000, 0, step=500)
        ph = st.text_input("Phone")
        em = st.text_input("Email")
        dl = st.text_input("Deadline")
        if st.form_submit_button("Save") and n:
            cl.append({"name": n, "work": w, "price": p, "paid": 0, "phone": ph, "email": em, "deadline": dl,
                       "payments": [], "created": datetime.now().strftime("%Y-%m-%d")})
            S(V.CLIENT_FILE, cl)
            st.rerun()
    with f2.form("pay"):
        st.markdown("**Payment mila**")
        who = st.selectbox("Client", [c["name"] for c in cl]) if cl else st.text_input("Client")
        amt = st.number_input("Amount ₹", 0, 10000000, 0, step=500)
        if st.form_submit_button("Note karo") and cl and amt:
            for c in cl:
                if c["name"] == who:
                    c["paid"] = V.num(c.get("paid")) + amt
                    c.setdefault("payments", []).append({"date": datetime.now().strftime("%Y-%m-%d"), "amount": amt})
            S(V.CLIENT_FILE, cl)
            st.rerun()
    if cl:
        pick = st.selectbox("Client briefing (Venom bolega: 'Sir, ye ye hai')", [c["name"] for c in cl])
        if st.button("Briefing do"):
            c = next(x for x in cl if x["name"] == pick)
            st.markdown(ai(f"Client record: {json.dumps(c, ensure_ascii=False)}. 'Sir,' se short status briefing de aur next actions bata. "
                           "Aakhir mein poochh: 'Sir, kya karna hai?'"))

# ================= LEADS & APPROVAL =================
with tabs[3]:
    st.subheader("Leads (scout.py background mein dhundta hai)")
    leads = L(LEADS_F, [])
    if st.button("Abhi 1 baar leads dhundo"):
        cfg = L(CFG_F, DEFAULT_CFG)
        niche = cfg["niches"][0] if cfg.get("niches") else "salons Ahmedabad"
        found = jget(f"Maninder (social media, design, video editing freelancer, Ahmedabad) ke liye '{niche}' mein 3 potential clients dhundh jinhe "
                     'social media/design/video ki need dikhti hai. SIRF wahi jo search results mein mile. JSON array: '
                     '[{"business":"","source":"url","need":"","angle":"","contact":""}]. Contact tabhi jab source mein likha ho, warna "".', search=True)
        names = {x["business"].lower() for x in leads}
        if isinstance(found, list):
            for f in found:
                if isinstance(f, dict) and f.get("business") and f["business"].lower() not in names:
                    f.update(status="new", found=datetime.now().strftime("%Y-%m-%d"))
                    leads.append(f)
            S(LEADS_F, leads)
            st.rerun()
        else:
            st.warning("Is baar leads parse nahi hui, dobara try kar.")
    with st.expander("Lead khud add karo"):
        with st.form("addl"):
            lb = st.text_input("Business")
            ln = st.text_input("Kya need dikhi")
            lc = st.text_input("Contact (phone/email)")
            if st.form_submit_button("Add") and lb:
                leads.append({"business": lb, "need": ln, "contact": lc, "source": "manual", "angle": "", "status": "new",
                              "found": datetime.now().strftime("%Y-%m-%d")})
                S(LEADS_F, leads)
                st.rerun()
    for i, ld in enumerate(reversed(leads[-30:])):
        with st.expander(f"{ld['business']}  [{ld.get('status', 'new')}]"):
            st.write(f"**Need:** {ld.get('need', '')}")
            st.write(f"**Angle:** {ld.get('angle', '')}")
            st.write(f"**Contact:** {ld.get('contact') or 'source page pe dekh'}")
            st.write(f"**Source:** {ld.get('source', '')}")
            if st.button("Pitch draft banao (WhatsApp + Email)", key=f"pitch{i}"):
                make_pitch(ld)
                for x in leads:
                    if x["business"] == ld["business"]:
                        x["status"] = "drafted"
                S(LEADS_F, leads)
                st.rerun()

    st.divider()
    st.subheader("Approval Queue (tu verify kare, tabhi aage badhega)")
    queue = L(QUEUE_F, [])
    live = [x for x in queue if x["status"] in ("pending", "approved")]
    if not live:
        st.caption("Queue khali hai.")
    for it in live:
        with st.container(border=True):
            st.markdown(f"**{it['title']}** — {it['channel']} — {it['created']}")
            to = st.text_input("Kisko (phone / email)", value=it.get("to", ""), key=f"to{it['id']}")
            subj = st.text_input("Subject", value=it.get("subject", ""), key=f"s{it['id']}") if it["channel"] == "email" else ""
            body = st.text_area("Message (edit kar sakta hai)", value=it["body"], height=160, key=f"b{it['id']}")
            if it["status"] == "pending":
                a1, a2 = st.columns(2)
                if a1.button("✅ Approve", key=f"ap{it['id']}"):
                    it.update(status="approved", to=to, subject=subj, body=body)
                    S(QUEUE_F, queue)
                    st.rerun()
                if a2.button("🗑️ Reject", key=f"rj{it['id']}"):
                    it["status"] = "rejected"
                    S(QUEUE_F, queue)
                    st.rerun()
            else:
                url = wa_url(it["to"], it["body"]) if it["channel"] == "whatsapp" else gmail_url(it["to"], it["subject"], it["body"])
                a1, a2 = st.columns(2)
                a1.link_button("Open karo (tu send dabayega)", url)
                if a2.button("Sent ho gaya", key=f"sent{it['id']}"):
                    it["status"] = "sent"
                    S(QUEUE_F, queue)
                    st.rerun()
    sent = [x for x in queue if x["status"] == "sent"]
    if sent:
        st.caption(f"Ab tak sent: {len(sent)}")

# ================= MEETING PREP =================
with tabs[4]:
    st.subheader("Meeting ya pitch ki taiyari")
    mc1, mc2 = st.columns(2)
    target = mc1.text_input("Kisse milna hai (business / person)")
    about = mc1.text_area("Wo kya karte hain / kya pata hai", height=100)
    goal = mc2.selectbox("Goal", ["Naya client pitch", "Order close karna", "Price negotiate", "Follow-up"])
    extra = mc2.text_input("Kuch special (jaise: budget kam hai, competitor se baat kar rahe)")
    if st.button("Meeting kit banao", type="primary") and target:
        kit = ai(f"Maninder ek meeting mein jaa raha hai: {target}. Unke baare mein: {about}. Goal: {goal}. Extra: {extra}. "
                 f"Uske rates: {json.dumps(V.RATES, ensure_ascii=False)}. Search se unke baare mein jo mile wo use kar (source ke saath, jo nahi mila wo 'pata nahi'). "
                 "Markdown mein de: 1) unke baare mein research, 2) 60 second pitch, 3) kya sawal poochne hain, 4) objections aur unke jawab, "
                 "5) price kaise bolna hai (anchor, floor), 6) meeting ke baad follow-up email draft. Sach proof points hi use kar.", search=True)
        QS["kit"] = kit
        (V.OUT_DIR / f"meetingkit_{datetime.now():%Y%m%d_%H%M%S}.md").write_text(kit, encoding="utf-8")
    if QS.get("kit"):
        st.markdown(QS["kit"])
        st.download_button("Kit download karo", QS["kit"], file_name="meeting_kit.md")

# ================= YOUTUBE =================
with tabs[5]:
    st.subheader("YouTube planner (title, description, keywords, schedule)")
    st.info("Honest baat: YouTube API se auto-upload karo to naye API projects ke videos private lock ho jaate hain jab tak audit pass na ho. "
            "Isliye Venom sab kuch ready karta hai, tu YouTube Studio mein paste karke Schedule dabata hai (2 minute ka kaam).")
    y1, y2 = st.columns(2)
    topic = y1.text_input("Video ka idea / topic")
    audience = y1.text_input("Audience", "students aur young creators")
    fmt = y2.selectbox("Format", ["Short", "Long video"])
    lang = y2.selectbox("Language", ["Hinglish", "English", "Hindi"])
    check = y2.checkbox("Pehle trends check karo (search)", value=False)
    if st.button("Package banao", type="primary") and topic:
        pkg = jget(f"YouTube {fmt} ka poora package: topic '{topic}', audience {audience}, language {lang}. Schema: "
                   '{"titles":["5 options"],"hook":"pehle 5 second ka line","description":"SEO-friendly, pehli 2 line mein hook, '
                   'neeche 3-5 hashtags","tags":["10-15 keywords"],"thumbnail_ideas":["3 ideas, max 4 shabd text"],'
                   '"pinned_comment":"","why_it_may_work":"honest, guarantee nahi"}. Viral ka guarantee mat de.', search=check)
        QS["yt"] = pkg if isinstance(pkg, dict) else None
        if QS["yt"] is None:
            st.warning("Parse nahi hua, dobara try kar.")
    yt = QS.get("yt")
    if yt:
        st.markdown("**Titles**")
        for t in yt.get("titles", []):
            st.code(t, language=None)
        st.markdown("**Hook**")
        st.code(yt.get("hook", ""), language=None)
        st.markdown("**Description**")
        st.code(yt.get("description", ""), language=None)
        st.markdown("**Tags / keywords** (comma separated paste kar)")
        st.code(", ".join(yt.get("tags", [])), language=None)
        st.markdown("**Thumbnail ideas**")
        for t in yt.get("thumbnail_ideas", []):
            st.write("•", t)
        st.caption(f"Pinned comment: {yt.get('pinned_comment', '')}")
        st.caption(f"Kyun chal sakta hai: {yt.get('why_it_may_work', '')}")
        s1, s2, s3 = st.columns(3)
        pd_ = s1.date_input("Publish date", key="ytd")
        pt_ = s2.time_input("Publish time", key="ytt")
        if s3.button("Schedule list mein daalo"):
            plan = L(YT_F, [])
            plan.append({"topic": topic, "title": (yt.get("titles") or [topic])[0], "when": f"{pd_:%Y-%m-%d} {pt_:%H:%M}", "done": False})
            S(YT_F, plan)
            st.success("Add ho gaya.")
    plan = L(YT_F, [])
    if plan:
        st.markdown("**Mera upload schedule**")
        for i, p in enumerate(sorted(plan, key=lambda x: x["when"])):
            st.write(f"{'✅' if p['done'] else '🕒'} {p['when']} — {p['title']}")

# ================= SETUP =================
with tabs[6]:
    st.subheader("Setup aur status")
    cnt = {}
    for prov, _ in V.PROVIDERS:
        cnt[prov] = cnt.get(prov, 0) + 1
    st.write("Active AI keys:", cnt or "koi nahi")
    st.write("Portfolio link:", V.PORTFOLIO_URL or "⚠️ .env mein PORTFOLIO_URL daal")
    st.markdown("**Scout (background lead hunter) settings**")
    cfg = L(CFG_F, DEFAULT_CFG)
    niches = st.text_area("Kahan dhundna hai (ek line = ek niche)", "\n".join(cfg["niches"]))
    ih = st.number_input("Kitne ghante mein ek baar", 1, 48, int(cfg.get("interval_hours", 8)))
    mx = st.number_input("Ek baar mein max naye leads", 1, 20, int(cfg.get("max_new_per_run", 6)))
    if st.button("Settings save"):
        S(CFG_F, {"niches": [x.strip() for x in niches.splitlines() if x.strip()], "interval_hours": ih, "max_new_per_run": mx})
        st.success("Save ho gaya. scout.py agle cycle mein utha lega.")
    st.markdown("""
**Step by step**
1. `pip install -r requirements.txt`
2. `.env` banao (`.env.example` copy karke) aur key + `PORTFOLIO_URL` daal
3. Dashboard: `streamlit run dashboard.py`
4. Voice: alag terminal mein `python venom.py`
5. Background scout: alag terminal mein `python scout.py` (laptop on ho tab tak dhundta rahega)
6. Roz ka flow: Home brief dekh → Leads mein pitch draft banao → Approval Queue mein verify → Open karke send dabao → payment aaye to note karo
""")
