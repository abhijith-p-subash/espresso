import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Must be set before pystray is imported anywhere: it picks its back end at
# import time and would otherwise need a real display server.
os.environ.setdefault("PYSTRAY_BACKEND", "dummy")


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    """Keep every test out of the real config/state directories."""
    from espresso import paths

    monkeypatch.setattr(paths, "config_dir", lambda: tmp_path / "config")
    monkeypatch.setattr(paths, "state_dir", lambda: tmp_path / "state")
    return tmp_path


class FakeBackend:
    """Records acquire/release so lifetime can be asserted."""

    name = "fake"
    unavailable_reason = None

    def __init__(self):
        self.acquired = 0
        self.released = 0

    @property
    def available(self):
        return True

    def acquire(self):
        self.acquired += 1

    def release(self):
        self.released += 1


class FakeSimulator:
    def __init__(self, works=True):
        self.pulses = 0
        self.works = works
        self.unavailable_reason = None

    @property
    def available(self):
        return self.works

    def pulse(self):
        self.pulses += 1
        return self.works


@pytest.fixture
def backend():
    return FakeBackend()


@pytest.fixture
def simulator():
    return FakeSimulator()
