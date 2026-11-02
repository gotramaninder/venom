# VENOM

**Ek hi project. Ek hi installation. Ek hi daily start button.**

## Sabse pehle

1. Is repository ka ZIP download karke **Extract All** karo.
2. Extracted folder ke andar `1_SETUP_VENOM.bat` double-click karo.
3. API setup wizard mein provider dashboard khulega. Jo free keys available hain, unhe add karo.
4. Roz VENOM chalane ke liye sirf `2_START_VENOM.bat` double-click karo.

## Root folder mein kya hai?

- `1_SETUP_VENOM.bat` — first-time install; dobara chalane par environment repair/update.
- `2_START_VENOM.bat` — daily start.
- `3_API_SETUP.bat` — API keys add/change karna.
- `jarvis.py`, `venom.py`, `scout.py`, `studio.py`, `notify.py`, `dashboard.py` — app ke internal modules; inhe move/rename mat karna.
- `static/` — VENOM HUD screen.
- `data/` — client records, payments, leads, meetings, settings, chat history.
- `logs/` — diagnostic logs.
- `outputs/` — generated reports and uploads.
- `.venv/` — isolated Python packages (installer creates this).
- `.env` — private API keys and settings (installer/wizard creates this).

## Data safety

- Existing JSON data from older VENOM versions is moved into `data/` automatically on first launch, without overwriting an existing destination file.
- Do not delete `data/`, `.env`, or `outputs/` if you want to keep your records.
- Never upload `.env` or private records to GitHub or send API keys in chat.
- Before replacing an old installation, copy its `.env`, `data/`, and `outputs/` folders as a backup.

## Optional features

- `4_DASHBOARD_SETUP.bat` installs the optional Streamlit business dashboard dependencies.
- `5_PHONE_SETUP.bat` is for phone access; use only after local VENOM works.
- Browser voice is part of the HUD. Optional desktop wake-word voice packages are separate.

## Troubleshooting

If setup fails, run `1_SETUP_VENOM.bat` again and keep the error window open. Logs are stored in `logs/`.
