"""PyInstaller entry point.

Frozen builds run this file directly rather than importing the package, so the
``src`` directory has to be on ``sys.path`` before ``espresso`` can be found.
Day-to-day, prefer ``python -m espresso`` or the ``espresso`` console script.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from espresso.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
