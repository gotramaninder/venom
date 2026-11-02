"""Interactive, local-only VENOM API key setup. Keys are stored in .env, never printed."""
import getpass
import os
import re
import webbrowser
from pathlib import Path

BASE = Path(__file__).parent
ENV_FILE = BASE / ".env"
PROVIDERS = [
    ("Gemini (recommended primary)", "GEMINI_API_KEY", "https://aistudio.google.com/apikey"),
    ("Groq (optional; enable only if your account shows free quota)", "GROQ_API_KEY", "https://console.groq.com/keys"),
    ("OpenRouter (free-model backup)", "OPENROUTER_API_KEY", "https://openrouter.ai/settings/keys"),
    ("Mistral (free-mode backup)", "MISTRAL_API_KEY", "https://console.mistral.ai/api-keys/"),
]

def read_env():
    values, lines = {}, []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        for line in lines:
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip().strip('"').strip("'")
    return values, lines

def save_env(values, lines):
    replaced = set()
    out = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in values:
                out.append(f"{key}={values[key]}")
                replaced.add(key)
                continue
        out.append(line)
    for key, value in values.items():
        if key not in replaced:
            out.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass

def main():
    values, lines = read_env()
    print("\n===== VENOM AI PROVIDER SETUP =====")
    print("Keys sirf is laptop ki .env file mein save hongi; GitHub par nahi.\n")
    for label, env_name, url in PROVIDERS:
        current = values.get(env_name, "")
        print(f"{label}: {'already configured' if current else 'not configured'}")
        action = input("  Is provider ki key add/replace karni hai? [y/N]: ").strip().lower()
        if action != "y":
            continue
        print("  Browser mein provider dashboard khol raha hu. Key copy karke neeche paste kar.")
        webbrowser.open(url)
        secret = getpass.getpass("  API key (input hidden): ").strip()
        if secret:
            values[env_name] = secret
            print("  Saved (key hidden).")
        else:
            print("  Blank input; existing setting unchanged.")
    if not any(values.get(k) for _, k, _ in PROVIDERS):
        print("\nAbhi koi supported free AI key configure nahi hui.")
        return 1
    save_env(values, lines)
    print("\nSettings saved. Existing .env settings/data untouched.")
    print("Next: start_venom.bat. Provider fallback automatic hai.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
