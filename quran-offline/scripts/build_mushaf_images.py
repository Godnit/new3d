#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

# The plain page stays compact and readable. The two themed sets are fully baked
# page images: Quran text + ornament in one WebP, never a white overlay at runtime.
PAGE_WIDTH = 540
PAGE_HEIGHT = 873
PLAIN_QUALITY = 68
THEME_WIDTH = 660
THEME_HEIGHT = 990
THEME_QUALITY = 76
INNER_BOX = (58, 58, 602, 932)


def draw_rosette(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int,
                 colors: tuple[str, str, str]) -> None:
    outer, middle, accent = colors
    points = []
    for index in range(16):
        angle = -math.pi / 2 + index * math.pi / 8
        distance = radius if index % 2 == 0 else radius * 0.48
        points.append((cx + math.cos(angle) * distance,
                       cy + math.sin(angle) * distance))
    draw.polygon(points, fill=middle, outline=outer)
    inner = radius * 0.36
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner),
                 fill=accent, outline=outer, width=max(1, radius // 10))
    dot = radius * 0.14
    draw.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=outer)


def draw_ornament_band(draw: ImageDraw.ImageDraw, y: int, left: int, right: int,
                       flipped: bool, colors: tuple[str, str, str]) -> None:
    outer, middle, _ = colors
    offset = -5 if flipped else 5
    draw.line((left, y, right, y), fill=outer, width=3)
    draw.line((left, y + offset, right, y + offset), fill=middle, width=2)
    for x in range(left + 22, right, 44):
        motif_y = y - 16 if flipped else y + 16
        draw_rosette(draw, x, motif_y, 11, colors)
        if flipped:
            draw.arc((x - 20, y - 27, x, y - 3), 20, 160, fill=middle, width=2)
            draw.arc((x, y - 27, x + 20, y - 3), 20, 160, fill=middle, width=2)
        else:
            draw.arc((x - 20, y + 3, x, y + 27), 200, 340, fill=middle, width=2)
            draw.arc((x, y + 3, x + 20, y + 27), 200, 340, fill=middle, width=2)


def build_theme_template(style: str) -> Image.Image:
    if style == "blue":
        paper, outer, middle, soft, accent = (
            "#fffefa", "#123e5f", "#2f759e", "#c9dce8", "#cf7d52"
        )
    elif style == "gold":
        paper, outer, middle, soft, accent = (
            "#fffaf0", "#5c4925", "#b48a3c", "#ead9aa", "#1f6a52"
        )
    else:
        raise ValueError(style)

    image = Image.new("RGB", (THEME_WIDTH, THEME_HEIGHT), paper)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 651, 981), radius=10, outline=outer, width=4)
    draw.rounded_rectangle((17, 17, 642, 972), radius=8, outline=middle, width=2)
    draw.rounded_rectangle((28, 28, 631, 961), radius=5, outline=outer, width=3)
    draw.rounded_rectangle((45, 45, 614, 944), radius=3, outline=soft, width=2)

    colors = (outer, middle, accent)
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        cx = 38 if sx == 1 else 622
        cy = 38 if sy == 1 else 952
        draw_rosette(draw, cx, cy, 18, colors)
        x0 = 12 if sx == 1 else 648
        y0 = 12 if sy == 1 else 978
        draw.line((x0, y0, x0 + sx * 42, y0), fill=outer, width=5)
        draw.line((x0, y0, x0, y0 + sy * 42), fill=outer, width=5)

    draw_ornament_band(draw, 42, 62, 598, False, colors)
    draw_ornament_band(draw, 948, 62, 598, True, colors)
    for y in range(90, 910, 42):
        for x in (32, 628):
            draw_rosette(draw, x, y, 8, colors)
            draw.line((x, y - 16, x, y + 16), fill=soft, width=2)

    draw.rectangle((INNER_BOX[0] - 4, INNER_BOX[1] - 4,
                    INNER_BOX[2] + 4, INNER_BOX[3] + 4),
                   fill=paper, outline=outer, width=3)
    draw.rectangle(INNER_BOX, fill="#ffffff")
    return image


BLUE_TEMPLATE = build_theme_template("blue")
GOLD_TEMPLATE = build_theme_template("gold")


def process_page(arguments: tuple[str, str, str, str]) -> tuple[int, int, int, int]:
    source_path, plain_path, blue_path, gold_path = map(Path, arguments)
    source = Image.open(source_path)

    # The Madani source is monochrome, so one luminance channel avoids storing
    # duplicate RGB channels. No Quran content is cropped or reflowed.
    source = ImageOps.grayscale(source)
    source = ImageOps.autocontrast(source, cutoff=0.10)
    source.thumbnail((PAGE_WIDTH, PAGE_HEIGHT), Image.Resampling.LANCZOS)
    source = source.filter(ImageFilter.UnsharpMask(radius=0.55, percent=118, threshold=2))
    source = ImageEnhance.Contrast(source).enhance(1.025)

    plain = Image.new("L", (PAGE_WIDTH, PAGE_HEIGHT), 255)
    left = (PAGE_WIDTH - source.width) // 2
    top = (PAGE_HEIGHT - source.height) // 2
    plain.paste(source, (left, top))

    plain_path.parent.mkdir(parents=True, exist_ok=True)
    plain.save(plain_path, "WEBP", quality=PLAIN_QUALITY, method=6, exact=True)

    page_rgb = plain.convert("RGB")
    inner_width = INNER_BOX[2] - INNER_BOX[0]
    inner_height = INNER_BOX[3] - INNER_BOX[1]
    fitted = ImageOps.contain(page_rgb, (inner_width, inner_height), Image.Resampling.LANCZOS)
    paste_x = INNER_BOX[0] + (inner_width - fitted.width) // 2
    paste_y = INNER_BOX[1] + (inner_height - fitted.height) // 2

    for template, output_path in ((BLUE_TEMPLATE, blue_path), (GOLD_TEMPLATE, gold_path)):
        output = template.copy()
        output.paste(fitted, (paste_x, paste_y))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output.save(output_path, "WEBP", quality=THEME_QUALITY, method=6, exact=True)

    return (
        source_path.stat().st_size,
        plain_path.stat().st_size,
        blue_path.stat().st_size,
        gold_path.stat().st_size,
    )


def validate_set(directory: Path, expected_size: tuple[int, int]) -> list[Path]:
    files = sorted(directory.glob("page*.webp"))
    if len(files) != 604:
        raise RuntimeError(f"Expected 604 pages in {directory}, got {len(files)}")
    for path in files:
        if path.stat().st_size < 1200:
            raise RuntimeError(f"Generated Mushaf page looks empty: {path}")
        with Image.open(path) as image:
            if image.size != expected_size:
                raise RuntimeError(f"Wrong dimensions for {path}: {image.size}")
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    plain_destination = args.destination
    blue_destination = plain_destination.parent / "mushaf-pages-blue"
    gold_destination = plain_destination.parent / "mushaf-pages-gold"
    for directory in (plain_destination, blue_destination, gold_destination):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True, exist_ok=True)

    tasks = []
    for page in range(1, 605):
        source = args.source / f"page{page:03d}.png"
        if not source.exists():
            raise FileNotFoundError(source)
        tasks.append((
            str(source),
            str(plain_destination / f"page{page:03d}.webp"),
            str(blue_destination / f"page{page:03d}.webp"),
            str(gold_destination / f"page{page:03d}.webp"),
        ))

    workers = min(8, os.cpu_count() or 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        sizes = list(pool.map(process_page, tasks, chunksize=4))

    validate_set(plain_destination, (PAGE_WIDTH, PAGE_HEIGHT))
    validate_set(blue_destination, (THEME_WIDTH, THEME_HEIGHT))
    validate_set(gold_destination, (THEME_WIDTH, THEME_HEIGHT))

    before = sum(item[0] for item in sizes)
    plain_bytes = sum(item[1] for item in sizes)
    blue_bytes = sum(item[2] for item in sizes)
    gold_bytes = sum(item[3] for item in sizes)
    print(
        "Built three complete 604-page Mushaf image sets: "
        f"source={before} plain={plain_bytes} blue={blue_bytes} gold={gold_bytes} bytes"
    )


if __name__ == "__main__":
    main()