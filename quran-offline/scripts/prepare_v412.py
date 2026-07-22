#!/usr/bin/env python3
from pathlib import Path


def replace_exact(path: Path, old: str, new: str, expected_min: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count < expected_min:
        raise RuntimeError(f"Expected at least {expected_min} occurrence(s) in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"patched {path}: {count} occurrence(s)")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    java = root / "app/src/main/java/com/mastermedia/quranoffline"
    audio = java / "AudioServiceV410.java"
    activity = java / "MainActivityV410.java"

    # Keep the stable service and preferences, but update all visible reader labels.
    replace_exact(audio, "ياسر الدوسري", "عادل ريان", expected_min=3)

    # Reduce the accumulated lag from native + JavaScript smoothing while preserving wrap-around.
    replace_exact(activity,
                  "private static final long COMPASS_DISPATCH_INTERVAL_MS = 75L;",
                  "private static final long COMPASS_DISPATCH_INTERVAL_MS = 35L;")
    replace_exact(activity, "final float alpha = 0.16f;", "final float alpha = 0.28f;")
    replace_exact(activity,
                  "delta = Math.max(-42f, Math.min(42f, delta));",
                  "delta = Math.max(-120f, Math.min(120f, delta));")
    replace_exact(activity,
                  "filteredHeading = (filteredHeading + delta * 0.32f + 360f) % 360f;",
                  "filteredHeading = (filteredHeading + delta * 0.72f + 360f) % 360f;")
    replace_exact(activity, "SensorManager.SENSOR_DELAY_UI", "SensorManager.SENSOR_DELAY_GAME", expected_min=3)


if __name__ == "__main__":
    main()
