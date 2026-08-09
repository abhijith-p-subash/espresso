# Contributing to Espresso

Thanks for taking the time. Bug reports, fixes and ideas are all welcome.

## Getting set up

```bash
git clone https://github.com/abhijith-p-subash/espresso.git
cd espresso

python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

pip install -e ".[dev]"
```

Run it from source:

```bash
python -m espresso --log-level DEBUG
```

## Before you open a PR

```bash
pytest                      # the full suite, ~1s
ruff check .                # lint
ruff format --check .       # formatting
```

All three run in CI on macOS, Windows and Linux, so it is cheapest to run them
locally first.

## How the code is organised

The one rule worth knowing: **`service.py` and everything it imports must not
import `pystray`.** The keep-awake engine is deliberately UI-free so it can be
tested on a headless CI runner. `app.py` is the only module that touches the
tray, and `cli.py` imports it lazily so `--help` and `--version` work without a
display server.

| Module | Responsibility |
| --- | --- |
| `app.py` | Tray icon, menu, lifecycle |
| `service.py` | The keep-awake loop |
| `keepawake.py` | Per-platform sleep inhibitors |
| `activity.py` | Synthetic keystrokes |
| `signals.py` | Signal delivery across native GUI loops |
| `singleton.py` | Single-instance lock |
| `config.py` / `paths.py` | Settings and where they live |
| `permissions.py` | macOS Accessibility checks |
| `resources.py` / `logs.py` | Icons and logging |

## Things to be careful about

These are the traps this codebase has already fallen into once.

**Never leave an inhibitor running.** Every helper must die with Espresso, even
on `kill -9`. macOS uses `caffeinate -w <pid>`; Linux gives `systemd-inhibit` a
child that exits when our stdin pipe closes; Windows' execution state is
per-thread and cleared on exit. An orphaned inhibitor is invisible to the user
and keeps their machine awake forever. If you add a back end, prove it cannot
be orphaned.

**The Windows back end is thread-bound.** `SetThreadExecutionState` applies to
the calling thread only, so acquire and release must happen on the *same*
long-lived thread. The worker in `service.py` does this in its own
`try`/`finally`; don't move it to the main thread.

**Call `icon.update_menu()` after any state change.** pystray builds the native
menu once on several back ends, so dynamic labels and check marks go stale
otherwise. This is what `EspressoTray.refresh()` is for.

**Don't use `print()`.** Windowed builds have no console — `sys.stdout` is
`None` and output vanishes. Use the module logger.

**Don't rely on plain `signal.signal()` to interrupt the tray.** CPython only
dispatches handlers between bytecodes, and the main thread is parked inside
`NSApplication.run()`. `signals.py` exists specifically to solve this; use it.

## Tests

`pytest` must pass without a display server. If you need pystray in a test,
`tests/conftest.py` already forces `PYSTRAY_BACKEND=dummy`.

Prefer testing behaviour over implementation, and give tests names that state
the expectation — `test_stop_is_prompt_even_with_a_long_interval` beats
`test_stop_2`.

## Commit messages

Short imperative subject line, and explain *why* in the body when it isn't
obvious. Conventional-commit prefixes (`fix:`, `feat:`, `docs:`) are welcome
but not required.

## Releasing (maintainers)

1. Bump `__version__` in `src/espresso/__init__.py`. That is the only place a
   version number is written — `pyproject.toml` and `Espresso.spec` both read
   it from there.
2. Move the `Unreleased` entries in `CHANGELOG.md` under the new version, and
   update the link definitions at the bottom.
3. Commit, then tag and push:

   ```bash
   git commit -am "Release v1.2.0"
   git push
   git tag v1.2.0
   git push origin v1.2.0
   ```

Pushing a `v*` tag triggers `.github/workflows/release.yml`, which builds on
macOS, Windows and Linux runners and attaches the three zips to a new GitHub
release. The tag must match the version in `__init__.py` — nothing enforces
this, so check it before tagging.

If a build fails, delete the tag (`git push --delete origin v1.2.0`), fix the
problem, and re-tag. You can also re-run the workflow by hand from the Actions
tab via `workflow_dispatch`.
