from pathlib import Path
import re

runner = Path("xau_lab/hf_window_runner.py")
text = runner.read_text(encoding="utf-8")

# The July/December 2025 gate from the previous completed run is now retired.
# Keep development and validation unchanged, and use two separate June 2025
# weeks that have not appeared in the prior holdout-rotation patches.
new_windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-14", "2021-06-19"),
    ("dev_2021_oct", "dev", "2021-10-11", "2021-10-16"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-12"),
    ("dev_2022_sep", "dev", "2022-09-19", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-13", "2023-03-18"),
    ("dev_2023_oct", "dev", "2023-10-09", "2023-10-14"),
    ("val_2024_feb", "validation", "2024-02-12", "2024-02-17"),
    ("val_2024_aug", "validation", "2024-08-12", "2024-08-17"),
    ("hold_2025_jun_a", "holdout", "2025-06-02", "2025-06-07"),
    ("hold_2025_jun_b", "holdout", "2025-06-16", "2025-06-21"),
]
'''
text, count = re.subn(r"WINDOWS = \[\n.*?\n\]\n", new_windows, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit("could not install fresh June 2025 holdout protocol")
runner.write_text(text, encoding="utf-8")
print("Rotated blind holdout to two previously unused June 2025 weeks")
