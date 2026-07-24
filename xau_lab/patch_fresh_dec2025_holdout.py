from pathlib import Path

path = Path("xau_lab/hf_window_runner.py")
text = path.read_text(encoding="utf-8")

replacements = {
    '("hold_2021_may", "holdout", "2021-05-24", "2021-06-05"),':
        '("hold_2025_dec_a", "holdout", "2025-12-01", "2025-12-13"),',
    '("hold_2022_dec", "holdout", "2022-12-01", "2022-12-20"),':
        '("hold_2025_dec_b", "holdout", "2025-12-15", "2025-12-27"),',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"Expected retired holdout tuple was not found: {old}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("Rotated to two previously unused December 2025 holdout blocks")
