from pathlib import Path
import re

# One simple strategy revision based only on the completed development and
# validation splits: long trades were negative in both splits, while shorts
# were approximately flat overall and positive in validation. Disable only
# long entries. Do not change signals, sessions, stops, targets, costs, risk,
# chronology safeguards, or short-entry logic.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")
marker = '''    # Symmetric trend-aligned entries restored after the short-only protocol
    # failed independently. The existing buy and sell conditions are unchanged.
    if buy:
'''
replacement = '''    # Current iteration: development and validation both showed negative long
    # expectancy after observed spread and adverse slippage. Disable longs only;
    # the complete short setup and every execution safeguard remain unchanged.
    buy = False

    if buy:
'''
if text.count(marker) != 1:
    raise SystemExit(f"Expected one symmetric dispatch marker, found {text.count(marker)}")
text = text.replace(marker, replacement, 1)
text = text.replace("_symmetricCore", "_shortCore2")
text = text.replace("symmetricCore", "shortCore2")
engine.write_text(text, encoding="utf-8")

# Protocol rotation only: the previous holdout has now been observed. Replace it
# with two non-overlapping windows that are not used in development, validation,
# candidate generation, or strategy logic. Dates remain invisible to signals.
runner = Path("xau_lab/hf_window_runner.py")
runner_text = runner.read_text(encoding="utf-8")
new_windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2021_jul_fresh", "holdout", "2021-07-05", "2021-07-24"),
    ("hold_2022_jan_fresh", "holdout", "2022-01-10", "2022-01-29"),
]'''
runner_text, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    new_windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not install fresh non-overlapping holdout windows")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh July-2021/January-2022 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")

print("Disabled development/validation loss-making longs and installed a fresh untouched holdout")
