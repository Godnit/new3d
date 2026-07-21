from pathlib import Path

path = Path("xau_lab/hf_window_runner.py")
text = path.read_text(encoding="utf-8")

# patch_protocol.py runs earlier and replaces the window block with fresh
# April/November 2025 holdout windows. This rotation intentionally retires
# those already-inspected windows and moves the untouched gate to 2020.
old = '''    ("hold_2025_apr", "holdout", "2025-04-14", "2025-04-19"),
    ("hold_2025_nov", "holdout", "2025-11-10", "2025-11-15"),
'''
new = '''    # Fresh untouched holdout windows. All previously inspected 2025 windows
    # are retired from holdout use after the prior statistical failure.
    ("hold_2020_mar", "holdout", "2020-03-09", "2020-03-14"),
    ("hold_2020_oct", "holdout", "2020-10-19", "2020-10-24"),
'''

if old not in text:
    if "hold_2020_mar" in text and "hold_2020_oct" in text:
        print("Fresh 2020 holdout windows already present")
    else:
        raise SystemExit("holdout rotation marker not found after protocol patch")
else:
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("Rotated to fresh untouched 2020 holdout windows")
