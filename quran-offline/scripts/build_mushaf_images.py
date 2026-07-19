#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

PAGE_WIDTH = 480
PAGE_HEIGHT = 776
BORDER_WIDTH = 800
BORDER_HEIGHT = 1294
INNER = (72, 84, 728, 1210)


def process_page(arguments: tuple[str, str]) -> tuple[int, int]:
    source_path, destination_path = map(Path, arguments)
    source = Image.open(source_path).convert("RGB")
    fitted = ImageOps.fit(source, (PAGE_WIDTH, PAGE_HEIGHT), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    # This matches the already accepted compact Mushaf quality: high-resolution
    # enough for a phone screen, while all 604 pages remain embedded offline.
    fitted.save(destination_path, "WEBP", quality=82, method=6, exact=True)
    return source_path.stat().st_size, destination_path.stat().st_size


def create_shared_border(source_path: Path, destination_path: Path) -> int:
    border = Image.open(source_path).convert("RGBA")
    border = ImageOps.fit(border, (BORDER_WIDTH, BORDER_HEIGHT), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    border = ImageEnhance.Contrast(border).enhance(1.04)
    pixels = border.load()
    left, top, right, bottom = INNER
    # Make the centre transparent. The ornament remains a real image asset,
    # loaded once and placed above every page without duplicating it 604 times.
    for y in range(top, bottom):
        for x in range(left, right):
            r, g, b, _ = pixels[x, y]
            pixels[x, y] = (r, g, b, 0)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    border.save(destination_path, "WEBP", lossless=True, method=6, exact=True)
    return destination_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--border", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    args.destination.mkdir(parents=True, exist_ok=True)
    tasks = []
    for page in range(1, 605):
        src = args.source / f"page{page:03d}.png"
        if not src.exists():
            raise FileNotFoundError(src)
        tasks.append((str(src), str(args.destination / f"page{page:03d}.webp")))

    workers = min(8, os.cpu_count() or 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        sizes = list(pool.map(process_page, tasks, chunksize=6))

    border_size = create_shared_border(args.border, args.destination / "mushaf-border.webp")
    before = sum(item[0] for item in sizes)
    after = sum(item[1] for item in sizes)
    files = sorted(args.destination.glob("page*.webp"))
    if len(files) != 604:
        raise RuntimeError(f"Expected 604 page images, got {len(files)}")
    if min(path.stat().st_size for path in files) < 1200:
        raise RuntimeError("A generated Mushaf page looks empty")
    if border_size < 5000:
        raise RuntimeError("The shared Mushaf border looks empty")
    print(f"Built 604 compact pages and one shared real ornament: {before} -> {after + border_size} bytes")


if __name__ == "__main__":
    main()
