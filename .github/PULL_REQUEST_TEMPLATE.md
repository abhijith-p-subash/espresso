## What does this change?

<!-- A sentence or two. Link the issue if there is one: Fixes #123 -->

## Why?

<!-- What problem does it solve? Skip if it's obvious from the above. -->

## How was it tested?

<!-- Which platforms did you actually run it on? Automated tests can't
     verify tray behaviour, so manual checks matter here. -->

- [ ] `pytest` passes
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] Tested manually on: <!-- macOS / Windows / Linux -->

## Checklist

- [ ] `CHANGELOG.md` updated under **Unreleased**
- [ ] No new `print()` calls (windowed builds have no console — use the logger)
- [ ] Any new sleep inhibitor cannot outlive the process, including on `kill -9`
- [ ] `service.py` and its imports still don't depend on `pystray`
