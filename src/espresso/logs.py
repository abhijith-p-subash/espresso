"""Logging setup.

Windowed builds have no console — ``sys.stdout`` is ``None`` and ``print()``
silently discards everything. Everything therefore goes to a rotating file, and
to stderr only when a stream actually exists.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .paths import log_file

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_MAX_BYTES = 512 * 1024
_BACKUPS = 2

#: At DEBUG these libraries drown out our own messages — PIL alone logs every
#: PNG chunk it decodes — so they are pinned regardless of the chosen level.
_NOISY_LIBRARIES = ("PIL", "pystray", "pynput")


def setup_logging(level: str = "INFO", path: Path | None = None) -> Path | None:
    """Configure the root logger. Returns the log file path, if one was opened."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(_FORMAT)
    destination: Path | None = path or log_file()
    try:
        file_handler = RotatingFileHandler(
            destination, maxBytes=_MAX_BYTES, backupCount=_BACKUPS, encoding="utf-8"
        )
    except OSError:
        destination = None
    else:
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    if sys.stderr is not None:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    if not root.handlers:
        root.addHandler(logging.NullHandler())

    for name in _NOISY_LIBRARIES:
        logging.getLogger(name).setLevel(logging.WARNING)

    return destination
