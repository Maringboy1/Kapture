from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# If running from local source tree where project root is writable, keep runtime state inside state/
if (PROJECT_ROOT / "pyproject.toml").is_file() and os.access(PROJECT_ROOT, os.W_OK):
    STATE_DIR = PROJECT_ROOT / "state"
    ASSETS_DIR = PROJECT_ROOT / "assets"
else:
    # Standard XDG state dir for installed packages
    xdg_state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    STATE_DIR = xdg_state / "kapture"
    pkg_assets = Path(__file__).resolve().parents[1] / "assets"
    if pkg_assets.exists():
        ASSETS_DIR = pkg_assets
    elif (PROJECT_ROOT / "assets").exists():
        ASSETS_DIR = PROJECT_ROOT / "assets"
    else:
        ASSETS_DIR = Path("/usr/share/kapture/assets")

CONFIG_FILE = STATE_DIR / "config.json"
LOGS_DIR = STATE_DIR / "logs"
TMP_DIR = STATE_DIR / "tmp"

# Directly save in user's home directory (/home/<user>)
SCREENSHOTS_DIR = Path.home()
VIDEOS_DIR = Path.home()

for p in (STATE_DIR, LOGS_DIR, TMP_DIR, SCREENSHOTS_DIR, VIDEOS_DIR):
    p.mkdir(parents=True, exist_ok=True)


def ensure_dirs():
    for p in (STATE_DIR, LOGS_DIR, TMP_DIR, SCREENSHOTS_DIR, VIDEOS_DIR):
        p.mkdir(parents=True, exist_ok=True)


def xdg_or(path, fallback):
    return Path(path) if path else Path(fallback)

