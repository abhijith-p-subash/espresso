import os
import sys

import pytest

from espresso.singleton import AlreadyRunningError, SingleInstance

WINDOWS = sys.platform == "win32"


def test_lock_is_exclusive(tmp_path):
    path = tmp_path / "espresso.lock"
    first = SingleInstance(path)
    first.acquire()
    try:
        with pytest.raises(AlreadyRunningError):
            SingleInstance(path).acquire()
    finally:
        first.release()


def test_lock_is_reusable_after_release(tmp_path):
    path = tmp_path / "espresso.lock"
    with SingleInstance(path):
        pass
    with SingleInstance(path):
        pass


@pytest.mark.skipif(WINDOWS, reason="msvcrt locks are mandatory; see the test below")
def test_lock_file_records_the_pid(tmp_path):
    path = tmp_path / "espresso.lock"
    with SingleInstance(path):
        assert path.read_text(encoding="ascii").strip() == str(os.getpid())


@pytest.mark.skipif(not WINDOWS, reason="Windows-only locking semantics")
def test_windows_lock_denies_reads_while_held(tmp_path):
    """`msvcrt.locking` is mandatory, not advisory like POSIX `flock`.

    The locked byte is unreadable by *any* handle while held, so the PID we
    write is only useful for diagnostics on POSIX. Asserting it here keeps the
    difference documented rather than surprising.
    """
    path = tmp_path / "espresso.lock"
    with SingleInstance(path), pytest.raises(PermissionError):
        path.read_text(encoding="ascii")
    # ...and readable again once released.
    assert path.read_text(encoding="ascii").strip() == str(os.getpid())


def test_release_without_acquire_is_safe(tmp_path):
    SingleInstance(tmp_path / "espresso.lock").release()


def test_unwritable_location_degrades_instead_of_raising(tmp_path):
    # No lock is taken, but the app must still be able to start.
    instance = SingleInstance(tmp_path / "missing" / "espresso.lock")
    instance.acquire()
    instance.release()
