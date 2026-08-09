import pytest

from espresso.singleton import AlreadyRunningError, SingleInstance


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


def test_lock_file_records_the_pid(tmp_path):
    import os

    path = tmp_path / "espresso.lock"
    with SingleInstance(path):
        assert path.read_text(encoding="ascii").strip() == str(os.getpid())


def test_release_without_acquire_is_safe(tmp_path):
    SingleInstance(tmp_path / "espresso.lock").release()


def test_unwritable_location_degrades_instead_of_raising(tmp_path):
    # No lock is taken, but the app must still be able to start.
    instance = SingleInstance(tmp_path / "missing" / "espresso.lock")
    instance.acquire()
    instance.release()
