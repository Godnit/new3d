#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageStat

# One complete precomposed page set keeps every page as a real image containing
# both Quran text and ornament. 620x930 is crisp on common phone screens while
# lossy WebP quality 58 removes the very large duplicate style packs.
WIDTH = 620
HEIGHT = 930
QUALITY = 58
INNER = (52, 54, 568, 876)


def rosette(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int) -> None:
    points = []
    for i in range(16):
        angle = -math.pi / 2 + i * math.pi / 8
        distance = radius if i % 2 == 0 else radius * .48
        points.append((cx + math.cos(angle) * distance, cy + math.sin(angle) * distance))
    draw.polygon(points, fill="#2f759e", outline="#123e5f")
    r = radius * .34
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill="#cf7d52", outline="#123e5f")


def template() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fffefa")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((7, 7, WIDTH-8, HEIGHT-8), radius=9, outline="#123e5f", width=4)
    draw.rounded_rectangle((16, 16, WIDTH-17, HEIGHT-17), radius=7, outline="#2f759e", width=2)
    draw.rounded_rectangle((28, 28, WIDTH-29, HEIGHT-29), radius=4, outline="#123e5f", width=3)
    draw.rounded_rectangle((43, 43, WIDTH-44, HEIGHT-44), radius=3, outline="#c9dce8", width=2)
    for cx, cy in ((36,36),(WIDTH-37,36),(36,HEIGHT-37),(WIDTH-37,HEIGHT-37)):
        rosette(draw, cx, cy, 17)
    for x in range(68, WIDTH-55, 43):
        rosette(draw, x, 37, 9)
        rosette(draw, x, HEIGHT-38, 9)
    for y in range(82, HEIGHT-70, 42):
        rosette(draw, 31, y, 7)
        rosette(draw, WIDTH-32, y, 7)
    draw.rectangle((INNER[0]-4, INNER[1]-4, INNER[2]+4, INNER[3]+4), fill="#fffefa", outline="#123e5f", width=3)
    draw.rectangle(INNER, fill="#ffffff")
    return image


TEMPLATE = template()


def process(args: tuple[str, str]) -> tuple[int, int]:
    src_path, out_path = map(Path, args)
    source = Image.open(src_path)
    source = ImageOps.grayscale(source)
    source = ImageOps.autocontrast(source, cutoff=.08)
    source = source.filter(ImageFilter.UnsharpMask(radius=.48, percent=112, threshold=2))
    source = ImageEnhance.Contrast(source).enhance(1.02)

    inner_w = INNER[2] - INNER[0]
    inner_h = INNER[3] - INNER[1]
    fitted = ImageOps.contain(source, (inner_w, inner_h), Image.Resampling.LANCZOS)
    output = TEMPLATE.copy()
    x = INNER[0] + (inner_w - fitted.width) // 2
    y = INNER[1] + (inner_h - fitted.height) // 2
    output.paste(fitted.convert("RGB"), (x, y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    output.save(out_path, "WEBP", quality=QUALITY, method=6, exact=True)
    return src_path.stat().st_size, out_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    shutil.rmtree(args.destination, ignore_errors=True)
    args.destination.mkdir(parents=True, exist_ok=True)
    tasks = []
    for page in range(1, 605):
        src = args.source / f"page{page:03d}.png"
        if not src.exists():
            raise FileNotFoundError(src)
        tasks.append((str(src), str(args.destination / f"page{page:03d}.webp")))

    workers = min(8, os.cpu_count() or 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        sizes = list(pool.map(process, tasks, chunksize=5))

    files = sorted(args.destination.glob("page*.webp"))
    if len(files) != 604:
        raise RuntimeError(f"Expected 604 pages, got {len(files)}")
    for sample in (files[0], files[1], files[427], files[-1]):
        with Image.open(sample) as image:
            if image.size != (WIDTH, HEIGHT):
                raise RuntimeError(f"Wrong dimensions: {sample} {image.size}")
            gray = image.convert("L").crop(INNER)
            if ImageStat.Stat(gray).var[0] < 120:
                raise RuntimeError(f"Page appears empty: {sample}")

    before = sum(x[0] for x in sizes)
    after = sum(x[1] for x in sizes)
    print(f"Built 604 decorated pages at {WIDTH}x{HEIGHT}, WebP q={QUALITY}: {before} -> {after} bytes ({after/1048576:.2f} MiB)")


if __name__ == "__main__":
    main()
