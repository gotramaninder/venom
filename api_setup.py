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
    ("Mistral (backup)", "MISTRAL_API_KEY", "https://console.mistral.ai/api-keys/"),
    ("OpenRouter (free-model backup)", "OPENROUTER_API_KEY", "https://openrouter.ai/settings/keys"),
    ("Groq (optional; quota depends on account)", "GROQ_API_KEY", "https://console.groq.com/keys"),
    ("Anthropic Claude (optional; may require billing)", "ANTHROPIC_API_KEY", "https://console.anthropic.com/settings/keys"),
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
        key_names = [k for k, v in values.items()
                     if v and (k == env_name or re.fullmatch(re.escape(env_name) + r"_\d+", k))]
        print(f"{label}: {len(key_names)} key(s) configured")
        action = input("  [A]dd backup key, [R]eplace first key, [N]one? [N]: ").strip().lower()
        if action not in ("a", "r"):
            continue
        print("  Browser mein provider dashboard khol raha hu. Key copy karke neeche paste kar.")
        webbrowser.open(url)
        secret = getpass.getpass("  API key (input hidden): ").strip()
        if not secret:
            print("  Blank input; existing settings unchanged.")
            continue
        if action == "r" or not key_names:
            target = env_name
        else:
            used = {int(k.rsplit("_", 1)[1]) for k in key_names if k != env_name}
            suffix = 2
            while suffix in used or f"{env_name}_{suffix}" in values:
                suffix += 1
            target = f"{env_name}_{suffix}"
        values[target] = secret
        print(f"  Saved as {target} (key hidden).")
    if not any(values.get(k) for _, k, _ in PROVIDERS):
        print("\nAbhi koi supported free AI key configure nahi hui.")
        return 1
    save_env(values, lines)
    print("\nSettings saved. Existing .env settings/data untouched.")
    print("Next: double-click 2_START_VENOM.bat. Provider fallback automatic hai.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
