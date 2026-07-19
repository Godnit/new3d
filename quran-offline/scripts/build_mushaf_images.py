#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageOps


@lru_cache(maxsize=2)
def load_border(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def content_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    rgb = image.convert("RGB")
    white = Image.new("RGB", rgb.size, "white")
    difference = ImageChops.difference(rgb, white).convert("L")
    difference = difference.point(lambda value: 255 if value > 18 else 0)
    box = difference.getbbox()
    if not box:
        return (0, 0, rgb.width, rgb.height)
    left, top, right, bottom = box
    pad_x = max(5, rgb.width // 100)
    pad_y = max(5, rgb.height // 120)
    return (
        max(0, left - pad_x), max(0, top - pad_y),
        min(rgb.width, right + pad_x), min(rgb.height, bottom + pad_y),
    )


def process_one(arguments: tuple[str, str, str]) -> tuple[int, int]:
    source_path, border_path, destination_path = map(Path, arguments)
    source = Image.open(source_path).convert("RGB")
    border = load_border(str(border_path))
    final_size = source.size
    canvas = ImageOps.fit(border, final_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    canvas = ImageEnhance.Contrast(canvas).enhance(1.03)

    width, height = final_size
    inner = (
        int(width * 0.105), int(height * 0.070),
        int(width * 0.895), int(height * 0.935),
    )
    inner_width = inner[2] - inner[0]
    inner_height = inner[3] - inner[1]
    cropped = source.crop(content_bbox(source))
    fitted = ImageOps.contain(cropped, (inner_width, inner_height), method=Image.Resampling.LANCZOS)
    paper = Image.new("RGB", (inner_width, inner_height), (255, 255, 252))
    canvas.paste(paper, (inner[0], inner[1]))
    x = inner[0] + (inner_width - fitted.width) // 2
    y = inner[1] + (inner_height - fitted.height) // 2
    canvas.paste(fitted, (x, y))

    # Preserve the full 800 px resolution. A carefully generated 64-colour palette
    # keeps black Uthmanic text crisp while dramatically shrinking the repeated ornament.
    quantized = canvas.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    quantized.save(destination_path, "WEBP", lossless=True, method=5, exact=True)
    return source_path.stat().st_size, destination_path.stat().st_size


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
        tasks.append((str(src), str(args.border), str(args.destination / f"page{page:03d}.webp")))

    workers = min(8, os.cpu_count() or 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        sizes = list(pool.map(process_one, tasks, chunksize=4))
    before = sum(item[0] for item in sizes)
    after = sum(item[1] for item in sizes)
    files = sorted(args.destination.glob("page*.webp"))
    if len(files) != 604:
        raise RuntimeError(f"Expected 604 images, got {len(files)}")
    if min(path.stat().st_size for path in files) < 2000:
        raise RuntimeError("A generated Mushaf image looks empty")
    print(f"Baked public-domain ornament into 604 full-resolution pages: {before} -> {after} bytes")


if __name__ == "__main__":
    main()
