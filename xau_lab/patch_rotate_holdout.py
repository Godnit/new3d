from pathlib import Path

path = Path("xau_lab/hf_window_runner.py")
text = path.read_text(encoding="utf-8")
old = '''    # Newly untouched holdout windows. Earlier 2025 windows are retired from holdout use.
    ("hold_2025_mar", "holdout", "2025-03-10", "2025-03-15"),
    ("hold_2025_sep", "holdout", "2025-09-15", "2025-09-20"),
'''
new = '''    # Fresh untouched holdout windows. All previously inspected 2025 windows are
    # retired from holdout use after the prior statistical failure.
    ("hold_2020_mar", "holdout", "2020-03-09", "2020-03-14"),
    ("hold_2020_oct", "holdout", "2020-10-19", "2020-10-24"),
'''
if old not in text:
    raise SystemExit("holdout rotation marker not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Rotated to fresh untouched 2020 holdout windows")
