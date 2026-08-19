from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision after the latest development
# and validation failure: remove server hours 07 and 08, which were negative
# in both splits, while retaining the earlier European-session hours 04-06.
# Signals, M5/M15 filters, stops, targets, risk, observed spread, adverse
# slippage and position-management logic are unchanged.
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

    # Earlier European-session window. Both directions remain subject to all
    # existing closed-bar trend and signal confirmations.
    return hour in (4, 5, 6)


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

old_block = '''                name=c.name + "_sym567",
                baseline_hour_rules=False,
                session_start=5,
                session_end=7,
                blocked_hour=24,
'''
new_block = '''                name=c.name + "_early0406",
                baseline_hour_rules=False,
                session_start=4,
                session_end=7,
                blocked_hour=24,
'''
if text.count(old_block) != 1:
    raise SystemExit(f"Expected one stale 05:00-06:59 candidate block, found {text.count(old_block)}")
text = text.replace(old_block, new_block, 1)
path.write_text(text, encoding="utf-8")

# The former holdout windows have already been inspected in prior iterations.
# To restore an honest blind gate, keep development and 2024 validation frozen
# and reserve two previously unused 2026 periods before the Headway June-August
# report interval. These dates are evaluation protocol only, never signal rules.
runner_path = Path("xau_lab/hf_window_runner.py")
runner = runner_path.read_text(encoding="utf-8")
new_windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2026_feb_blind", "holdout", "2026-02-09", "2026-02-28"),
    ("hold_2026_may_blind", "holdout", "2026-05-04", "2026-05-23"),
]
'''
runner, count = re.subn(r"WINDOWS = \[\n.*?\n\]\n", new_windows, runner, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not install fresh February/May 2026 holdout windows")
runner_path.write_text(runner, encoding="utf-8")

aggregate_path = Path("xau_lab/aggregate_results.py")
aggregate = aggregate_path.read_text(encoding="utf-8")
aggregate = re.sub(
    r"The candidate is considered acceptable only when .*? holdout gate passes\.",
    "The candidate is considered acceptable only when the newly untouched February/May 2026 holdout gate passes; these periods do not overlap the Headway June-August 2026 report interval.",
    aggregate,
)
aggregate_path.write_text(aggregate, encoding="utf-8")

print("Applied one revision: removed weak hours 07-08 and opened a fresh blind 2026 gate")
