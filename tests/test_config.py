import json

import pytest

from espresso.config import (
    MAX_INTERVAL,
    MIN_INTERVAL,
    Config,
    clamp_interval,
    normalize_mode,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, MIN_INTERVAL),
        (-10, MIN_INTERVAL),
        (10**9, MAX_INTERVAL),
        (45, 45),
        ("90", 90),
        (None, 60),
        ("nonsense", 60),
    ],
)
def test_clamp_interval(value, expected):
    assert clamp_interval(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("both", "both"), ("SYSTEM", "system"), ("activity", "activity"), ("nope", "both")],
)
def test_normalize_mode(value, expected):
    assert normalize_mode(value) == expected


def test_mode_properties():
    assert Config(mode="both").inhibits_system
    assert Config(mode="both").simulates_activity
    assert Config(mode="system").inhibits_system
    assert not Config(mode="system").simulates_activity
    assert not Config(mode="activity").inhibits_system
    assert Config(mode="activity").simulates_activity


def test_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    Config(interval=120, mode="system", start_active=False).save(path)
    loaded = Config.load(path)
    assert (loaded.interval, loaded.mode, loaded.start_active) == (120, "system", False)


def test_missing_file_yields_defaults(tmp_path):
    assert Config.load(tmp_path / "absent.json") == Config()


def test_corrupt_file_yields_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    assert Config.load(path) == Config()


def test_non_object_json_yields_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert Config.load(path) == Config()


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"interval": 90, "legacy_option": True}), encoding="utf-8")
    assert Config.load(path).interval == 90


def test_out_of_range_values_are_repaired(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"interval": -5, "mode": "turbo"}), encoding="utf-8")
    loaded = Config.load(path)
    assert loaded.interval == MIN_INTERVAL
    assert loaded.mode == "both"


def test_save_leaves_no_temp_file(tmp_path):
    path = tmp_path / "config.json"
    Config().save(path)
    assert [p.name for p in tmp_path.iterdir()] == ["config.json"]


def test_save_to_unwritable_location_returns_false(tmp_path):
    assert Config().save(tmp_path / "missing-dir" / "config.json") is False
