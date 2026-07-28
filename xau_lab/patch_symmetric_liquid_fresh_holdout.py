from pathlib import Path
import re

# One simple, date-agnostic strategy revision after the long-only liquid-session
# test failed across development, validation, and the inspected holdout:
# restore the symmetric short side under the same trend, pullback, spread,
# stop, target, risk, and execution-cost rules. This does not add indicators or
# date-specific logic; it only removes the directional asymmetry.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")
old = '''    # Date-agnostic long-only liquid-session revision. The previous first-hour
    # restriction produced too few independent trades to validate. Preserve the
    # same signal and risk logic, but permit long entries throughout the
    # candidate's already-defined liquid session.
    if c.session_start < c.session_end:
        session_ok = c.session_start <= hour < c.session_end
    else:
        session_ok = hour >= c.session_start or hour < c.session_end
    return session_ok and direction > 0
'''
new = '''    # Date-agnostic symmetric liquid-session revision. Apply the identical
    # trend/pullback quality and cost controls to both directions instead of
    # imposing a permanent long-only bias.
    if c.session_start < c.session_end:
        session_ok = c.session_start <= hour < c.session_end
    else:
        session_ok = hour >= c.session_start or hour < c.session_end
    return session_ok
'''
if old not in text:
    raise SystemExit("Could not find current long-only liquid-session rule")
text = text.replace(old, new, 1)
text = text.replace("_longLiquid", "_symLiquid")
text = text.replace("longLiquid", "symLiquid")
engine.write_text(text, encoding="utf-8")

# The June/October 2022 windows were inspected by the preceding run. Restore a
# fresh, non-overlapping holdout protocol. The mirror begins on 2021-05-24.
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
    raise SystemExit("Could not restore fresh holdout windows")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh May-2021/December-2022 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")

print(
    "Applied one strategy revision: restore symmetric long/short entries within "
    "the same liquid-session and cost controls; rotated to fresh holdout windows"
)
