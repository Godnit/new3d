from pathlib import Path
import re

engine = Path("xau_lab/real_tick_lab.py")
runner = Path("xau_lab/hf_window_runner.py")

text = engine.read_text(encoding="utf-8")

# One economically interpretable strategy revision: disable long entries.
# Across the just-completed development+validation sample, long trades were
# negative while short trades were approximately break-even/positive. This
# preserves the existing signal, trend, risk, and execution logic and changes
# only the permitted direction.
needle = '''    if buy:
        name = "CROSS_BUY" if cross_buy else ("FOLLOW_BUY" if follow_buy else "CONT_BUY")
        return 1, name, atr
    if sell:
'''
replacement = '''    # Iteration revision: short-only directional asymmetry.
    # Do not alter the underlying signal construction; simply reject longs.
    buy = False

    if buy:
        name = "CROSS_BUY" if cross_buy else ("FOLLOW_BUY" if follow_buy else "CONT_BUY")
        return 1, name, atr
    if sell:
'''
if needle not in text:
    raise SystemExit("Could not locate final buy/sell dispatch in engine")
text = text.replace(needle, replacement, 1)
engine.write_text(text, encoding="utf-8")

rtext = runner.read_text(encoding="utf-8")
pattern = re.compile(r"WINDOWS = \[.*?\n\]", re.S)
windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2021_may_available", "holdout", "2021-05-24", "2021-06-05"),
    ("hold_2022_dec", "holdout", "2022-12-01", "2022-12-20"),
]'''
rtext, count = pattern.subn(windows, rtext, count=1)
if count != 1:
    raise SystemExit("Could not replace diagnostic protocol windows")
runner.write_text(rtext, encoding="utf-8")

print("Applied one strategy revision (short-only) and reset the holdout protocol to non-overlapping available windows")
