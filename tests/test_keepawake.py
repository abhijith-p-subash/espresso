import os

import pytest

from espresso import keepawake
from espresso.keepawake import (
    KeepAwakeBackend,
    LinuxKeepAwake,
    MacKeepAwake,
    WindowsKeepAwake,
    create_backend,
)


@pytest.mark.parametrize(
    ("platform", "expected"),
    [
        ("darwin", MacKeepAwake),
        ("win32", WindowsKeepAwake),
        ("linux", LinuxKeepAwake),
        ("linux2", LinuxKeepAwake),
        ("freebsd13", KeepAwakeBackend),
    ],
)
def test_backend_selection(platform, expected, monkeypatch):
    monkeypatch.setattr(keepawake.shutil, "which", lambda _cmd: "/usr/bin/stub")
    monkeypatch.setattr(WindowsKeepAwake, "__init__", lambda _self: None)
    assert type(create_backend(platform)) is expected


def test_null_backend_is_inert_and_reports_why():
    backend = KeepAwakeBackend()
    assert not backend.available
    assert backend.unavailable_reason
    backend.acquire()
    backend.release()  # must not raise


def test_missing_helper_marks_backend_unavailable(monkeypatch):
    monkeypatch.setattr(keepawake.shutil, "which", lambda _cmd: None)
    backend = MacKeepAwake()
    assert not backend.available
    assert "caffeinate" in backend.unavailable_reason


def test_unavailable_backend_never_spawns_a_process(monkeypatch):
    monkeypatch.setattr(keepawake.shutil, "which", lambda _cmd: None)

    def fail(*args, **kwargs):
        raise AssertionError("Popen must not be called")

    monkeypatch.setattr(keepawake.subprocess, "Popen", fail)
    backend = LinuxKeepAwake()
    backend.acquire()
    backend.release()


class FakeStdin:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeProcess:
    def __init__(self, stdin=None):
        self.terminated = False
        self.killed = False
        self.stdin = stdin
        self._alive = True

    def poll(self):
        return None if self._alive else 0

    def terminate(self):
        self.terminated = True
        self._alive = False

    def kill(self):
        self.killed = True
        self._alive = False

    def wait(self, timeout=None):
        return 0


def test_acquire_release_lifecycle(monkeypatch):
    monkeypatch.setattr(keepawake.shutil, "which", lambda _cmd: "/usr/bin/caffeinate")
    spawned = []

    def fake_popen(cmd, **kwargs):
        spawned.append(cmd)
        return FakeProcess()

    monkeypatch.setattr(keepawake.subprocess, "Popen", fake_popen)

    backend = MacKeepAwake()
    backend.acquire()
    assert spawned == [backend.build_command()]

    # A second acquire must not stack a duplicate helper process.
    backend.acquire()
    assert len(spawned) == 1

    process = backend._process
    backend.release()
    assert process.terminated
    backend.release()  # idempotent


def test_caffeinate_is_tied_to_our_pid():
    # Without -w, a hard kill of Espresso would leave the Mac awake forever.
    command = MacKeepAwake.build_command(MacKeepAwake.__new__(MacKeepAwake))
    assert command[-2:] == ["-w", str(os.getpid())]


def test_linux_helper_exits_when_our_stdin_closes(monkeypatch):
    monkeypatch.setattr(keepawake.shutil, "which", lambda _cmd: "/usr/bin/systemd-inhibit")
    stdin = FakeStdin()
    captured = {}

    def fake_popen(cmd, **kwargs):
        captured.update(kwargs)
        return FakeProcess(stdin=stdin)

    monkeypatch.setattr(keepawake.subprocess, "Popen", fake_popen)
    backend = LinuxKeepAwake()
    backend.acquire()
    assert captured["stdin"] is keepawake.subprocess.PIPE
    backend.release()
    assert stdin.closed


def test_popen_failure_is_reported_not_raised(monkeypatch):
    monkeypatch.setattr(keepawake.shutil, "which", lambda _cmd: "/usr/bin/caffeinate")

    def boom(*args, **kwargs):
        raise OSError("no fork for you")

    monkeypatch.setattr(keepawake.subprocess, "Popen", boom)
    backend = MacKeepAwake()
    backend.acquire()
    assert not backend.available
    backend.release()


def test_stuck_helper_is_killed(monkeypatch):
    monkeypatch.setattr(keepawake.shutil, "which", lambda _cmd: "/usr/bin/caffeinate")

    class StuckProcess(FakeProcess):
        def __init__(self):
            super().__init__()
            self._waits = 0

        def terminate(self):
            self.terminated = True  # ignores SIGTERM

        def wait(self, timeout=None):
            self._waits += 1
            if self._waits == 1:
                raise keepawake.subprocess.TimeoutExpired("caffeinate", timeout)
            return 0

    process = StuckProcess()
    monkeypatch.setattr(keepawake.subprocess, "Popen", lambda *_a, **_k: process)
    backend = MacKeepAwake()
    backend.acquire()
    backend.release()
    assert process.killed
