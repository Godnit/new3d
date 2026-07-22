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

# Ready-made Madinah Mushaf scans. Quran text and the original blue ornament are
# already combined in each source image; the app never draws a frame at runtime.
WIDTH = 480
HEIGHT = 720
QUALITY = 64


def source_urls(page_number: int) -> list[tuple[str, str]]:
    equran = f"https://equran.me/assets/images/pages/{page_number:04d}.jpg"
    ummah = f"https://ummah.su/img/mushaf/{page_number}.jpg"
    encoded = urllib.parse.quote(ummah, safe="")
    return [
        (equran, f"https://equran.me/page-img-{page_number}.html"),
        (ummah, f"https://ummah.su/quran/medinskiy-muskhaf/{page_number}"),
        ("https://images.weserv.nl/?url=" + encoded + "&output=jpg&q=90", "https://images.weserv.nl/"),
        ("https://wsrv.nl/?url=" + encoded + "&output=jpg&q=90", "https://wsrv.nl/"),
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
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
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


def process(arguments: tuple[str, str]) -> tuple[int, int]:
    source_path, output_path = map(Path, arguments)
    with Image.open(source_path) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")

    # Preserve the full printed page and every decorated edge without cropping.
    source = ImageOps.contain(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    source = ImageOps.autocontrast(source, cutoff=(0.06, 0.06))
    source = source.filter(ImageFilter.UnsharpMask(radius=0.28, percent=112, threshold=3))
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

    # IMPORTANT: temporary JPGs stay under the system temp directory, never under
    # app/src/main/assets. This prevents the original scans from being packaged a
    # second time inside the APK.
    with tempfile.TemporaryDirectory(prefix="rafiq-mushaf-") as temporary:
        source_dir = Path(temporary)
        downloads = [(n, str(source_dir / f"{n:03d}.jpg")) for n in range(1, 605)]
        with ThreadPoolExecutor(max_workers=10) as pool:
            downloaded = list(pool.map(download_page, downloads))

        tasks = [
            (downloaded[n - 1], str(args.destination / f"page{n:03d}.webp"))
            for n in range(1, 605)
        ]
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

    # Remove leftovers accidentally packaged by the previous implementation.
    for stale in ("mushaf-480-bundle", "mushaf-complete-blue-source"):
        shutil.rmtree(args.destination.parent / stale, ignore_errors=True)

    (args.destination.parent / "MUSHAF_SOURCE_NOTICE.txt").write_text(
        "The app uses complete ready-scanned Hafs Mushaf page images from equran.me, "
        "with ummah.su as a fallback. Quran text and the original blue ornament are "
        "one source image; no frame is generated at runtime. Temporary source scans "
        "are kept outside app assets and are not packaged in the APK. Confirm "
        "redistribution permission before a public or commercial release.\n",
        encoding="utf-8",
    )
    print(
        f"Built 604 complete blue-decorated pages at {WIDTH}x{HEIGHT}, WebP q={QUALITY}: "
        f"{output_bytes / 1048576:.2f} MiB"
    )


if __name__ == "__main__":
    main()
