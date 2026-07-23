from pathlib import Path
import re

# Data/protocol repair only; no strategy parameter or signal logic is changed.
# The prior final patch requested April 2020, but the partitioned real-tick
# mirror begins in 2021. Replace that unavailable window and the now-observed
# April 2025 window with two previously unused, data-available blind windows.
# They remain outside the development and validation date ranges.
runner_path = Path("xau_lab/hf_window_runner.py")
runner = runner_path.read_text(encoding="utf-8")

windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2021_jan_blind", "holdout", "2021-01-11", "2021-01-30"),
    ("hold_2024_dec_blind", "holdout", "2024-12-02", "2024-12-21"),
]'''

runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not install data-available blind holdout protocol")

runner_path.write_text(runner, encoding="utf-8")
print("Replaced unavailable/observed holdouts with blind January 2021 and December 2024 windows")
