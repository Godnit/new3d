#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# The source pages are 800 px wide. 600 px is noticeably clearer than the
# previous 480 px build on 720 px phones, while grayscale WebP keeps the total
# package small enough for the complete offline recitation.
PAGE_WIDTH = 600
PAGE_HEIGHT = 970
WEBP_QUALITY = 74


def process_page(arguments: tuple[str, str]) -> tuple[int, int]:
    source_path, destination_path = map(Path, arguments)
    source = Image.open(source_path)

    # The supplied Madani pages are monochrome. Keeping a single luminance
    # channel saves space without discarding Quran text detail.
    source = ImageOps.grayscale(source)
    source = ImageOps.autocontrast(source, cutoff=0.15)
    source.thumbnail((PAGE_WIDTH, PAGE_HEIGHT), Image.Resampling.LANCZOS)

    # A light unsharp mask restores edge clarity lost during down-sampling.
    # It does not redraw, crop or reflow any Quran text.
    source = source.filter(ImageFilter.UnsharpMask(radius=0.65, percent=125, threshold=2))
    source = ImageEnhance.Contrast(source).enhance(1.035)

    canvas = Image.new("L", (PAGE_WIDTH, PAGE_HEIGHT), 255)
    left = (PAGE_WIDTH - source.width) // 2
    top = (PAGE_HEIGHT - source.height) // 2
    canvas.paste(source, (left, top))

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(
        destination_path,
        "WEBP",
        quality=WEBP_QUALITY,
        method=6,
        exact=True,
    )
    return source_path.stat().st_size, destination_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
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

    before = sum(item[0] for item in sizes)
    after = sum(item[1] for item in sizes)
    files = sorted(args.destination.glob("page*.webp"))
    if len(files) != 604:
        raise RuntimeError(f"Expected 604 page images, got {len(files)}")
    if min(path.stat().st_size for path in files) < 1200:
        raise RuntimeError("A generated Mushaf page looks empty")
    print(
        "Built 604 complete grayscale Mushaf pages at "
        f"{PAGE_WIDTH}x{PAGE_HEIGHT}, quality={WEBP_QUALITY}: "
        f"{before} -> {after} bytes"
    )


if __name__ == "__main__":
    main()
