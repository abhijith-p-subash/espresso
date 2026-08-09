# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/abhijith-p-subash/espresso/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/abhijith-p-subash/espresso/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/abhijith-p-subash/espresso/releases/tag/v1.0.0
