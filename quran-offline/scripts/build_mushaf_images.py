#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

# The source files are already scanned Mushaf pages with their original ornament.
# We only resize and encode them. No frame or decoration is drawn by this script.
WIDTH = 620
HEIGHT = 930
QUALITY = 70


def find_source(directory: Path, page: int) -> Path:
    names = (
        f"{page}.jpg", f"{page:03d}.jpg", f"page{page:03d}.jpg",
        f"{page}.jpeg", f"{page:03d}.jpeg", f"page{page:03d}.jpeg",
        f"{page}.png", f"{page:03d}.png", f"page{page:03d}.png",
    )
    for name in names:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No scanned source image for page {page} in {directory}")


def process(arguments: tuple[str, str]) -> tuple[int, int]:
    source_path, output_path = map(Path, arguments)
    with Image.open(source_path) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")

    # Keep the complete scanned page, including its original decorative border.
    source = ImageOps.contain(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    source = source.filter(ImageFilter.UnsharpMask(radius=0.42, percent=108, threshold=3))
    source = ImageEnhance.Contrast(source).enhance(1.015)

    page = Image.new("RGB", (WIDTH, HEIGHT), "white")
    x = (WIDTH - source.width) // 2
    y = (HEIGHT - source.height) // 2
    page.paste(source, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path, "WEBP", quality=QUALITY, method=6, exact=True)
    return source_path.stat().st_size, output_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    shutil.rmtree(args.destination, ignore_errors=True)
    args.destination.mkdir(parents=True, exist_ok=True)

    tasks = []
    for page_number in range(1, 605):
        source = find_source(args.source, page_number)
        destination = args.destination / f"page{page_number:03d}.webp"
        tasks.append((str(source), str(destination)))

    workers = min(8, os.cpu_count() or 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        sizes = list(pool.map(process, tasks, chunksize=5))

    files = sorted(args.destination.glob("page*.webp"))
    if len(files) != 604:
        raise RuntimeError(f"Expected 604 pages, got {len(files)}")

    for sample in (files[0], files[1], files[427], files[-1]):
        if sample.stat().st_size < 8_000:
            raise RuntimeError(f"Generated page is suspiciously small: {sample}")
        with Image.open(sample) as image:
            if image.size != (WIDTH, HEIGHT):
                raise RuntimeError(f"Wrong dimensions: {sample} {image.size}")
            gray = image.convert("L")
            if ImageStat.Stat(gray).var[0] < 120:
                raise RuntimeError(f"Page appears empty: {sample}")

    original_bytes = sum(item[0] for item in sizes)
    output_bytes = sum(item[1] for item in sizes)
    print(
        f"Compressed 604 ready-scanned decorated pages at {WIDTH}x{HEIGHT}, "
        f"WebP q={QUALITY}: {original_bytes} -> {output_bytes} bytes "
        f"({output_bytes / 1048576:.2f} MiB)"
    )


if __name__ == "__main__":
    main()
