#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

# Ready-made Madinah Mushaf scans. Quran text and ornament are already combined.
WIDTH = 480
HEIGHT = 720
QUALITY = 64


def source_urls(page_number: int) -> list[tuple[str, str]]:
    # Prefer the blue decorated scan requested by the user; keep the gold scan as fallback.
    blue = f"https://ummah.su/img/mushaf/{page_number}.jpg"
    encoded = urllib.parse.quote(blue, safe="")
    gold = f"https://equran.me/assets/images/pages/{page_number:04d}.jpg"
    return [
        ("https://images.weserv.nl/?url=" + encoded + "&output=jpg&q=92", "https://images.weserv.nl/"),
        ("https://wsrv.nl/?url=" + encoded + "&output=jpg&q=92", "https://wsrv.nl/"),
        (blue, f"https://ummah.su/quran/medinskiy-muskhaf/{page_number}"),
        (gold, f"https://equran.me/page-img-{page_number}.html"),
    ]


def download_page(arguments: tuple[int, str]) -> str:
    page_number, destination_text = arguments
    destination = Path(destination_text)
    last_error: Exception | None = None
    for url, referer in source_urls(page_number):
        for _ in range(3):
            try:
                request = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/132 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Referer": referer,
                })
                with urllib.request.urlopen(request, timeout=75) as response:
                    payload = response.read()
                if len(payload) < 8_000:
                    raise RuntimeError(f"Page {page_number} is suspiciously small")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
                with Image.open(destination) as image:
                    image.verify()
                return str(destination)
            except Exception as error:
                last_error = error
    raise RuntimeError(f"Failed to download decorated Mushaf page {page_number}: {last_error}")


def crop_outer_paper(source: Image.Image) -> Image.Image:
    # Remove only the empty scanner margin around the printed ornament. The ornament
    # itself remains untouched and receives a small safety padding.
    gray = source.convert("L")
    mask = gray.point(lambda value: 255 if value < 246 else 0)
    box = mask.getbbox()
    if not box:
        return source
    left, top, right, bottom = box
    if right - left < source.width * 0.55 or bottom - top < source.height * 0.55:
        return source
    padding = max(6, round(min(source.size) * 0.012))
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(source.width, right + padding)
    bottom = min(source.height, bottom + padding)
    return source.crop((left, top, right, bottom))


def process(arguments: tuple[str, str]) -> tuple[int, int]:
    source_path, output_path = map(Path, arguments)
    with Image.open(source_path) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")

    source = crop_outer_paper(source)
    source = ImageOps.contain(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    source = ImageOps.autocontrast(source, cutoff=(0.05, 0.05))
    source = source.filter(ImageFilter.UnsharpMask(radius=0.27, percent=114, threshold=3))
    source = ImageEnhance.Contrast(source).enhance(1.012)

    page = Image.new("RGB", (WIDTH, HEIGHT), "white")
    page.paste(source, ((WIDTH - source.width) // 2, (HEIGHT - source.height) // 2))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path, "WEBP", quality=QUALITY, method=6, exact=True)
    return source_path.stat().st_size, output_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True,
                        help="Compatibility argument; ready-decorated remote scans are used.")
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    shutil.rmtree(args.destination, ignore_errors=True)
    args.destination.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="rafiq-mushaf-") as temporary:
        source_dir = Path(temporary)
        downloads = [(n, str(source_dir / f"{n:03d}.jpg")) for n in range(1, 605)]
        with ThreadPoolExecutor(max_workers=10) as pool:
            downloaded = list(pool.map(download_page, downloads))
        tasks = [(downloaded[n - 1], str(args.destination / f"page{n:03d}.webp")) for n in range(1, 605)]
        with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as pool:
            sizes = list(pool.map(process, tasks, chunksize=6))

    files = sorted(args.destination.glob("page*.webp"))
    if len(files) != 604:
        raise RuntimeError(f"Expected 604 pages, got {len(files)}")
    for sample in (files[0], files[1], files[430], files[439], files[-1]):
        if sample.stat().st_size < 4_000:
            raise RuntimeError(f"Generated page is suspiciously small: {sample}")
        with Image.open(sample) as image:
            if image.size != (WIDTH, HEIGHT):
                raise RuntimeError(f"Wrong dimensions: {sample} {image.size}")
            if ImageStat.Stat(image.convert("L")).var[0] < 120:
                raise RuntimeError(f"Page appears empty: {sample}")

    output_bytes = sum(item[1] for item in sizes)
    if output_bytes >= 45 * 1024 * 1024:
        raise RuntimeError(f"Decorated Mushaf is unexpectedly large: {output_bytes / 1048576:.2f} MiB")

    for stale in ("mushaf-480-bundle", "mushaf-complete-blue-source"):
        shutil.rmtree(args.destination.parent / stale, ignore_errors=True)

    (args.destination.parent / "MUSHAF_SOURCE_NOTICE.txt").write_text(
        "The app uses complete ready-scanned Hafs Mushaf page images, preferring the "
        "blue decorated ummah.su scan with equran.me as fallback. Quran text and the "
        "ornament are one source image; no frame is generated at runtime. Empty outer "
        "scanner margins are cropped while the complete ornament is preserved. Confirm "
        "redistribution permission before a public or commercial release.\n",
        encoding="utf-8",
    )
    print(f"Built 604 full blue-decorated pages: {output_bytes / 1048576:.2f} MiB")


if __name__ == "__main__":
    main()
