import logging

from espresso.logs import setup_logging


def test_writes_to_the_given_file(tmp_path):
    path = tmp_path / "espresso.log"
    assert setup_logging("DEBUG", path) == path
    logging.getLogger("espresso.test").info("hello from the test")
    logging.shutdown()
    assert "hello from the test" in path.read_text(encoding="utf-8")


def test_unknown_level_falls_back_to_info(tmp_path):
    setup_logging("NONSENSE", tmp_path / "espresso.log")
    assert logging.getLogger().level == logging.INFO


def test_repeated_setup_does_not_duplicate_handlers(tmp_path):
    path = tmp_path / "espresso.log"
    setup_logging("INFO", path)
    first = len(logging.getLogger().handlers)
    setup_logging("INFO", path)
    assert len(logging.getLogger().handlers) == first


def test_survives_an_unwritable_log_path(tmp_path):
    assert setup_logging("INFO", tmp_path / "missing" / "espresso.log") is None
    logging.getLogger("espresso.test").info("still works")
