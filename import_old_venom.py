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
    "notes.txt", ".integrity.json", ".security_baseline.json", ".sessions.json",
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
    env_result = copy_missing(old / ".env", BASE / ".env")
    if env_result == "copied":
        copied.append(".env")
    elif env_result == "kept-existing":
        kept.append(".env (new setup already has one; not overwritten)")

    old_data = old / "data"
    source_data = old_data if old_data.is_dir() else old
    for name in sorted(DATA_FILES):
        result = copy_missing(source_data / name, DATA / name)
        if result == "copied":
            copied.append("data/" + name)
        elif result == "kept-existing":
            kept.append("data/" + name)

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
