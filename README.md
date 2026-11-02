# VENOM

**Ek hi project. Ek hi installation. Ek hi daily start button.**

## Bas ye steps follow karo

1. GitHub se ZIP download karo aur **Extract All** karke ek hi naya folder banao, jaise `C:\\VENOM_FINAL`. Purane VENOM folders ko abhi delete mat karna; woh backup rahenge.
2. Extracted folder ke andar `1_SETUP_VENOM.bat` double-click karo. Ye isolated Python environment banayega, core packages install karega aur API wizard kholega.
3. Agar purane VENOM folder mein data/settings hain, `IMPORT_OLD_VENOM.bat` double-click karo aur purane VENOM folder ka full path paste karo. Ye existing values ko overwrite kiye bina missing `.env`, client records, leads, meetings, chat history aur outputs import karega. Purana folder untouched rahega.
4. Agar old API settings import hui hain, `3_API_SETUP.bat` dobara chala kar missing provider keys add karo.
5. Roz sirf `2_START_VENOM.bat` double-click karo.

## Root folder mein kya hai?

- `1_SETUP_VENOM.bat` — first-time install / repair.
- `2_START_VENOM.bat` — daily start (HUD + Scout).
- `3_API_SETUP.bat` — API keys add/change.
- `IMPORT_OLD_VENOM.bat` — purane folder se private data safe import.
- `BACKUP_VENOM.bat` — `.env`, `data/`, `outputs/` ka ZIP backup.
- `4_DASHBOARD_SETUP.bat` — optional Streamlit dashboard dependencies.
- `5_PHONE_SETUP.bat` — optional phone access.
- `6_DESKTOP_VOICE_SETUP.bat` — optional desktop wake-word voice packages.
- Python files — internal engine modules; inhe move/rename/delete mat karna.
- `static/` — HUD screen.
- `data/` — clients, payments, leads, meetings, settings, history.
- `logs/` — diagnostic logs.
- `outputs/` — generated reports and uploaded media.
- `.venv/` — isolated Python environment, setup khud banata hai.
- `.env` — private API keys and settings.

## Data safety

- Importer never overwrites an existing destination file. Existing values remain safe.
- Run `BACKUP_VENOM.bat` before major updates.
- Do not delete `data/`, `.env`, or `outputs/` if you want to keep your records.
- Never upload `.env` or private records to GitHub or send API keys in chat.
- The old VENOM folder is not deleted by setup or import.

## Optional features

- `4_DASHBOARD_SETUP.bat` installs optional dashboard dependencies.
- `5_PHONE_SETUP.bat` is for phone access; use only after local VENOM works.
- Browser voice is part of the HUD. For desktop wake-word voice, run `6_DESKTOP_VOICE_SETUP.bat` first. Only then enable optional `install_autostart.bat`.

## Free API note

Free model availability, account eligibility, and request quotas vary by provider and can change. Automatic fallback tries configured providers in order; it cannot guarantee uninterrupted or unlimited service.

## Troubleshooting

If setup fails, run `1_SETUP_VENOM.bat` again and keep the error window open. Logs are stored in `logs/`.
