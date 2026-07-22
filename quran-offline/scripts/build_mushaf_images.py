#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import urllib.request
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

# A ready-made 604-page Madinah Mushaf image bundle. The 480px edition is about
# 28 MiB before repacking and is much more suitable for a compact offline APK.
BUNDLE_URL = "https://quran.islam-db.com/public/data/pages/quranpages_480.zip"
WIDTH = 480
HEIGHT = 720
QUALITY = 70


def download_bundle(destination: Path) -> None:
    request = urllib.request.Request(
        BUNDLE_URL,
        headers={"User-Agent": "Mozilla/5.0 RafiqAlHuda/4.15"},
    )
    last_error: Exception | None = None
    for _ in range(5):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = response.read()
            if len(payload) < 10 * 1024 * 1024:
                raise RuntimeError(f"Mushaf ZIP is suspiciously small: {len(payload)} bytes")
            destination.write_bytes(payload)
            with zipfile.ZipFile(destination) as archive:
                bad = archive.testzip()
                if bad:
                    raise RuntimeError(f"Corrupt file in Mushaf ZIP: {bad}")
            return
        except Exception as error:
            last_error = error
    raise RuntimeError(f"Unable to download Mushaf ZIP: {last_error}")


def page_number(path: Path) -> int | None:
    matches = re.findall(r"\d+", path.stem)
    if not matches:
        return None
    value = int(matches[-1])
    return value if 1 <= value <= 604 else None


def discover_pages(directory: Path) -> dict[int, Path]:
    candidates: dict[int, Path] = {}
    for path in directory.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        number = page_number(path)
        if number is not None and number not in candidates:
            candidates[number] = path
    missing = sorted(set(range(1, 605)) - set(candidates))
    if missing:
        raise RuntimeError(f"Mushaf bundle is missing pages: {missing[:12]}")
    return candidates


def process(arguments: tuple[str, str]) -> tuple[int, int]:
    source_path, output_path = map(Path, arguments)
    with Image.open(source_path) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")

    # Keep the complete page and its original decoration. No frame is drawn.
    source = ImageOps.contain(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    source = source.filter(ImageFilter.UnsharpMask(radius=0.28, percent=108, threshold=3))
    source = ImageEnhance.Contrast(source).enhance(1.01)
    page = Image.new("RGB", (WIDTH, HEIGHT), "white")
    page.paste(source, ((WIDTH - source.width) // 2, (HEIGHT - source.height) // 2))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path, "WEBP", quality=QUALITY, method=6, exact=True)
    return source_path.stat().st_size, output_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True,
                        help="Compatibility argument; the compact page bundle is used.")
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    shutil.rmtree(args.destination, ignore_errors=True)
    args.destination.mkdir(parents=True, exist_ok=True)
    work = args.destination.parent / "mushaf-480-bundle"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    archive_path = work / "quranpages_480.zip"
    extracted = work / "extracted"
    extracted.mkdir()

    download_bundle(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(extracted)
    pages = discover_pages(extracted)

    tasks = [
        (str(pages[number]), str(args.destination / f"page{number:03d}.webp"))
        for number in range(1, 605)
    ]
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as pool:
        sizes = list(pool.map(process, tasks, chunksize=8))

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
    if output_bytes >= 42 * 1024 * 1024:
        raise RuntimeError(f"Compressed Mushaf is still too large: {output_bytes / 1048576:.2f} MiB")

    (args.destination.parent / "MUSHAF_SOURCE_NOTICE.txt").write_text(
        "The app uses the quranpages_480.zip bundle from quran.islam-db.com. "
        "Each page is a complete ready-made Mushaf image; the app does not draw an "
        "ornamental frame over Quran text. Confirm redistribution permission before "
        "a public or commercial release.\n",
        encoding="utf-8",
    )
    print(
        f"Built 604 complete Mushaf pages at {WIDTH}x{HEIGHT}, WebP q={QUALITY}: "
        f"{output_bytes / 1048576:.2f} MiB"
    )


if __name__ == "__main__":
    main()
