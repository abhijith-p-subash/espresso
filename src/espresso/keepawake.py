"""Platform back ends that ask the OS to stay awake.

Simulating a keystroke alone is not enough: on every major desktop OS the sleep
timer is driven by the power manager, and several of them ignore synthetic
input events entirely. Each back end here uses the documented, supported
mechanism for its platform and degrades to a no-op when that mechanism is
missing, so the app never hard-fails on an unusual desktop.

Back ends are *not* thread-safe and, on Windows, are thread-*bound*:
``SetThreadExecutionState`` applies to the calling thread and is cleared when
that thread exits. Acquire and release from the same, long-lived thread.
"""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
import subprocess
import sys

log = logging.getLogger(__name__)

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class KeepAwakeBackend:
    """Base class: a no-op inhibitor."""

    name = "none"
    #: Human-readable reason this back end cannot inhibit sleep, if any.
    unavailable_reason: str | None = "No supported power-management API found"

    @property
    def available(self) -> bool:
        return self.unavailable_reason is None

    def acquire(self) -> None:
        """Start inhibiting sleep. Safe to call when already acquired."""

    def release(self) -> None:
        """Stop inhibiting sleep. Safe to call when not acquired."""


class _SubprocessBackend(KeepAwakeBackend):
    """Shared plumbing for back ends driven by a helper process.

    Every helper is wired so it dies with us. An orphaned inhibitor is the
    worst failure this app can have: the tray icon is gone, so the user has no
    way to notice or stop it, and the machine never sleeps again.
    """

    executable = ""
    #: When set, the helper inherits a pipe on stdin and exits on EOF — which
    #: the kernel delivers even if Espresso is SIGKILLed.
    exits_on_stdin_eof = False
    #: Seconds to wait for a helper to exit before escalating to SIGKILL.
    exit_timeout = 5

    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self.unavailable_reason = (
            None
            if self.executable and shutil.which(self.executable)
            else f"{self.executable or 'helper'} not found on PATH"
        )

    def build_command(self) -> list[str]:
        """The argv to run. Overridden per platform."""
        raise NotImplementedError

    def acquire(self) -> None:
        if not self.available or (self._process and self._process.poll() is None):
            return
        command = self.build_command()
        try:
            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE if self.exits_on_stdin_eof else subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_NO_WINDOW,
            )
        except OSError as exc:
            self.unavailable_reason = f"Could not start {self.executable}: {exc}"
            log.warning("%s", self.unavailable_reason)
            self._process = None
        else:
            log.info("Sleep inhibited via %s", " ".join(command))

    def release(self) -> None:
        process, self._process = self._process, None
        if process is None or process.poll() is not None:
            return
        if process.stdin is not None:
            with contextlib.suppress(OSError):
                process.stdin.close()
        process.terminate()
        try:
            process.wait(timeout=self.exit_timeout)
        except subprocess.TimeoutExpired:
            log.warning("%s did not exit; killing it", self.executable)
            process.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=self.exit_timeout)
        log.info("Sleep inhibitor released")


class MacKeepAwake(_SubprocessBackend):
    """macOS: ``caffeinate`` holds display, idle, disk and system assertions."""

    name = "caffeinate"
    executable = "caffeinate"

    def build_command(self) -> list[str]:
        # -w makes caffeinate exit when our PID does, so it cannot be orphaned.
        return [self.executable, "-d", "-i", "-m", "-s", "-w", str(os.getpid())]


class LinuxKeepAwake(_SubprocessBackend):
    """Linux: a blocking ``systemd-inhibit`` lock on idle and sleep."""

    name = "systemd-inhibit"
    executable = "systemd-inhibit"
    # systemd-inhibit holds the lock for as long as its child runs, and `cat`
    # exits the moment our end of its stdin pipe closes — including on a crash.
    exits_on_stdin_eof = True

    def build_command(self) -> list[str]:
        return [
            self.executable,
            "--what=idle:sleep",
            "--who=Espresso",
            "--why=User requested the system stay awake",
            "--mode=block",
            "cat",
        ]


class WindowsKeepAwake(KeepAwakeBackend):
    """Windows: ``SetThreadExecutionState`` on the calling thread."""

    name = "SetThreadExecutionState"

    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

    def __init__(self) -> None:
        self._kernel32 = None
        self.unavailable_reason = None
        try:
            import ctypes

            self._kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            self._kernel32.SetThreadExecutionState.restype = ctypes.c_uint
        except (ImportError, AttributeError, OSError) as exc:
            self.unavailable_reason = f"kernel32 unavailable: {exc}"

    def _set(self, flags: int) -> None:
        if self._kernel32 is None:
            return
        if self._kernel32.SetThreadExecutionState(flags) == 0:
            log.warning("SetThreadExecutionState(0x%X) failed", flags)

    def acquire(self) -> None:
        self._set(self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED | self.ES_DISPLAY_REQUIRED)
        log.info("Sleep inhibited via SetThreadExecutionState")

    def release(self) -> None:
        self._set(self.ES_CONTINUOUS)
        log.info("Sleep inhibitor released")


def create_backend(platform: str | None = None) -> KeepAwakeBackend:
    """Return the inhibitor for ``platform`` (defaults to :data:`sys.platform`)."""
    platform = platform or sys.platform
    if platform == "darwin":
        return MacKeepAwake()
    if platform == "win32":
        return WindowsKeepAwake()
    if platform.startswith("linux"):
        return LinuxKeepAwake()
    log.info("No keep-awake back end for platform %r", platform)
    return KeepAwakeBackend()
