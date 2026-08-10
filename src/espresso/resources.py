"""Bundled asset lookup and tray icon rendering."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PIL import Image, ImageDraw

log = logging.getLogger(__name__)

#: Tray icons render at roughly 22-44 px even on HiDPI displays. The bundled
#: artwork is 1280x1280, which costs 6.2 MB of RAM per decoded copy and buys
#: nothing — we keep two (active and paused), so this scaling is most of the
#: app's resident memory.
ICON_SIZE = 64


def assets_dir() -> Path:
    """Locate ``assets/`` both in a source checkout and inside a frozen bundle."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:  # PyInstaller unpacks datas next to the executable's temp root
        return Path(meipass) / "assets"
    return Path(__file__).resolve().parents[2] / "assets"


def resource_path(name: str) -> Path:
    return assets_dir() / name


def _fallback_icon() -> Image.Image:
    """Draw a plain cup so a missing asset never turns into a blank tray slot."""
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    body = (24, 40, 92, 104)
    draw.rounded_rectangle(body, radius=12, fill=(120, 72, 42, 255))
    draw.arc((84, 52, 116, 88), start=270, end=90, fill=(120, 72, 42, 255), width=8)
    draw.rectangle((24, 40, 92, 52), fill=(240, 236, 230, 255))
    return image


def base_icon() -> Image.Image:
    """The tray icon artwork, scaled down, or a fallback if it can't be read."""
    path = resource_path("c5.png")
    try:
        with Image.open(path) as image:
            # draft() lets the JPEG/PNG decoder skip pixels it will never need,
            # so oversized artwork is never fully decoded in the first place.
            image.draft("RGBA", (ICON_SIZE, ICON_SIZE))
            icon = image.convert("RGBA")
    except (OSError, ValueError) as exc:
        log.warning("Could not load icon %s (%s); using fallback artwork", path, exc)
        return _fallback_icon()
    if max(icon.size) > ICON_SIZE:
        icon.thumbnail((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
    return icon


def idle_icon(active: Image.Image) -> Image.Image:
    """A desaturated, dimmed variant used while Espresso is paused."""
    grey = active.convert("LA").convert("RGBA")
    alpha = active.getchannel("A").point(lambda value: int(value * 0.55))
    grey.putalpha(alpha)
    return grey
