#!/usr/bin/env python3
"""Reject portrait, black, blank, overlay-only, or frozen Android screenshots."""

from pathlib import Path
from PIL import Image, ImageChops, ImageStat

MENU_PATH = Path("build/android81-menu.png")
GAME_PATH = Path("build/android81-game.png")
SCREENSHOTS = (MENU_PATH, GAME_PATH)
images: list[Image.Image] = []

for path in SCREENSHOTS:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"Missing screenshot: {path}")

    image = Image.open(path).convert("RGB")
    images.append(image)
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

start, playing = images
if start.size != playing.size:
    raise SystemExit(f"Screenshot size changed unexpectedly: {start.size} vs {playing.size}")

difference = ImageChops.difference(start, playing)
difference_mean = sum(ImageStat.Stat(difference).mean) / 3.0
print(f"start-to-playing difference={difference_mean:.2f}")
if difference_mean <= 0.45:
    raise SystemExit("The gameplay view did not respond to movement input")

for label, image in (("start", start), ("playing", playing)):
    center = image.crop((image.width * 0.25, image.height * 0.08, image.width * 0.75, image.height * 0.62))
    center_stats = ImageStat.Stat(center)
    center_mean = center_stats.mean
    center_contrast = sum(center_stats.stddev) / 3.0
    teal_like = center_mean[1] > center_mean[0] * 1.5 and center_mean[1] > center_mean[2] * 1.15
    if teal_like and center_contrast < 45.0:
        raise SystemExit(f"Android fullscreen help overlay still covers the {label} screenshot")
