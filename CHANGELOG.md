# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.2.0] - 2026-08-10

Quieter and lighter. Espresso now runs with no permissions on any platform out
of the box, and uses less memory than v1.0.1 did.

### Upgrade note

**If you relied on Espresso keeping your chat presence green, switch the mode
back.** The default no longer simulates keystrokes. Open the tray menu →
**Mode** → **Sleep + activity**. Saved settings are untouched, so this only
affects installs that never changed the mode.

### Changed

- **The default mode is now `system`** (prevent sleep only), which requires no
  permissions on any platform. Espresso now works out of the box with no macOS
  Accessibility prompt; keystroke simulation is opt-in from the tray menu.
- **Builds are onedir on every platform**, not just macOS. A onefile executable
  unpacked its whole ~36 MB payload to a temp directory on every launch, which
  is slow and is one of the patterns antivirus heuristics flag most readily.
  Windows and Linux releases are now a folder containing the executable.
- Tray artwork reduced from 1280×1280 to 256×256, and scaled to 64 px on load.
  A tray icon renders at 22–44 px; the original cost 6.2 MB of RAM per decoded
  copy, and two are held. Resident memory dropped from ~103 MB to ~80 MB —
  below the ~93 MB of v1.0.1. The full-size artwork is kept as
  `assets/c5-source.png` for regenerating the `.icns` and `.ico`.

### Fixed

- Windows lock-file test assumed POSIX semantics. `msvcrt.locking` is mandatory
  rather than advisory, so the file cannot be read while the lock is held.

## [1.1.0] - 2026-08-09

The headline: Espresso now actually prevents your computer from sleeping.
Before this release it only simulated a keystroke, which keeps chat presence
alive but does not stop the OS power manager from suspending the machine.

### Added

- Real per-platform sleep inhibition: `caffeinate` on macOS,
  `SetThreadExecutionState` on Windows, `systemd-inhibit` on Linux.
- Three modes — *Sleep + activity*, *Prevent sleep only*, *Simulate activity
  only* — switchable from the tray menu.
- Adjustable interval (30 s to 10 min) from the tray menu.
- Settings persisted to a per-platform config file, plus a `--save` flag.
- Command-line interface: `--interval`, `--mode`, `--paused`, `--log-level`,
  `--allow-multiple`, `--version`.
- Single-instance lock, so a forgotten second copy cannot silently hold the
  machine awake.
- Rotating file logging, and an "Open log file" menu entry.
- Detection of missing macOS Accessibility permission, with a menu shortcut to
  the relevant settings pane.
- Distinct active and paused tray icons.
- Test suite (101 tests) that runs headless on all three platforms, and CI.

### Fixed

- **The tray status line never updated.** pystray builds its menu once on
  several back ends, so the indicator added in 1.0.0 kept reporting the state
  at launch. `icon.update_menu()` is now called on every state change.
- **Ctrl-C and SIGTERM did not quit the app.** CPython dispatches signal
  handlers between bytecodes, but the main thread sits inside
  `NSApplication.run()`, so they were received and never acted on. Signals now
  arrive over `signal.set_wakeup_fd` and are handled on a dedicated thread.
- **`requirements.txt` could not be installed on Windows or Linux.** The
  macOS-only PyObjC pins now carry environment markers.
- **Diagnostics were silently discarded in released builds.** Windowed
  executables have no console, so every `print()` went nowhere.
- **A crash could leave the machine awake forever.** Helper processes are now
  tied to Espresso's lifetime and cannot be orphaned, even by `kill -9`.
- A missing or unreadable icon asset no longer crashes startup; a fallback icon
  is drawn instead.
- A corrupt config file no longer prevents the app from starting.
- `platform.system()` was queried but never used; platform handling is now real.

### Changed

- Split the single `main.py` into a tested `espresso` package. The keep-awake
  engine has no UI dependency and runs headless.
- The macOS bundle sets `LSUIElement`, so a tray-only app no longer takes a
  Dock slot, and now carries an icon and a bundle identifier.
- `Espresso.spec` is committed instead of gitignored, so builds are
  reproducible across platforms.
- UPX compression disabled — it mangles macOS and Windows signatures.

## [1.0.0] - 2025-10-01

### Added

- Initial release: tray icon with Start/Stop/Quit, F15 keystroke simulation,
  PyInstaller builds for Windows, macOS and Linux.

[Unreleased]: https://github.com/abhijith-p-subash/espresso/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/abhijith-p-subash/espresso/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/abhijith-p-subash/espresso/compare/v1.0.1...v1.1.0
[1.0.0]: https://github.com/abhijith-p-subash/espresso/releases/tag/v1.0.0
