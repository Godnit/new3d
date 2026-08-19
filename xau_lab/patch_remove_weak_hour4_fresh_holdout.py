from pathlib import Path
import re

# One simple, date-agnostic strategy revision based only on development and
# validation results from run 401. Server hour 04 produced 22 non-holdout
# trades with -2.36 USD net and a materially sub-1 profit factor, while hour 05
# was positive and hour 06 shorts were positive in validation. Remove only
# hour-04 long entries; retain the same signals, closed-bar trend logic, stop,
# target, risk, spread, adverse slippage and daily protections.
engine_path = Path("xau_lab/real_tick_lab.py")
text = engine_path.read_text(encoding="utf-8")
old = '''    # Directional liquidity hand-off rule: long pullback resumptions during
    # hours 04-05, then short resumptions in hour 06. All existing closed-bar
    # trend, body, distance and execution-cost checks still apply.
    if direction > 0:
        return hour in (4, 5)
    return hour == 6
'''
new = '''    # Cost-aware liquidity hand-off rule: wait through the thinner 04:00
    # opening segment, allow long pullback resumptions in hour 05, and short
    # resumptions in hour 06. All closed-bar trend, body, distance and
    # execution-cost checks remain unchanged.
    if direction > 0:
        return hour == 5
    return hour == 6
'''
if text.count(old) != 1:
    raise SystemExit(f"Expected exactly one directional hour rule, found {text.count(old)}")
text = text.replace(old, new, 1)
text = text.replace('name=c.name + "_dirL45S6"', 'name=c.name + "_dirL5S6_noH4"')
engine_path.write_text(text, encoding="utf-8")

# The previous May-2021/December-2022 holdouts are now observed. Rotate only
# the evaluation protocol to two previously unused, non-overlapping windows.
# No date enters trading logic and no parameter is selected from these windows.
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
    ("hold_2021_jul_blind", "holdout", "2021-07-05", "2021-07-24"),
    ("hold_2022_nov_blind", "holdout", "2022-11-07", "2022-11-26"),
]'''
runner, count = re.subn(r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months", windows + "\n\n\ndef iter_months", runner, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not install fresh July-2021/November-2022 holdout protocol")
runner_path.write_text(runner, encoding="utf-8")

print("Applied one revision: remove weak hour-04 longs; fresh blind holdouts installed")
