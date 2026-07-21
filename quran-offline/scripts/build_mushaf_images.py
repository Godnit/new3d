#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image

PAGE_WIDTH = 480
PAGE_HEIGHT = 776


def process_page(arguments: tuple[str, str]) -> tuple[int, int]:
    source_path, destination_path = map(Path, arguments)
    source = Image.open(source_path).convert("RGB")

    # Preserve the complete original Mushaf page. We resize proportionally and
    # center it on a white canvas instead of cropping it with ImageOps.fit.
    source.thumbnail((PAGE_WIDTH, PAGE_HEIGHT), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    left = (PAGE_WIDTH - source.width) // 2
    top = (PAGE_HEIGHT - source.height) // 2
    canvas.paste(source, (left, top))

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    # No generated frame, ornament, header or footer is added above the Quran.
    canvas.save(destination_path, "WEBP", quality=84, method=6, exact=True)
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
    print(f"Built 604 complete original Mushaf pages without cropping: {before} -> {after} bytes")


if __name__ == "__main__":
    main()
