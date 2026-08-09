"""Per-platform locations for configuration, state and log files.

Kept dependency-free on purpose: pulling in ``platformdirs`` for three
``if`` branches is not worth the extra wheel in every build.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from . import APP_NAME


def _home() -> Path:
    return Path("~").expanduser()


def config_dir() -> Path:
    """Directory holding the user's ``config.json``."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        return Path(base) / APP_NAME if base else _home() / "AppData" / "Roaming" / APP_NAME
    if sys.platform == "darwin":
        return _home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else _home() / ".config") / APP_NAME.lower()


def state_dir() -> Path:
    """Directory holding logs and the single-instance lock."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        return Path(base) / APP_NAME if base else config_dir()
    if sys.platform == "darwin":
        return _home() / "Library" / "Logs" / APP_NAME
    base = os.environ.get("XDG_STATE_HOME")
    return (Path(base) if base else _home() / ".local" / "state") / APP_NAME.lower()


def ensure_dir(path: Path) -> Path:
    """Create ``path`` if possible, falling back to a temp dir.

    A read-only or otherwise unusable home directory must not stop the tray
    icon from appearing, so this degrades instead of raising.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        fallback = Path(tempfile.gettempdir()) / APP_NAME.lower()
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def config_file() -> Path:
    return ensure_dir(config_dir()) / "config.json"


def log_file() -> Path:
    return ensure_dir(state_dir()) / "espresso.log"


def lock_file() -> Path:
    return ensure_dir(state_dir()) / "espresso.lock"
