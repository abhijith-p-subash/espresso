"""macOS Accessibility permission checks.

Without Accessibility access macOS drops synthetic key events *silently* —
``pynput`` reports success and nothing happens. Detecting this up front turns a
baffling "it doesn't work" into an actionable prompt.
"""

from __future__ import annotations

import logging
import subprocess
import sys

log = logging.getLogger(__name__)

_SETTINGS_URL = "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"


def needs_accessibility_grant() -> bool:
    """True only when we can prove macOS will drop our synthetic events."""
    if sys.platform != "darwin":
        return False
    try:
        from ApplicationServices import AXIsProcessTrusted
    except ImportError:
        log.debug("ApplicationServices unavailable; skipping Accessibility check")
        return False
    try:
        return not bool(AXIsProcessTrusted())
    except Exception as exc:  # noqa: BLE001 - PyObjC bridge errors vary
        log.debug("Accessibility check failed: %s", exc)
        return False


def open_accessibility_settings() -> None:
    """Open the macOS Accessibility privacy pane."""
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(["open", _SETTINGS_URL], check=False, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("Could not open Accessibility settings: %s", exc)
