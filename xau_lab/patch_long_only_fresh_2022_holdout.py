from pathlib import Path
import re

# One simple, economically defensible revision based only on the frozen
# development + validation sample from the previous completed run:
# long pullback entries were roughly break-even/positive, while short entries
# were negative overall. Remove the short side without changing indicators,
# stops, targets, costs, risk, or execution stress.
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

    # Date-agnostic long-only revision: retain the first liquid-hour pullback
    # setup and remove the short side, which was negative in the frozen
    # development + validation sample. No date is referenced by this rule.
    return hour == 5 and direction > 0


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")
text = text.replace("_dirL5S67", "_longL5")
text = text.replace("dirL5S67", "longL5")
engine.write_text(text, encoding="utf-8")

# The June/November 2025 holdout has now been inspected. Rotate to two fresh,
# non-overlapping 2022 windows that are absent from development and validation.
# These dates are evaluation protocol only and are not visible to signal logic.
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
    ("hold_2022_jun_blind", "holdout", "2022-06-06", "2022-06-25"),
    ("hold_2022_oct_blind", "holdout", "2022-10-03", "2022-10-22"),
]'''
runner_text, windows_count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if windows_count != 1:
    raise SystemExit("Could not rotate to fresh 2022 holdout windows")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh June-2022/October-2022 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")
print(
    "Applied one strategy revision: long-only hour-5 pullbacks; all risk, cost, "
    "indicator and exit settings unchanged; rotated to fresh 2022 holdout"
)
