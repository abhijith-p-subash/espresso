"""Synthetic keystrokes that make the machine look "in use".

Inhibiting sleep and looking active are different things: chat clients and
presence indicators watch the *input idle timer*, which a power assertion does
not touch. F15 is used because it exists in the HID tables, is absent from
mainstream keyboards, and is not bound by default on any supported desktop.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class ActivitySimulator:
    """Taps a harmless key. ``pynput`` is imported lazily.

    Importing ``pynput`` connects to the display server, which fails on headless
    machines and during test collection, so it must not happen at module import.
    """

    def __init__(self) -> None:
        self._controller = None
        self._key = None
        self._failed = False
        self.unavailable_reason: str | None = None

    def _ensure_controller(self) -> bool:
        if self._controller is not None:
            return True
        if self._failed:
            return False
        try:
            from pynput.keyboard import Controller, Key

            self._controller = Controller()
            self._key = Key.f15
        except Exception as exc:  # noqa: BLE001 - pynput raises backend-specific errors
            self._failed = True
            self.unavailable_reason = f"Keyboard control unavailable: {exc}"
            log.warning("%s", self.unavailable_reason)
            return False
        return True

    @property
    def available(self) -> bool:
        return not self._failed

    def pulse(self) -> bool:
        """Send one key press/release. Returns whether it was delivered."""
        if not self._ensure_controller():
            return False
        try:
            self._controller.press(self._key)
            self._controller.release(self._key)
        except Exception as exc:  # noqa: BLE001 - backend-specific errors
            self.unavailable_reason = f"Could not send keystroke: {exc}"
            log.warning("%s", self.unavailable_reason)
            return False
        log.debug("Activity pulse sent")
        return True
