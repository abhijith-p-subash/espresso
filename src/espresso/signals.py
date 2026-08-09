"""Signal delivery that survives a native GUI event loop.

A plain :func:`signal.signal` handler is not enough here. CPython runs handlers
on the main thread *between bytecodes*, and while the tray is up the main
thread is parked inside a native run loop — ``NSApplication.run()`` on macOS,
``GetMessage()`` on Windows. Ctrl-C and SIGTERM are then received but never
dispatched, and the app appears to hang.

:func:`signal.set_wakeup_fd` is handled at the C level, which always runs, so
writing the signal number to a socket and reading it from a dedicated thread
wakes us up regardless of what the main thread is doing. A socket pair (rather
than a pipe) is used because that is the only form Windows supports.
"""

from __future__ import annotations

import contextlib
import logging
import signal
import socket
import threading

log = logging.getLogger(__name__)

DEFAULT_SIGNALS = ("SIGINT", "SIGTERM", "SIGBREAK")


class SignalWatcher:
    """Calls ``on_signal(signum)`` from a worker thread when a signal arrives.

    Args:
        on_signal: Invoked off the main thread; must be safe to call there.
        signal_names: Names of signals to watch. Names absent on the current
            platform are skipped.
    """

    def __init__(self, on_signal, signal_names=DEFAULT_SIGNALS) -> None:
        self._on_signal = on_signal
        self._signal_names = signal_names
        self._reader: socket.socket | None = None
        self._writer: socket.socket | None = None
        self._previous_handlers: dict[int, object] = {}
        self._previous_wakeup_fd: int | None = None
        self._thread: threading.Thread | None = None

    @staticmethod
    def _noop(_signum, _frame) -> None:
        """Keeps the signal from killing us; the reader thread does the work."""

    def install(self) -> bool:
        """Start watching. Returns ``False`` if signals could not be hooked."""
        if threading.current_thread() is not threading.main_thread():
            log.debug("Signal handlers can only be installed on the main thread")
            return False

        self._reader, self._writer = socket.socketpair()
        self._writer.setblocking(False)
        self._reader.settimeout(None)
        try:
            self._previous_wakeup_fd = signal.set_wakeup_fd(self._writer.fileno())
        except (ValueError, OSError) as exc:
            log.debug("set_wakeup_fd unavailable: %s", exc)
            self._close_sockets()
            return False

        for name in self._signal_names:
            sig = getattr(signal, name, None)
            if sig is None:
                continue
            try:
                self._previous_handlers[sig] = signal.signal(sig, self._noop)
            except (ValueError, OSError):
                log.debug("Could not hook %s", name)

        if not self._previous_handlers:
            self.uninstall()
            return False

        self._thread = threading.Thread(
            target=self._watch, name="espresso-signals", daemon=True
        )
        self._thread.start()
        return True

    def _watch(self) -> None:
        reader = self._reader
        while reader is not None:
            try:
                data = reader.recv(1)
            except OSError:
                return
            if not data:  # the writer was closed by uninstall()
                return
            signum = data[0]
            log.info("Received signal %s", signum)
            try:
                self._on_signal(signum)
            except Exception:  # noqa: BLE001 - shutdown must not raise here
                log.exception("Signal handler failed")
            return

    def uninstall(self) -> None:
        """Restore the previous handlers and stop the reader thread."""
        for sig, handler in self._previous_handlers.items():
            with contextlib.suppress(ValueError, OSError, TypeError):
                signal.signal(sig, handler)
        self._previous_handlers.clear()

        if self._previous_wakeup_fd is not None:
            with contextlib.suppress(ValueError, OSError):
                signal.set_wakeup_fd(self._previous_wakeup_fd)
            self._previous_wakeup_fd = None

        self._close_sockets()

    def _close_sockets(self) -> None:
        for sock in (self._writer, self._reader):
            if sock is not None:
                with contextlib.suppress(OSError):
                    sock.close()
        self._writer = None
        self._reader = None

    def __enter__(self) -> SignalWatcher:
        self.install()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.uninstall()
