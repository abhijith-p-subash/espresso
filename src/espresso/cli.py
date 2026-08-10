"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
import sys

from . import APP_NAME, __version__
from .config import MAX_INTERVAL, MIN_INTERVAL, MODES, Config, clamp_interval
from .logs import setup_logging
from .singleton import AlreadyRunningError, SingleInstance

log = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_ALREADY_RUNNING = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="espresso",
        description=f"{APP_NAME} — keep your computer awake from the system tray.",
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        metavar="SECONDS",
        help=(
            f"seconds between activity pulses ({MIN_INTERVAL}-{MAX_INTERVAL}); "
            "overrides the saved setting"
        ),
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=MODES,
        help=(
            "system: inhibit sleep only, needs no permissions (default); "
            "both: also simulate activity to keep chat presence green; "
            "activity: simulate keystrokes only"
        ),
    )
    parser.add_argument(
        "--paused",
        action="store_true",
        help="start in the paused state instead of immediately keeping awake",
    )
    parser.add_argument(
        "--allow-multiple",
        action="store_true",
        help="skip the single-instance check",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="verbosity for the log file and stderr",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="persist the options given on this run as the new defaults",
    )
    return parser


def apply_overrides(config: Config, args: argparse.Namespace) -> Config:
    """Layer command-line options over the saved configuration."""
    if args.interval is not None:
        config.interval = clamp_interval(args.interval, config.interval)
    if args.mode is not None:
        config.mode = args.mode
    if args.paused:
        config.start_active = False
    if args.log_level is not None:
        config.log_level = args.log_level
    return config


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    config = apply_overrides(Config.load(), args)
    log_path = setup_logging(config.log_level)
    log.info("%s %s starting on %s", APP_NAME, __version__, sys.platform)
    if log_path:
        log.debug("Logging to %s", log_path)
    if args.save and config.save():
        log.info("Saved current options as defaults")

    lock = SingleInstance()
    if not args.allow_multiple:
        try:
            lock.acquire()
        except AlreadyRunningError:
            log.error("%s is already running. Use --allow-multiple to override.", APP_NAME)
            return EXIT_ALREADY_RUNNING

    try:
        # Imported here so --version and --help work on headless machines,
        # where importing pystray fails for want of a display server.
        from .app import EspressoTray

        EspressoTray(config).run()
    except Exception:
        log.exception("%s exited with an unhandled error", APP_NAME)
        return EXIT_ERROR
    finally:
        lock.release()

    log.info("%s exited cleanly", APP_NAME)
    return EXIT_OK
