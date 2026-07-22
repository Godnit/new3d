#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import urllib.parse
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

# Each source is a ready-composed scan: Quran text, headings, verse markers and
# the original blue floral border are one JPG. No ornament is generated here.
ORIGINAL_TEMPLATE = "https://ummah.su/img/mushaf/{page}.jpg"
WIDTH = 620
HEIGHT = 930
QUALITY = 72


def source_urls(page_number: int) -> list[str]:
    original = ORIGINAL_TEMPLATE.format(page=page_number)
    encoded = urllib.parse.quote(original, safe="")
    return [
        original,
        "https://images.weserv.nl/?url=" + encoded + "&output=jpg&q=92",
        "https://wsrv.nl/?url=" + encoded + "&output=jpg&q=92",
    ]


def download_page(arguments: tuple[int, str]) -> str:
    page_number, destination_text = arguments
    destination = Path(destination_text)
    last_error: Exception | None = None
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/132 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": f"https://ummah.su/quran/medinskiy-muskhaf/{page_number}",
    }
    for url in source_urls(page_number):
        for _ in range(3):
            try:
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = response.read()
                if len(payload) < 8_000:
                    raise RuntimeError(f"Page {page_number} download is suspiciously small")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
                with Image.open(destination) as image:
                    image.verify()
                return str(destination)
            except Exception as error:
                last_error = error
    raise RuntimeError(f"Failed to download complete Mushaf page {page_number}: {last_error}")


def process(arguments: tuple[str, str]) -> tuple[int, int]:
    source_path, output_path = map(Path, arguments)
    with Image.open(source_path) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")

    # Preserve every decorated edge and the complete Quran page without cropping.
    source = ImageOps.contain(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    source = source.filter(ImageFilter.UnsharpMask(radius=0.38, percent=106, threshold=3))
    source = ImageEnhance.Contrast(source).enhance(1.01)

    page = Image.new("RGB", (WIDTH, HEIGHT), "white")
    x = (WIDTH - source.width) // 2
    y = (HEIGHT - source.height) // 2
    page.paste(source, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path, "WEBP", quality=QUALITY, method=6, exact=True)
    return source_path.stat().st_size, output_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True,
                        help="Compatibility argument; complete remote scans are used.")
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    shutil.rmtree(args.destination, ignore_errors=True)
    args.destination.mkdir(parents=True, exist_ok=True)
    remote_source = args.destination.parent / "mushaf-complete-blue-source"
    shutil.rmtree(remote_source, ignore_errors=True)
    remote_source.mkdir(parents=True, exist_ok=True)

    downloads = [(page, str(remote_source / f"{page:03d}.jpg")) for page in range(1, 605)]
    with ThreadPoolExecutor(max_workers=10) as pool:
        downloaded = list(pool.map(download_page, downloads))

    tasks = [
        (downloaded[page - 1], str(args.destination / f"page{page:03d}.webp"))
        for page in range(1, 605)
    ]
    workers = min(8, os.cpu_count() or 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        sizes = list(pool.map(process, tasks, chunksize=5))

    files = sorted(args.destination.glob("page*.webp"))
    if len(files) != 604:
        raise RuntimeError(f"Expected 604 pages, got {len(files)}")

    for sample in (files[0], files[1], files[430], files[439], files[-1]):
        if sample.stat().st_size < 10_000:
            raise RuntimeError(f"Generated page is suspiciously small: {sample}")
        with Image.open(sample) as image:
            if image.size != (WIDTH, HEIGHT):
                raise RuntimeError(f"Wrong dimensions: {sample} {image.size}")
            gray = image.convert("L")
            if ImageStat.Stat(gray).var[0] < 150:
                raise RuntimeError(f"Page appears empty: {sample}")

    original_bytes = sum(item[0] for item in sizes)
    output_bytes = sum(item[1] for item in sizes)
    notice = args.destination.parent / "MUSHAF_SOURCE_NOTICE.txt"
    notice.write_text(
        "Complete ready-scanned Madinah Mushaf page images were retrieved from "
        "https://ummah.su/quran/medinskiy-muskhaf/ (directly or through an image "
        "delivery proxy). Text and the original blue ornament are one source image; "
        "no frame is generated at runtime. Confirm redistribution permission before "
        "a public or commercial release.\n",
        encoding="utf-8",
    )
    print(
        f"Built 604 complete blue-border scanned Mushaf pages at {WIDTH}x{HEIGHT}, "
        f"WebP q={QUALITY}: {original_bytes} -> {output_bytes} bytes "
        f"({output_bytes / 1048576:.2f} MiB)"
    )


if __name__ == "__main__":
    main()
