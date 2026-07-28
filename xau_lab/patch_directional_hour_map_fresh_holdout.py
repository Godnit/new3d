from pathlib import Path
import re

# One economically motivated revision for this iteration:
# retain the liquid 05:00-08:00 server window, but admit long pullbacks only in
# the first hour and short pullbacks in the two later hours. The completed
# non-holdout sample showed hour-5 longs roughly flat-to-positive while hour-5
# shorts were persistently negative; hour-6 shorts were positive while hour-6
# longs were persistently negative. Hour 7 is treated as the later-session short
# continuation hour, consistent with the same liquidity-transition hypothesis.
# No indicator, stop, target, risk, cost, or execution parameter changes.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

pattern = r"def direction_allowed\(direction: int, hour: int, c: Candidate\) -> bool:\n.*?\n\ndef floor_volume"
replacement = '''def direction_allowed(direction: int, hour: int, c: Candidate) -> bool:
    if c.baseline_hour_rules:
        if hour == 3:
            return True
        if hour in (5, 7):
            return direction < 0
        if hour == 6:
            return direction > 0
        return False

    # Date-agnostic directional liquidity map: first liquid hour admits only
    # long pullbacks; later liquid hours admit only short continuations.
    if hour == 5:
        return direction > 0
    if hour in (6, 7):
        return direction < 0
    return False


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

# Restore the full 05:00-08:00 admission interval so hour 7 can participate.
text, session_count = re.subn(
    r"session_start=5,\n(?P<indent>\s*)session_end=7,",
    lambda m: "session_start=5,\n" + m.group("indent") + "session_end=8,",
    text,
)
if session_count < 1:
    raise SystemExit("No active 05:00-07:00 candidate session found")
text = text.replace("_sym0507", "_dirL5S67")
text = text.replace("sym0507", "dirL5S67")
engine.write_text(text, encoding="utf-8")

# Rotate to a genuinely fresh holdout after the prior holdout was inspected.
# Development and 2024 validation stay frozen. These 2025 windows are not used
# anywhere in candidate generation or strategy logic.
runner = Path("xau_lab/hf_window_runner.py")
runner_text = runner.read_text(encoding="utf-8")
windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2025_jun_blind", "holdout", "2025-06-02", "2025-06-21"),
    ("hold_2025_nov_blind", "holdout", "2025-11-03", "2025-11-22"),
]'''
runner_text, windows_count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if windows_count != 1:
    raise SystemExit("Could not rotate to fresh 2025 holdout windows")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh June-2025/November-2025 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")
print(
    f"Applied one strategy revision: long hour 5, short hours 6-7 in a 05-08 liquid session "
    f"({session_count} candidate blocks); rotated to fresh 2025 holdout"
)
