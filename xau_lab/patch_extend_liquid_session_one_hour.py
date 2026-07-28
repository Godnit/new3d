from pathlib import Path
import re

# One simple, date-agnostic strategy revision for this iteration.
# The completed cost-aware real-tick run produced only 14 development trades
# across six independent windows, so its side and signal comparisons collapsed
# to the same tiny sample. Extend the existing liquid-session end by one server
# hour (05:00-08:00 -> 05:00-09:00 EET/EEST). This keeps the same trend,
# pullback, spread, adverse-slippage, stop, target, sizing, and chronology rules.
# Economically, it includes the next hour of the London morning rather than
# adding an indicator or a date-specific exception.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

if "_session0509" in text:
    raise SystemExit("The 05:00-09:00 liquid-session revision is already active")

pattern = r"(?m)^def in_session\("
match = re.search(pattern, text)
if not match:
    raise SystemExit("Could not locate in_session() boundary")

wrapper = '''_candidates_before_session0509 = candidates

def candidates() -> list[Candidate]:
    return [
        replace(
            c,
            name=c.name + "_session0509",
            session_start=5,
            session_end=9,
        )
        for c in _candidates_before_session0509()
    ]


'''
text = text[:match.start()] + wrapper + text[match.start():]
engine.write_text(text, encoding="utf-8")

# The previously untouched November-2021/July-2022 holdout has now been
# observed. Rotate only the protocol to two non-overlapping periods that are not
# used in development or validation and are invisible to strategy logic.
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
    ("hold_2021_dec_fresh", "holdout", "2021-12-01", "2021-12-20"),
    ("hold_2022_may_fresh", "holdout", "2022-05-02", "2022-05-21"),
]'''
runner_text, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    new_windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not install fresh December-2021/May-2022 holdout windows")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh December-2021/May-2022 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")

print(
    "Applied one revision: extend the unchanged cost-aware symmetric strategy "
    "through 09:00 server time to increase independent sample size; fresh holdout rotated"
)
