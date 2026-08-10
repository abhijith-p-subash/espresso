"""Persisted user settings, with validation and safe defaults."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from .paths import config_file

log = logging.getLogger(__name__)

#: How the app keeps the machine awake.
#:
#: ``system``   — ask the OS power manager to inhibit sleep (the reliable one).
#: ``activity`` — tap a harmless key so apps see "user is present".
#: ``both``     — do both; they solve different problems.
MODES = ("both", "system", "activity")

MIN_INTERVAL = 5
MAX_INTERVAL = 3600
INTERVAL_PRESETS = (30, 60, 120, 300, 600)


DEFAULT_INTERVAL = 60
#: ``system`` is the default because it needs no permissions on any platform:
#: it prevents sleep out of the box with nothing to grant and nothing to
#: prompt about. Synthetic keystrokes — the only part that needs macOS
#: Accessibility access — are opt-in via the tray menu.
DEFAULT_MODE = "system"


def clamp_interval(value: object, fallback: int = DEFAULT_INTERVAL) -> int:
    """Coerce ``value`` to a sane number of seconds within the allowed range."""
    try:
        seconds = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        log.warning("Invalid interval %r, using %ss", value, fallback)
        return fallback
    return max(MIN_INTERVAL, min(MAX_INTERVAL, seconds))


def normalize_mode(value: object, fallback: str = DEFAULT_MODE) -> str:
    """Coerce ``value`` to one of :data:`MODES`."""
    if isinstance(value, str) and value.lower() in MODES:
        return value.lower()
    log.warning("Unknown mode %r, falling back to %r", value, fallback)
    return fallback


@dataclass
class Config:
    """User-tunable settings.

    Attributes:
        interval: Seconds between simulated activity pulses.
        mode: One of :data:`MODES`.
        start_active: Whether to begin keeping the system awake on launch.
        log_level: Root log level name.
    """

    interval: int = DEFAULT_INTERVAL
    mode: str = DEFAULT_MODE
    start_active: bool = True
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        self.interval = clamp_interval(self.interval)
        self.mode = normalize_mode(self.mode)
        self.start_active = bool(self.start_active)
        if not isinstance(self.log_level, str) or not hasattr(logging, self.log_level.upper()):
            self.log_level = "INFO"
        self.log_level = self.log_level.upper()

    @property
    def inhibits_system(self) -> bool:
        return self.mode in ("both", "system")

    @property
    def simulates_activity(self) -> bool:
        return self.mode in ("both", "activity")

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        """Read config from disk. A missing or corrupt file yields defaults."""
        path = path or config_file()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return cls()
        except (OSError, ValueError) as exc:
            log.warning("Could not read %s (%s); using defaults", path, exc)
            return cls()
        if not isinstance(raw, dict):
            log.warning("Config at %s is not an object; using defaults", path)
            return cls()
        known = {f: raw[f] for f in cls.__dataclass_fields__ if f in raw}
        return cls(**known)

    def save(self, path: Path | None = None) -> bool:
        """Write config atomically. Returns ``False`` if it could not be saved."""
        path = path or config_file()
        tmp = path.with_name(path.name + ".tmp")
        try:
            tmp.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
            tmp.replace(path)
            return True
        except OSError as exc:
            log.warning("Could not save config to %s: %s", path, exc)
            tmp.unlink(missing_ok=True)
            return False
