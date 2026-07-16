#!/usr/bin/env python3
"""Reject portrait, black, or visually blank Android emulator screenshots."""

from pathlib import Path
from PIL import Image, ImageStat

SCREENSHOTS = (
    Path("build/android81-menu.png"),
    Path("build/android81-game.png"),
)

for path in SCREENSHOTS:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"Missing screenshot: {path}")

    image = Image.open(path).convert("RGB")
    if image.width <= image.height:
        raise SystemExit(f"Not landscape: {path} {image.size}")

    statistics = ImageStat.Stat(image)
    brightness = sum(statistics.mean) / 3.0
    contrast = sum(statistics.stddev) / 3.0
    print(f"{path}: size={image.size} brightness={brightness:.2f} contrast={contrast:.2f}")

    if brightness <= 10.0:
        raise SystemExit(f"Black/dark screen: {path}")
    if contrast <= 8.0:
        raise SystemExit(f"Flat/blank screen: {path}")
