# Contributing to Espresso

Thanks for taking the time. Bug reports, fixes and ideas are all welcome.

Espresso is small, so don't overthink it: for a typo or an obvious bug, just
open a PR. For anything that changes behaviour or adds a dependency, open an
issue first so we can agree on the shape before you write code.

> Maintainer publishing a version? That lives in [RELEASING.md](RELEASING.md).

## Getting set up

```bash
# Fork the repo on GitHub first, then clone your fork
git clone https://github.com/<your-username>/espresso.git
cd espresso
git remote add upstream https://github.com/abhijith-p-subash/espresso.git

python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

pip install -e ".[dev]"
```

Run it from source:

```bash
python -m espresso --log-level DEBUG
```

On Linux you also need a tray implementation — `gir1.2-appindicator3-0.1`
(Debian/Ubuntu) or `libappindicator-gtk3` (Fedora).

## Opening a pull request

### 1. Branch from an up-to-date master

```bash
git checkout master
git pull upstream master
git checkout -b fix/tray-icon-flicker
```

Use a short, descriptive branch name. `fix/`, `feat/` and `docs/` prefixes are
nice but not required.

### 2. Make your change

Keep it focused — one problem per PR. A PR that fixes a bug *and* reformats
half the codebase is hard to review and hard to revert.

Add or update tests for anything you change. If you fix a bug, the ideal PR has
a test that fails before your fix and passes after it.

Update `CHANGELOG.md` under **Unreleased** if the change is user-visible.

### 3. Check it locally

```bash
make check          # lint + tests, exactly what CI runs
```

Or individually:

```bash
pytest                      # the full suite, ~1s
ruff check .                # lint
ruff format .               # auto-fix formatting
```

CI runs all of this on macOS, Windows and Linux, so it is much cheaper to catch
problems here first.

### 4. Commit and push

```bash
git add -A
git commit -m "Stop the tray icon flickering on state change"
git push -u origin fix/tray-icon-flicker
```

Short imperative subject line, and explain *why* in the body when it isn't
obvious from the diff. Conventional-commit prefixes (`fix:`, `feat:`, `docs:`)
are welcome but not required.

### 5. Open the PR

Push prints a link, or use the "Compare & pull request" banner on GitHub. Target
`master`. Fill in the template — especially **which platforms you tested on**,
since no automated test can verify that a tray icon actually appears and
behaves.

Then watch CI. A red build is expected sometimes; push a follow-up commit to the
same branch and the PR updates itself.

### Keeping your branch current

If `master` moves while your PR is open:

```bash
git fetch upstream
git rebase upstream/master
git push --force-with-lease
```

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

**Watch the memory.** This is a background app people leave running all day.
Tray artwork is deliberately small — a 1280×1280 PNG once cost 6.2 MB of RAM
per decoded copy for pixels no tray can display.

## Tests

`pytest` must pass without a display server. If you need pystray in a test,
`tests/conftest.py` already forces `PYSTRAY_BACKEND=dummy`.

Prefer testing behaviour over implementation, and give tests names that state
the expectation — `test_stop_is_prompt_even_with_a_long_interval` beats
`test_stop_2`.

Platform-specific behaviour deserves a platform-specific test rather than a
blanket skip. POSIX and Windows file locking differ in a way that matters, so
`tests/test_singleton.py` asserts the correct thing on each instead of switching
itself off on Windows.

## Manual testing

Automated tests cannot see a tray icon. Before marking a PR ready, run the app
and check:

- The icon appears, and dims when you pause it
- The menu opens, and the status line updates after Start/Stop
- Interval and Mode changes take effect and survive a restart
- Quit exits cleanly and releases the inhibitor
  (macOS: `pmset -g assertions`; Linux: `systemd-inhibit --list`)
