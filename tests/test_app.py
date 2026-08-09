import pytest

from espresso.config import INTERVAL_PRESETS, Config
from espresso.service import KeepAwakeService

app = pytest.importorskip("espresso.app")


@pytest.fixture
def tray(backend, simulator, monkeypatch):
    monkeypatch.setattr(app, "needs_accessibility_grant", lambda: False)
    config = Config(interval=60, mode="both", start_active=False)
    service = KeepAwakeService(config, backend=backend, simulator=simulator)
    instance = app.EspressoTray(config, service=service)
    yield instance
    instance.service.stop()


def labels(menu):
    return [str(item.text) for item in menu.items]


def find(menu, prefix):
    for item in menu.items:
        if str(item.text).startswith(prefix):
            return item
    raise AssertionError(f"no menu item starting with {prefix!r} in {labels(menu)}")


def test_menu_has_the_expected_entries(tray):
    text = " | ".join(labels(tray.icon.menu))
    for expected in ("Keep awake", "Interval", "Mode", "Open log file", "Quit"):
        assert expected in text


def test_status_line_tracks_state(tray):
    assert "Paused" in tray._status_text()
    tray.service.start()
    assert "Awake" in tray._status_text()


def test_status_line_reports_the_interval(tray):
    tray.service.config.interval = 300
    tray.service.start()
    assert "5 min" in tray._status_text()


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(30, "30 sec"), (60, "1 min"), (120, "2 min"), (600, "10 min"), (45, "45 sec")],
)
def test_interval_formatting(seconds, expected):
    assert app._format_interval(seconds) == expected


def test_toggle_item_starts_and_stops_the_service(tray, backend):
    item = find(tray.icon.menu, "Keep awake")
    item(tray.icon)
    assert tray.service.is_active
    assert backend.acquired == 1
    item(tray.icon)
    assert not tray.service.is_active
    assert backend.released == 1


def test_toggle_item_checked_state_follows_the_service(tray):
    item = find(tray.icon.menu, "Keep awake")
    assert item.checked is False
    tray.service.start()
    assert item.checked is True


def test_interval_submenu_covers_every_preset(tray):
    submenu = find(tray.icon.menu, "Interval").submenu
    assert len(submenu.items) == len(INTERVAL_PRESETS)


def test_choosing_an_interval_updates_the_config(tray):
    submenu = find(tray.icon.menu, "Interval").submenu
    submenu.items[-1](tray.icon)
    assert tray.config.interval == INTERVAL_PRESETS[-1]


def test_exactly_one_interval_is_checked(tray):
    submenu = find(tray.icon.menu, "Interval").submenu
    assert sum(1 for item in submenu.items if item.checked) == 1


def test_choosing_a_mode_updates_the_config(tray):
    submenu = find(tray.icon.menu, "Mode").submenu
    for item in submenu.items:
        if "Prevent sleep only" in str(item.text):
            item(tray.icon)
    assert tray.config.mode == "system"


def test_changing_the_interval_restarts_a_running_service(tray, backend):
    tray.service.start()
    assert backend.acquired == 1
    tray.service.set_interval(120)
    assert tray.service.is_active
    assert backend.acquired == 2
    assert backend.released == 1


def test_refresh_swaps_the_icon_image(tray):
    tray.refresh()
    assert tray.icon.icon is tray._idle_image
    tray.service.start()
    tray.refresh()
    assert tray.icon.icon is tray._active_image
    assert "awake" in tray.icon.title


def test_refresh_updates_the_menu(tray, monkeypatch):
    """Without this call the status line goes stale on macOS."""
    calls = []
    monkeypatch.setattr(tray.icon, "update_menu", lambda: calls.append(1))
    tray.refresh()
    assert calls == [1]


def test_refresh_survives_a_broken_icon(tray, monkeypatch):
    def boom():
        raise RuntimeError("tray gone")

    monkeypatch.setattr(tray.icon, "update_menu", boom)
    tray.refresh()  # must not raise


def test_service_state_changes_refresh_the_tray(tray, monkeypatch):
    calls = []
    monkeypatch.setattr(tray.icon, "update_menu", lambda: calls.append(1))
    tray.service.start()
    tray.service.stop()
    assert len(calls) >= 2


def test_quit_stops_the_service_and_the_icon(tray, backend, monkeypatch):
    stopped = []
    monkeypatch.setattr(tray.icon, "stop", lambda: stopped.append(1))
    tray.service.start()
    tray._on_quit()
    assert not tray.service.is_active
    assert backend.released == 1
    assert stopped == [1]


def test_accessibility_warning_hidden_when_permission_is_granted(tray):
    assert tray._warning_visible() is False


def test_accessibility_warning_shown_when_permission_is_missing(tray, monkeypatch):
    monkeypatch.setattr(app, "needs_accessibility_grant", lambda: True)
    assert tray._warning_visible() is True


def test_accessibility_warning_hidden_in_system_only_mode(tray, monkeypatch):
    monkeypatch.setattr(app, "needs_accessibility_grant", lambda: True)
    tray.config.mode = "system"
    assert tray._warning_visible() is False
