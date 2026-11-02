"""Safely import private settings and business data from one older VENOM folder."""
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
OUTPUTS = BASE / "outputs"
DATA.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

DATA_FILES = {
    "history.json", "meetings.json", "clients.json", "rates.json", "apps.json",
    "notes.txt", ".sessions.json",
    ".push.json", "leads.json", "queue.json", "briefs.json", "youtube_plan.json",
    "scout_config.json",
}

def copy_missing(src, dst):
    if not src.exists():
        return "missing"
    if dst.exists():
        return "kept-existing"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return "copied"

def main():
    raw = input("Purane VENOM folder ka full path paste kar: ").strip().strip('"')
    old = Path(raw).expanduser()
    if not old.is_dir() or old.resolve() == BASE:
        print("Folder path galat hai, ya current folder hi select hua hai.")
        return 1

    copied, kept = [], []
    old_env, new_env = old / ".env", BASE / ".env"
    if old_env.is_file():
        if not new_env.exists():
            shutil.copy2(old_env, new_env)
            copied.append(".env")
        else:
            existing_lines = new_env.read_text(encoding="utf-8").splitlines()
            existing_keys = {line.split("=", 1)[0].strip() for line in existing_lines
                             if "=" in line and not line.lstrip().startswith("#")}
            additions = []
            for line in old_env.read_text(encoding="utf-8").splitlines():
                if "=" not in line or line.lstrip().startswith("#"):
                    continue
                key = line.split("=", 1)[0].strip()
                if key and key not in existing_keys:
                    additions.append(line)
                    existing_keys.add(key)
            if additions:
                with new_env.open("a", encoding="utf-8") as f:
                    f.write("\n" + "\n".join(additions) + "\n")
                copied.append(".env (missing settings merged; current values kept)")
            else:
                kept.append(".env (current values kept)")

    old_data = old / "data"
    for name in sorted(DATA_FILES):
        candidates = [old_data / name, old / name] if old_data.is_dir() else [old / name]
        for source in candidates:
            result = copy_missing(source, DATA / name)
            if result == "copied":
                copied.append("data/" + name)
                break
            if result == "kept-existing":
                kept.append("data/" + name)
                break

    old_outputs = old / "outputs"
    if old_outputs.is_dir():
        for src in old_outputs.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(old_outputs)
            result = copy_missing(src, OUTPUTS / rel)
            if result == "copied":
                copied.append("outputs/" + str(rel))
            elif result == "kept-existing":
                kept.append("outputs/" + str(rel))

    print("\nIMPORT COMPLETE. Purana folder change/delete nahi kiya.")
    print("Copied:", len(copied))
    for name in copied:
        print("  +", name)
    print("Existing destination files kept:", len(kept))
    for name in kept:
        print("  =", name)
    print("\nAgar .env copy hui hai, API wizard dobara chala sakta hai.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
