from pathlib import Path
import re

# One simple, date-agnostic strategy revision based only on the frozen
# development + validation trades from the preceding run: the final session
# hour (server hour 7) was negative in both splits. Remove that late hour while
# preserving signals, indicators, stops, targets, risk, spread and slippage.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")
old = '''    return session_ok
'''
new = '''    # Keep the same symmetric setup but stop before the final liquid-session
    # hour, whose later-session reversals were negative in both development and
    # validation. This rule is clock-based and contains no calendar date.
    return session_ok and hour < 7
'''
if old not in text:
    raise SystemExit("Could not find the symmetric session return")
text = text.replace(old, new, 1)
text = text.replace("_symLiquid", "_symCore")
text = text.replace("symLiquid", "symCore")
engine.write_text(text, encoding="utf-8")

# Rotate to two fresh, non-overlapping 2025 holdout windows. These dates are
# evaluation protocol only and are never visible to the signal logic.
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
    ("hold_2025_feb_fresh", "holdout", "2025-02-03", "2025-02-22"),
    ("hold_2025_sep_fresh", "holdout", "2025-09-01", "2025-09-20"),
]'''
runner_text, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not rotate to fresh 2025 holdout windows")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh February-2025/September-2025 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")

print(
    "Applied one strategy revision: removed server hour 7 from the unchanged "
    "symmetric liquid-session setup; rotated to fresh 2025 holdout windows"
)
