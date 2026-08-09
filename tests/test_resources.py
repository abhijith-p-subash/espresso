import sys

from espresso import resources


def test_assets_dir_resolves_in_a_source_checkout():
    assert resources.assets_dir().name == "assets"
    assert (resources.assets_dir() / "c5.png").exists()


def test_assets_dir_uses_meipass_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert resources.assets_dir() == tmp_path / "assets"


def test_base_icon_loads_rgba():
    icon = resources.base_icon()
    assert icon.mode == "RGBA"
    assert icon.size[0] > 0


def test_missing_asset_falls_back_to_drawn_icon(monkeypatch, tmp_path):
    monkeypatch.setattr(resources, "resource_path", lambda name: tmp_path / name)
    icon = resources.base_icon()
    assert icon.mode == "RGBA"
    assert icon.size == (resources.ICON_SIZE, resources.ICON_SIZE)


def test_idle_icon_is_dimmer_than_the_active_one():
    active = resources.base_icon()
    idle = resources.idle_icon(active)
    assert idle.size == active.size
    assert sum(idle.getchannel("A").tobytes()) < sum(active.getchannel("A").tobytes())
