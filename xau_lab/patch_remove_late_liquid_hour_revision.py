from pathlib import Path
import re

# Existing baseline rule retained from the preceding iteration: the final
# liquid-session hour was removed because it was negative in both development
# and validation. This is not a new change in the present iteration.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")
old = '''    return session_ok
'''
new = '''    # Keep the same setup but stop before the final liquid-session hour.
    return session_ok and hour < 7
'''
if old in text:
    text = text.replace(old, new, 1)
text = text.replace("_symLiquid", "_symCore")
text = text.replace("symLiquid", "symCore")

# One new, economically interpretable strategy revision for this iteration:
# allow only short entries. In the completed development+validation sample,
# long trades had negative expectancy while shorts were approximately
# break-even/positive. All indicators, signal construction, stops, targets,
# spread stress, slippage and risk sizing remain unchanged.
dispatch = '''    if buy:
        name = "CROSS_BUY" if cross_buy else ("FOLLOW_BUY" if follow_buy else "CONT_BUY")
        return 1, name, atr
    if sell:
'''
short_only = '''    # Current iteration: directional asymmetry, short entries only.
    buy = False

    if buy:
        name = "CROSS_BUY" if cross_buy else ("FOLLOW_BUY" if follow_buy else "CONT_BUY")
        return 1, name, atr
    if sell:
'''
if dispatch not in text:
    raise SystemExit("Could not find final signal dispatch for short-only revision")
text = text.replace(dispatch, short_only, 1)
text = text.replace("_symCore", "_shortCore")
text = text.replace("symCore", "shortCore")
engine.write_text(text, encoding="utf-8")

# Evaluation protocol only: use non-overlapping available windows that were not
# part of the immediately preceding February/September-2025 holdout decision.
# Dates are never visible to the signal logic.
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
    ("hold_2021_may_available", "holdout", "2021-05-24", "2021-06-05"),
    ("hold_2022_dec", "holdout", "2022-12-01", "2022-12-20"),
]'''
runner_text, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not install non-overlapping holdout protocol")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the non-overlapping May-2021/December-2022 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")

print(
    "Retained the prior liquid-core hour rule; applied one new strategy "
    "revision (short-only); installed non-overlapping holdout windows"
)
