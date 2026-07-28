from pathlib import Path
import re

# One simple, date-agnostic strategy revision after run 489 failed statistically.
# The development and validation sample was too sparse (11 total trades) because
# the final strategy admitted entries only from 05:00-05:59 server time. Keep
# direction, signals, strict M15 trend, stops, targets, risk, spread, slippage,
# and chronology unchanged; widen only the liquid-session horizon to 05:00-07:59.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

pattern = r"def in_session\(hour: int, c: Candidate\) -> bool:\n.*?\n\ndef direction_allowed"
replacement = '''def in_session(hour: int, c: Candidate) -> bool:
    if c.baseline_hour_rules:
        return hour in (3, 5, 6, 7)

    # Single revision for this iteration: retain the London-open liquid core,
    # but use three complete server hours instead of only the first hour.
    # No calendar date or holdout result enters this rule.
    return 5 <= hour < 8


def direction_allowed'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one in_session function, replaced {count}")

if "_session0508Fresh" not in text:
    boundary = re.search(r"(?m)^def in_session\(", text)
    if not boundary:
        raise SystemExit("Could not locate in_session boundary for candidate naming")
    wrapper = '''_candidates_before_session_0508_fresh = candidates

def candidates() -> list[Candidate]:
    return [
        replace(c, name=c.name + "_session0508Fresh")
        for c in _candidates_before_session_0508_fresh()
    ]


'''
    text = text[:boundary.start()] + wrapper + text[boundary.start():]
engine.write_text(text, encoding="utf-8")

# The previously reported June-2024/February-2025 holdout is now observed.
# Rotate only the evaluation protocol to two non-overlapping periods that are
# not referenced by strategy logic. This is not an additional strategy change.
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
    ("hold_2021_may_fresh", "holdout", "2021-05-24", "2021-06-05"),
    ("hold_2022_dec_fresh", "holdout", "2022-12-05", "2022-12-24"),
]'''
runner_text, windows_count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    new_windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if windows_count != 1:
    raise SystemExit("Could not install fresh May-2021/December-2022 holdout")
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

print("Applied one strategy revision: widened the unchanged long-only liquid session from 05-06 to 05-08; installed a fresh non-overlapping holdout protocol")
