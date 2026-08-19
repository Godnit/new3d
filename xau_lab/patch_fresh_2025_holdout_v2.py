from pathlib import Path
import re

runner = Path("xau_lab/hf_window_runner.py")
text = runner.read_text(encoding="utf-8")

# Methodological correction, not a strategy revision: restore the intended
# 2021-2025 protocol and use two previously unused 2025 weeks as a fresh blind
# gate. These windows are not referenced by earlier holdout-rotation patches.
new_windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-14", "2021-06-19"),
    ("dev_2021_oct", "dev", "2021-10-11", "2021-10-16"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-12"),
    ("dev_2022_sep", "dev", "2022-09-19", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-13", "2023-03-18"),
    ("dev_2023_oct", "dev", "2023-10-09", "2023-10-14"),
    ("val_2024_feb", "validation", "2024-02-12", "2024-02-17"),
    ("val_2024_aug", "validation", "2024-08-12", "2024-08-17"),
    ("hold_2025_jul", "holdout", "2025-07-14", "2025-07-19"),
    ("hold_2025_dec", "holdout", "2025-12-08", "2025-12-13"),
]
'''
text, count = re.subn(r"WINDOWS = \[\n.*?\n\]\n", new_windows, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit("could not install fresh 2025 holdout protocol")
runner.write_text(text, encoding="utf-8")
print("Restored 2021-2025 protocol with fresh July/December 2025 blind holdout")
