"""System tray front end."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import time

from pystray import Icon, Menu, MenuItem

from . import APP_NAME, __version__
from .config import INTERVAL_PRESETS, MODES, Config
from .paths import log_file
from .permissions import needs_accessibility_grant, open_accessibility_settings
from .resources import base_icon, idle_icon
from .service import KeepAwakeService
from .signals import SignalWatcher

log = logging.getLogger(__name__)

#: Seconds to wait for the tray loop to unwind after a signal before giving up.
FORCE_EXIT_AFTER = 10.0

_MODE_LABELS = {
    "both": "Sleep + activity",
    "system": "Prevent sleep only",
    "activity": "Simulate activity only",
}


def _force_exit() -> None:
    """Last resort when a native tray loop refuses to exit.

    Safe by construction: every inhibitor is tied to this process's lifetime
    (``caffeinate -w``, a stdin pipe to ``systemd-inhibit``, and a per-thread
    Windows execution state), so none of them can outlive a hard exit.
    """
    log.warning("Tray loop did not exit within %.0fs; forcing shutdown", FORCE_EXIT_AFTER)
    logging.shutdown()
    os._exit(0)


def _format_interval(seconds: int) -> str:
    if seconds % 60 == 0 and seconds >= 60:
        minutes = seconds // 60
        return f"{minutes} min" if minutes > 1 else "1 min"
    return f"{seconds} sec"


def open_path(path) -> None:
    """Open ``path`` with the desktop's default handler."""
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False, timeout=10)
        else:
            subprocess.run(["xdg-open", str(path)], check=False, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("Could not open %s: %s", path, exc)


class EspressoTray:
    """Wires :class:`KeepAwakeService` to a pystray icon."""

    def __init__(self, config: Config, service: KeepAwakeService | None = None) -> None:
        self.config = config
        self.service = service or KeepAwakeService(config)
        self.service.on_change = self.refresh
        self._force_exit_timer: threading.Timer | None = None
        self._active_image = base_icon()
        self._idle_image = idle_icon(self._active_image)
        self.icon = Icon(
            APP_NAME,
            self._idle_image,
            title=APP_NAME,
            menu=self._build_menu(),
        )

    # -- menu ----------------------------------------------------------------

    def _status_text(self, _item=None) -> str:
        if not self.service.is_active:
            return "☕ Paused"
        detail = _format_interval(self.config.interval)
        if self.service.last_pulse:
            since = int(time.time() - self.service.last_pulse)
            return f"● Awake — every {detail} (last pulse {since}s ago)"
        return f"● Awake — every {detail}"

    def _warning_text(self, _item=None) -> str:
        return "⚠️ Grant Accessibility access…"

    def _warning_visible(self, _item=None) -> bool:
        return self.config.simulates_activity and needs_accessibility_grant()

    def _interval_menu(self) -> Menu:
        def setter(seconds: int):
            return lambda _icon=None, _item=None: self.service.set_interval(seconds)

        return Menu(
            *(
                MenuItem(
                    _format_interval(seconds),
                    setter(seconds),
                    checked=lambda _item, seconds=seconds: self.config.interval == seconds,
                    radio=True,
                )
                for seconds in INTERVAL_PRESETS
            )
        )

    def _mode_menu(self) -> Menu:
        def setter(mode: str):
            return lambda _icon=None, _item=None: self.service.set_mode(mode)

        return Menu(
            *(
                MenuItem(
                    _MODE_LABELS[mode],
                    setter(mode),
                    checked=lambda _item, mode=mode: self.config.mode == mode,
                    radio=True,
                )
                for mode in MODES
            )
        )

    def _build_menu(self) -> Menu:
        return Menu(
            MenuItem(self._status_text, None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(
                "Keep awake",
                self._on_toggle,
                checked=lambda _item: self.service.is_active,
                default=True,
            ),
            MenuItem("Interval", self._interval_menu()),
            MenuItem("Mode", self._mode_menu()),
            Menu.SEPARATOR,
            MenuItem(
                self._warning_text,
                self._on_fix_permissions,
                visible=self._warning_visible,
            ),
            MenuItem("Open log file", self._on_open_log),
            MenuItem(f"{APP_NAME} v{__version__}", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Quit", self._on_quit),
        )

    # -- callbacks -----------------------------------------------------------

    def _on_toggle(self, _icon=None, _item=None) -> None:
        self.service.toggle()

    def _on_open_log(self, _icon=None, _item=None) -> None:
        open_path(log_file())

    def _on_fix_permissions(self, _icon=None, _item=None) -> None:
        open_accessibility_settings()

    def _on_quit(self, _icon=None, _item=None) -> None:
        log.info("Quit requested")
        self.service.shutdown()
        self.icon.stop()

    def refresh(self) -> None:
        """Re-render icon, tooltip and menu after a state change.

        pystray only re-evaluates dynamic menu text when asked to, and several
        back ends build the menu once at creation time, so this is required —
        not merely an optimisation.
        """
        try:
            active = self.service.is_active
            self.icon.icon = self._active_image if active else self._idle_image
            self.icon.title = f"{APP_NAME} — {'awake' if active else 'paused'}"
            self.icon.update_menu()
        except Exception:  # noqa: BLE001 - a tray refresh must never crash the app
            log.exception("Could not refresh tray icon")

    # -- lifecycle -----------------------------------------------------------

    def _on_signal(self, _signum) -> None:
        """Shut down after Ctrl-C or SIGTERM.

        Runs on the signal watcher's thread. ``Icon.stop`` is safe to call from
        there: every back end wakes its loop by posting an event.
        """
        self._force_exit_timer = threading.Timer(FORCE_EXIT_AFTER, _force_exit)
        self._force_exit_timer.daemon = True
        self._force_exit_timer.start()
        self._on_quit()

    def run(self) -> None:
        """Block on the tray event loop until the user quits."""
        watcher = SignalWatcher(self._on_signal)
        watcher.install()
        if self.config.start_active:
            self.service.start()
        self.refresh()
        if self._warning_visible():
            log.warning(
                "macOS Accessibility access is not granted; simulated keystrokes "
                "will be ignored until it is."
            )
        try:
            self.icon.run()
        finally:
            if self._force_exit_timer is not None:
                self._force_exit_timer.cancel()
            watcher.uninstall()
            self.service.shutdown()
