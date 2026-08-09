"""A single-instance lock.

Two copies of Espresso means two tray icons and two inhibitors, where stopping
one leaves the other silently holding the machine awake. An advisory lock on a
file in the state directory is enough: the OS releases it when the process
dies, so a crash cannot leave a stale lock behind.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
from pathlib import Path
from types import TracebackType

from .paths import lock_file

log = logging.getLogger(__name__)


class AlreadyRunningError(RuntimeError):
    """Raised when another instance already holds the lock."""


class SingleInstance:
    """Context manager holding an exclusive advisory lock on a file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or lock_file()
        self._fd: int | None = None

    def acquire(self) -> None:
        try:
            fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        except OSError as exc:
            # An unwritable state dir should not block the app; skip locking.
            log.warning("Could not open lock file %s (%s); skipping lock", self.path, exc)
            return

        try:
            self._lock(fd)
        except OSError as exc:
            os.close(fd)
            raise AlreadyRunningError(
                f"Another {__package__} instance is already running"
            ) from exc

        self._fd = fd
        os.truncate(fd, 0)
        os.write(fd, str(os.getpid()).encode("ascii"))
        with contextlib.suppress(OSError):
            os.fsync(fd)

    @staticmethod
    def _lock(fd: int) -> None:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def release(self) -> None:
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError as exc:
            log.debug("Could not unlock %s: %s", self.path, exc)
        finally:
            os.close(fd)

    def __enter__(self) -> SingleInstance:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()
