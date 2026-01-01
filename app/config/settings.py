from __future__ import annotations

from pathlib import Path
import os
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    REPO_ROOT = BASE_DIR
else:
    BASE_DIR = Path(__file__).resolve().parents[2]
    REPO_ROOT = BASE_DIR
APP_NAME = "python_auto_cpg"


def resolve_user_data_root() -> Path:
    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if root:
            return Path(root) / APP_NAME
        return Path.home() / "AppData" / "Local" / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


USER_DATA_ROOT = resolve_user_data_root()
DATA_DIR = USER_DATA_ROOT / "data"
LOG_DIR = USER_DATA_ROOT / "logs"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "app.sqlite3"
LOG_FILE = LOG_DIR / "garena-test.log"


def resolve_playwright_dir() -> Path:
    candidates = []
    env_root = os.environ.get("PLAYWRIGHT_ROOT")
    if env_root:
        candidates.append(Path(env_root) / "playwright")
        candidates.append(Path(env_root))
    candidates.append(BASE_DIR / "playwright")
    candidates.append(Path.cwd() / "playwright")
    for candidate in candidates:
        if (candidate / "garena-runner.js").exists():
            return candidate
    return REPO_ROOT / "playwright"


PLAYWRIGHT_DIR = resolve_playwright_dir()

DEFAULT_NEW_PASSWORD = "Password#2025"

DB_BUSY_TIMEOUT_MS = 5000
DB_RETRY_COUNT = 7
DB_RETRY_MIN_DELAY = 0.05
DB_RETRY_MAX_DELAY = 0.2

PROXY_API_URL = "https://proxyxoay.shop/api/get.php"
