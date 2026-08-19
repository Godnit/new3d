from pathlib import Path
import re

runner = Path("xau_lab/hf_window_runner.py")
text = runner.read_text(encoding="utf-8")

# April/November 2025 have now been inspected and are retired. Preserve all
# development and 2024 validation windows, and move the blind gate to two
# previously unused 2026 periods that do not overlap the Headway June-August
# report interval.
new_windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-14", "2021-06-19"),
    ("dev_2021_oct", "dev", "2021-10-11", "2021-10-16"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-12"),
    ("dev_2022_sep", "dev", "2022-09-19", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-13", "2023-03-18"),
    ("dev_2023_oct", "dev", "2023-10-09", "2023-10-14"),
    ("val_2024_feb", "validation", "2024-02-12", "2024-02-17"),
    ("val_2024_aug", "validation", "2024-08-12", "2024-08-17"),
    ("hold_2026_jan", "holdout", "2026-01-12", "2026-01-17"),
    ("hold_2026_mar", "holdout", "2026-03-09", "2026-03-14"),
]
'''
text, count = re.subn(r"WINDOWS = \[\n.*?\n\]\n", new_windows, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit("could not rotate holdout windows")
runner.write_text(text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The previously inspected .*? holdout gate passes\.",
    "All previously inspected 2025 holdout windows are retired. The candidate is considered acceptable only when the newly untouched January/March 2026 holdout gate passes; these periods do not overlap the Headway June-August 2026 report interval.",
    report,
)
aggregate.write_text(report, encoding="utf-8")
print("Rotated blind holdout to previously unused January/March 2026 windows")
