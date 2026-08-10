# Assets

| File | Used for | Bundled |
| --- | --- | --- |
| `c5.png` | Tray icon, loaded at runtime. 256×256, scaled to 64 px on load. | ✅ |
| `c5.icns` | macOS app icon (`.app`) | build only |
| `c5.ico` | Windows executable icon | build only |
| `c5-source.png` | 1280×1280 master artwork, kept for regenerating the above | ❌ |

`c5.png` is deliberately small. A tray icon renders at 22–44 px, and the
1280×1280 original cost 6.2 MB of RAM per decoded copy — roughly 13 MB of the
app's resident memory for pixels nothing could display.
