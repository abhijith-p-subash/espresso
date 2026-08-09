"""The keep-awake engine, free of any UI dependency.

Separated from the tray so the interesting behaviour — start/stop races, mode
changes, back end lifetime — can be tested without a display server.
"""

from __future__ import annotations

import logging
import threading
import time

from .activity import ActivitySimulator
from .config import Config, clamp_interval, normalize_mode
from .keepawake import KeepAwakeBackend, create_backend

log = logging.getLogger(__name__)

#: How long :meth:`KeepAwakeService.stop` waits for the worker to unwind.
STOP_TIMEOUT = 10.0


class KeepAwakeService:
    """Runs a background loop that inhibits sleep and simulates activity.

    Args:
        config: Settings to read; mutated in place by the ``set_*`` methods.
        backend: Sleep inhibitor. Defaults to the current platform's.
        simulator: Keystroke source. Defaults to :class:`ActivitySimulator`.
        on_change: Called (from the controlling thread) after any state change,
            so a UI can refresh itself.
    """

    def __init__(
        self,
        config: Config,
        backend: KeepAwakeBackend | None = None,
        simulator: ActivitySimulator | None = None,
        on_change=None,
    ) -> None:
        self.config = config
        self.backend = backend if backend is not None else create_backend()
        self.simulator = simulator if simulator is not None else ActivitySimulator()
        #: Public so a UI constructed after the service can attach itself.
        self.on_change = on_change
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.pulse_count = 0
        self.last_pulse: float | None = None

    # -- state ---------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """Whether the worker is actually alive, not merely intended to be."""
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def _notify(self) -> None:
        if self.on_change is None:
            return
        try:
            self.on_change()
        except Exception:  # noqa: BLE001 - a broken UI callback must not stop us
            log.exception("State-change callback failed")

    # -- control -------------------------------------------------------------

    def start(self) -> bool:
        """Start the worker. Returns ``False`` if it was already running."""
        with self._lock:
            if self.is_active:
                log.debug("Start requested while already active")
                return False
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                args=(self._stop_event, self.config.interval, self.config.mode),
                name="espresso-worker",
                daemon=True,
            )
            self._thread.start()
        log.info("Started (mode=%s, interval=%ss)", self.config.mode, self.config.interval)
        self._notify()
        return True

    def stop(self) -> bool:
        """Stop the worker and wait for it to release the inhibitor."""
        with self._lock:
            thread, self._thread = self._thread, None
            self._stop_event.set()
        if thread is None:
            return False
        thread.join(timeout=STOP_TIMEOUT)
        if thread.is_alive():
            log.warning("Worker did not stop within %.0fs", STOP_TIMEOUT)
        else:
            log.info("Stopped")
        self._notify()
        return True

    def toggle(self) -> bool:
        """Flip between running and stopped. Returns the new active state."""
        if self.is_active:
            self.stop()
            return False
        self.start()
        return self.is_active

    def restart_if_active(self) -> None:
        """Apply a settings change to a running worker."""
        if self.is_active:
            self.stop()
            self.start()

    def set_interval(self, seconds: int) -> None:
        self.config.interval = clamp_interval(seconds, self.config.interval)
        self.config.save()
        self.restart_if_active()
        self._notify()

    def set_mode(self, mode: str) -> None:
        self.config.mode = normalize_mode(mode, self.config.mode)
        self.config.save()
        self.restart_if_active()
        self._notify()

    def shutdown(self) -> None:
        """Stop and make a final, defensive attempt to release the inhibitor."""
        self.stop()

    # -- worker --------------------------------------------------------------

    def _run(self, stop_event: threading.Event, interval: int, mode: str) -> None:
        """Worker body.

        The interval and mode are captured at start time so a concurrent
        settings change cannot half-apply mid-loop; ``restart_if_active``
        recycles the thread instead.

        The inhibitor is acquired and released *on this thread* because the
        Windows back end is thread-bound.
        """
        config = Config(interval=interval, mode=mode)
        acquired = False
        try:
            if config.inhibits_system:
                self.backend.acquire()
                acquired = True
            while not stop_event.is_set():
                if config.simulates_activity and self.simulator.pulse():
                    self.pulse_count += 1
                    self.last_pulse = time.time()
                if stop_event.wait(config.interval):
                    break
        except Exception:  # noqa: BLE001 - never let the worker die silently
            log.exception("Keep-awake worker crashed")
        finally:
            if acquired:
                try:
                    self.backend.release()
                except Exception:  # noqa: BLE001
                    log.exception("Failed to release sleep inhibitor")
