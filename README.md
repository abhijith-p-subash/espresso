<div align="center">

<img src="assets/c5.png" alt="Espresso" width="96">

# Espresso ☕️

**Keep your computer awake. From the menu bar, in one click.**

[![CI](https://github.com/abhijith-p-subash/espresso/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/abhijith-p-subash/espresso/actions/workflows/ci.yml)
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

| Mode | What it does | Permissions |
| --- | --- | --- |
| **Prevent sleep only** (default) | Power assertion, no synthetic input | **None, on any OS** |
| **Sleep + activity** | Power assertion **and** a keystroke | macOS Accessibility |
| **Simulate activity only** | A keystroke every interval | macOS Accessibility |

The default is deliberately the one that needs nothing granted: Espresso keeps
your machine awake out of the box without a single permission prompt. Switch
modes from the tray menu if you also want chat presence kept green.

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

| Platform | File | Unzip, then run |
| --- | --- | --- |
| Windows | `Espresso-windows.zip` | `Espresso\Espresso.exe` |
| macOS   | `Espresso-macos.zip`   | `Espresso.app` |
| Linux   | `Espresso-linux.zip`   | `Espresso/Espresso` |

There is no installer. Unzip anywhere and run it — Espresso writes nothing
outside its config and log files.

<details>
<summary><b>Why does my OS warn me about this download?</b></summary>

Because the binaries are **not code-signed**. Signing costs money and identity
verification, and this is a free side project — see
[Code signing](RELEASING.md#code-signing) for where that stands.

The warning is about *provenance*, not behaviour: your OS is saying "I can't
verify who published this", not "this does something dangerous". Every
unsigned download gets the same treatment, and building from source yourself
produces no warning at all.

- **Windows** — SmartScreen shows a blue "Windows protected your PC" screen.
  Click **More info → Run anyway**. The warning appears because the file was
  downloaded from the internet; the same binary built locally is silent.
- **macOS** — right-click the app → **Open**, or go to
  **System Settings → Privacy & Security → Open Anyway**.

If that isn't acceptable in your environment, build from source. The
`Espresso.spec` recipe is committed and produces the same artefacts.

</details>

> **macOS keystroke modes only**: *Sleep + activity* and *Simulate activity
> only* need **System Settings → Privacy & Security → Accessibility**; without
> it macOS silently discards the keystrokes. Espresso detects this and offers a
> menu shortcut to the right pane. The default mode needs nothing.

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
  Espresso v1.2.0
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

Output lands in `dist/`: `Espresso.app` on macOS, `Espresso/Espresso.exe` on
Windows, `Espresso/Espresso` on Linux. The spec is committed, so every platform
builds the same way; it sets `LSUIElement` on macOS so the app stays out of the
Dock.

Builds are **onedir**, not onefile. A onefile executable unpacks its whole
~36 MB payload into a temp directory on every single launch — slow, hard on the
disk, and one of the patterns antivirus heuristics flag most readily. UPX
compression is off for the same reason.

## Footprint

Measured on macOS, idle, with the tray icon showing:

| | |
| --- | --- |
| Resident memory | ~80 MB |
| CPU while idle | 0.0% |
| Startup | well under a second |

Most of that memory is the embedded Python runtime and the GUI bindings, which
is the price of a cross-platform tray app in Python. The application's own
working set is a few hundred KB: it wakes on a timer, calls one OS function,
and goes back to sleep.

If you are curious where the rest went — the tray artwork used to be a
1280×1280 PNG, which cost 6.2 MB of RAM per decoded copy for pixels no tray can
display. It is now 256×256, scaled to 64 px on load.

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

Contributions are welcome.

```bash
pip install -e ".[dev]"
make check          # lint + tests, exactly what CI runs
```

| Document | For |
| --- | --- |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, opening a PR, code layout, the traps |
| [RELEASING.md](RELEASING.md) | Maintainers cutting a version |
| [SECURITY.md](SECURITY.md) | Reporting a vulnerability |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | How we treat each other |

## License

[MIT](LICENSE) © Abhijith P Subash
