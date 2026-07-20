from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

new_fetch = '''def fetch_one(hour: datetime) -> tuple[datetime, str, int]:
    path = chunk_path(hour)
    if path.exists() and path.stat().st_size > 0:
        return hour, "cached", path.stat().st_size
    path.parent.mkdir(parents=True, exist_ok=True)
    url = dukascopy_url(hour)
    headers = {"User-Agent": "Mozilla/5.0 XAU-Real-Tick-Lab/1.0"}
    for attempt in range(7):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            if not data:
                return hour, "empty", 0
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)
            return hour, "downloaded", len(data)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return hour, "missing", 0
            if exc.code in (429, 500, 502, 503, 504):
                time.sleep(min(20.0, 2.0 * (attempt + 1)))
                continue
            return hour, f"http_{exc.code}", 0
        except Exception as exc:  # noqa: BLE001
            if attempt == 6:
                return hour, f"error:{type(exc).__name__}", 0
            time.sleep(min(20.0, 2.0 * (attempt + 1)))
    return hour, "failed", 0
'''

new_download = '''def download_window(start: datetime, end: datetime) -> None:
    hours = hourly_range(start, end)
    print(f"Downloading/checking {len(hours)} hourly chunks: {start} -> {end}", flush=True)
    pending = list(hours)
    total_bytes = 0

    # Dukascopy's public feed can throttle cloud runners. Use progressively
    # lower concurrency and retry only unresolved hours.
    for pass_no, workers in enumerate((4, 2, 1), 1):
        if not pending:
            break
        print(f"  download pass {pass_no}: pending={len(pending)} workers={workers}", flush=True)
        retry: list[datetime] = []
        counts: dict[str, int] = {}
        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(fetch_one, h) for h in pending]
            for idx, fut in enumerate(cf.as_completed(futures), 1):
                hour, status, size = fut.result()
                counts[status] = counts.get(status, 0) + 1
                total_bytes += size
                if status in ("cached", "downloaded", "empty", "missing"):
                    pass
                else:
                    retry.append(hour)
                if idx % 25 == 0 or idx == len(futures):
                    print(f"    {idx}/{len(futures)} statuses={counts} bytes={total_bytes:,}", flush=True)
        pending = sorted(retry)
        if pending:
            time.sleep(8 * pass_no)

    if pending:
        sample = ", ".join(h.isoformat() for h in pending[:8])
        raise RuntimeError(
            f"Unresolved Dukascopy hours after three passes: {len(pending)}; sample={sample}"
        )
'''

text, n1 = re.subn(
    r"def fetch_one\(hour: datetime\).*?\n\ndef download_window",
    new_fetch + "\n\ndef download_window",
    text,
    count=1,
    flags=re.S,
)
if n1 != 1:
    raise SystemExit("Could not patch fetch_one")

text, n2 = re.subn(
    r"def download_window\(start: datetime, end: datetime\).*?\n\ndef decode_hour",
    new_download + "\n\ndef decode_hour",
    text,
    count=1,
    flags=re.S,
)
if n2 != 1:
    raise SystemExit("Could not patch download_window")

path.write_text(text, encoding="utf-8")
print("Downloader patched for throttled cloud runners")
