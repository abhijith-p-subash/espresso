<div align="center">

<img src="assets/c5.png" alt="Espresso" width="96">

# Espresso ☕️

**Keep your computer awake. From the menu bar, in one click.**

[![CI](https://github.com/abhijith-p-subash/espresso/actions/workflows/ci.yml/badge.svg)](https://github.com/abhijith-p-subash/espresso/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](#installation)

</div>

---

Espresso stops your machine from sleeping, dimming, or showing you as "away"
while a build runs, a download finishes, or a presentation plays. It lives in
the system tray, uses almost no CPU, and gets out of the way.

## Why not just move the mouse every minute?

Because faking input and staying awake are two different problems, and most
"keep awake" scripts only solve half of one:

|                                    | Synthetic keystroke | OS power assertion |
| ---------------------------------- | :-----------------: | :----------------: |
| Stops the screen from sleeping     |     unreliable      |         ✅         |
| Stops the system from suspending   |         ❌          |         ✅         |
| Keeps chat presence "available"    |         ✅          |         ❌         |
| Works when the screen is locked    |         ❌          |         ✅         |

Sleep is governed by the OS power manager, which is free to ignore synthetic
input — and on macOS it will, unless you have granted Accessibility access.
Presence indicators, meanwhile, watch the *input idle timer*, which a power
assertion does not touch.

So Espresso does both, and lets you pick:

| Mode | What it does | Use it when |
| --- | --- | --- |
| **Sleep + activity** (default) | Power assertion **and** a keystroke | You want the obvious thing |
| **Prevent sleep only** | Power assertion, no synthetic input | You'd rather not grant input permissions |
| **Simulate activity only** | A keystroke every interval | You only care about looking "available" |

Under the hood it uses each platform's supported mechanism:

| Platform | Mechanism |
| --- | --- |
| macOS   | `caffeinate -dims`, tied to Espresso's PID |
| Windows | `SetThreadExecutionState` with `ES_SYSTEM_REQUIRED \| ES_DISPLAY_REQUIRED` |
| Linux   | `systemd-inhibit --what=idle:sleep --mode=block` |

The simulated keystroke is **F15** — a real key in the HID tables that no
mainstream keyboard has and no desktop binds by default, so it cannot type into
your documents or trigger a shortcut.

## Features

- 🖥️ Lives in the system tray on macOS, Windows and Linux
- ⚡ Real OS-level sleep inhibition, not just fake input
- ⏱️ Adjustable interval — 30 s to 10 min — from the menu
- 🎛️ Three modes, switchable at runtime
- 💾 Settings persist between launches
- 🔒 Single-instance lock, so you never leave a forgotten copy holding your machine awake
- 🧹 Releases everything on exit — including after a crash or `kill -9`
- 📋 Logs to a file, so a windowed build can still be debugged

## Installation

### Pre-built binaries

Grab the latest from [Releases](https://github.com/abhijith-p-subash/espresso/releases/latest):

| Platform | File |
| --- | --- |
| Windows | `Espresso-windows.zip` |
| macOS   | `Espresso-macos.zip` |
| Linux   | `Espresso-linux.zip` |

> **macOS**: the app is unsigned, so the first launch needs
> **System Settings → Privacy & Security → Open Anyway**. For the
> *Sleep + activity* and *Simulate activity only* modes, also grant
> **Privacy & Security → Accessibility**; without it macOS silently discards
> the keystrokes. Espresso detects this and offers a menu shortcut to the
> right settings pane.

### From source

```bash
git clone https://github.com/abhijith-p-subash/espresso.git
cd espresso

python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

pip install -e .
espresso
```

On Linux you also need a tray implementation — `gir1.2-appindicator3-0.1`
(Debian/Ubuntu) or `libappindicator-gtk3` (Fedora) — plus a
`systemd`-based session for sleep inhibition.

## Usage

Launch it and a cup appears in your tray. Click it:

```
● Awake — every 1 min (last pulse 12s ago)
─────────────────────────────
✓ Keep awake
  Interval  ▸   30 sec · 1 min · 2 min · 5 min · 10 min
  Mode      ▸   Sleep + activity · Prevent sleep only · Simulate activity only
─────────────────────────────
  Open log file
  Espresso v1.1.0
─────────────────────────────
  Quit
```

The icon is full colour while awake and dimmed while paused, so you can tell
at a glance without opening the menu.

### Command line

```bash
espresso                        # start keeping awake immediately
espresso --paused               # start in the tray, but idle
espresso -i 300 -m system       # 5-minute interval, no synthetic input
espresso -i 300 -m system --save   # ...and remember it as the default
espresso --log-level DEBUG
```

| Flag | Meaning |
| --- | --- |
| `-i`, `--interval SECONDS` | Seconds between pulses (5–3600) |
| `-m`, `--mode {both,system,activity}` | Which mechanism to use |
| `--paused` | Start idle instead of active |
| `--save` | Persist this run's options as the defaults |
| `--allow-multiple` | Skip the single-instance check |
| `--log-level {DEBUG,INFO,WARNING,ERROR}` | Verbosity |

Exit codes: `0` clean, `1` unhandled error, `2` another instance is running.

### Files

| | macOS | Windows | Linux |
| --- | --- | --- | --- |
| Config | `~/Library/Application Support/Espresso/config.json` | `%APPDATA%\Espresso\config.json` | `~/.config/espresso/config.json` |
| Log | `~/Library/Logs/Espresso/espresso.log` | `%LOCALAPPDATA%\Espresso\espresso.log` | `~/.local/state/espresso/espresso.log` |

## Building

```bash
pip install -e ".[build]"
pyinstaller Espresso.spec --noconfirm
```

Output lands in `dist/` — `Espresso.app` on macOS, `Espresso.exe` on Windows,
`Espresso` on Linux. The spec is committed, so every platform builds the same
way; it sets `LSUIElement` on macOS so the app stays out of the Dock.

## Project layout

```
espresso/
├── src/espresso/
│   ├── app.py          # tray icon, menu, lifecycle
│   ├── service.py      # the keep-awake engine (no UI)
│   ├── keepawake.py    # per-platform sleep inhibitors
│   ├── activity.py     # synthetic keystrokes
│   ├── signals.py      # Ctrl-C/SIGTERM across native GUI loops
│   ├── singleton.py    # single-instance lock
│   ├── config.py       # persisted settings
│   ├── permissions.py  # macOS Accessibility checks
│   ├── paths.py        # per-platform config/state/log locations
│   ├── resources.py    # icon loading and rendering
│   ├── logs.py         # rotating file logging
│   └── cli.py          # argument parsing, entry point
├── tests/
├── assets/
└── Espresso.spec
```

`service.py` has no UI dependency, which is what makes the interesting parts —
start/stop races, inhibitor lifetime, mode switching — testable without a
display server.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev
setup, and please read the [Code of Conduct](CODE_OF_CONDUCT.md).

```bash
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

## License

[MIT](LICENSE) © Abhijith P Subash
