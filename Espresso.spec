# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build recipe for Espresso.

Build with:  pyinstaller Espresso.spec --noconfirm

Output:
    macOS    dist/Espresso.app   (onedir — a bundle cannot be a single file)
    Windows  dist/Espresso.exe   (onefile)
    Linux    dist/Espresso       (onefile)
"""

import re
import sys
from pathlib import Path

IS_MACOS = sys.platform == "darwin"
ICONS = {"darwin": "assets/c5.icns", "win32": "assets/c5.ico"}

# Read the version rather than repeating it: src/espresso/__init__.py is the
# single source of truth, so a release only ever needs one number changed.
# Parsed textually because the package is not importable at build time.
_INIT = Path("src/espresso/__init__.py").read_text(encoding="utf-8")
VERSION = re.search(r'^__version__ = "([^"]+)"', _INIT, re.MULTILINE).group(1)

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=[],
    datas=[("assets/c5.png", "assets")],
    # pystray and pynput choose a back end at import time, so PyInstaller's
    # static analysis cannot see them. List every platform's; the ones that
    # don't apply are simply absent and get skipped.
    hiddenimports=[
        "pystray._darwin",
        "pystray._win32",
        "pystray._xorg",
        "pystray._appindicator",
        "pystray._gtk",
        "pynput.keyboard._darwin",
        "pynput.keyboard._win32",
        "pynput.keyboard._xorg",
        "pynput.mouse._darwin",
        "pynput.mouse._win32",
        "pynput.mouse._xorg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc_data"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

common = dict(
    name="Espresso",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX mangles macOS and Windows signatures often enough not to be worth it.
    upx=False,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICONS.get(sys.platform),
)

if IS_MACOS:
    # A .app is a directory, so the bundle must be built onedir. Combining
    # onefile with BUNDLE is deprecated and becomes an error in PyInstaller 7.
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, **common)
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Espresso")
    app = BUNDLE(
        coll,
        name="Espresso.app",
        icon=ICONS["darwin"],
        bundle_identifier="com.abhijithpsubash.espresso",
        version=VERSION,
        info_plist={
            # A tray-only app: no Dock icon, no app switcher entry.
            "LSUIElement": True,
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSAppleEventsUsageDescription": (
                "Espresso sends a harmless keystroke to keep this Mac awake."
            ),
        },
    )
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], runtime_tmpdir=None, **common)
