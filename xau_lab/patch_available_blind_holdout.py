from pathlib import Path
import re

# Data/protocol repair only; no strategy parameter, signal, or execution logic
# is changed. The partitioned mirror starts in May 2021, so the prior January
# 2021 blind window cannot run. The December 2024 window has already produced
# an artifact in the failed protocol run and is therefore no longer blind.
# Replace both with two data-available periods that do not appear in any prior
# development, validation, or holdout protocol on this branch.
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
    ("hold_2022_jun_blind", "holdout", "2022-06-06", "2022-06-25"),
    ("hold_2024_jun_blind", "holdout", "2024-06-03", "2024-06-22"),
]'''

runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not install fresh data-available blind holdout protocol")

runner_path.write_text(runner, encoding="utf-8")
print("Installed fresh available holdouts: June 2022 and June 2024")
