from pathlib import Path
import re

path = Path("xau_lab/hf_window_runner.py")
text = path.read_text(encoding="utf-8")

replacement = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    # Fresh holdouts not used by the preceding July-based diagnostic run.
    ("hold_2025_sep", "holdout", "2025-09-01", "2025-09-20"),
    ("hold_2025_nov", "holdout", "2025-11-03", "2025-11-22"),
]'''

text, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    replacement + "\n\n\ndef iter_months",
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not replace WINDOWS with fresh Sep/Nov 2025 holdout")
path.write_text(text, encoding="utf-8")
print("Installed fresh September/November 2025 untouched holdout windows")
