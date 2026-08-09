import pytest

from espresso.cli import EXIT_ALREADY_RUNNING, apply_overrides, build_parser, main
from espresso.config import MAX_INTERVAL, Config


def parse(*argv):
    return build_parser().parse_args(list(argv))


def test_defaults_leave_config_untouched():
    config = Config(interval=120, mode="system")
    assert apply_overrides(config, parse()) == Config(interval=120, mode="system")


def test_interval_override_is_clamped():
    config = apply_overrides(Config(), parse("--interval", "99999"))
    assert config.interval == MAX_INTERVAL


def test_mode_and_paused_overrides():
    config = apply_overrides(Config(), parse("-m", "activity", "--paused"))
    assert config.mode == "activity"
    assert config.start_active is False


def test_invalid_mode_is_rejected_by_the_parser():
    with pytest.raises(SystemExit):
        parse("--mode", "turbo")


def test_version_flag_exits_zero(capsys):
    with pytest.raises(SystemExit) as excinfo:
        parse("--version")
    assert excinfo.value.code == 0
    assert "Espresso" in capsys.readouterr().out


def test_second_instance_exits_with_its_own_code(monkeypatch, tmp_path):
    from espresso import cli, singleton

    monkeypatch.setattr(singleton, "lock_file", lambda: tmp_path / "espresso.lock")

    held = singleton.SingleInstance(tmp_path / "espresso.lock")
    held.acquire()
    try:
        monkeypatch.setattr(
            cli, "SingleInstance", lambda: singleton.SingleInstance(tmp_path / "espresso.lock")
        )
        assert main([]) == EXIT_ALREADY_RUNNING
    finally:
        held.release()
