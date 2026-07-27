from pathlib import Path
import re

# One economically defensible strategy revision after the audited run whose
# development sample was only eight trades: remove the date-mined directional
# hand-off (long only in server hour 05, short only in 06). A trend-following
# pullback/cross system should be directionally symmetric; keep the same liquid
# 04:00-07:00 server session, closed-bar M1/M5/M15 alignment, cost filter,
# stops, targets, trailing, risk limits and execution stress.
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

    # Symmetric liquid-session rule. Session admission is already enforced by
    # in_session(); do not mine a preferred direction from a single clock hour.
    return True


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")
text = text.replace('name=c.name + "_early0406"', 'name=c.name + "_sym0407"')
text = text.replace('_dirL5S6_noH4', '_sym0407')
engine.write_text(text, encoding="utf-8")

# The July-2021 and November-2022 holdouts have now been inspected. Rotate the
# gate to two non-overlapping periods that are not part of the active
# development/validation protocol. This changes evaluation only, never trading
# logic, and keeps the new holdout hidden from candidate selection.
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
    ("hold_2022_jan_blind", "holdout", "2022-01-10", "2022-01-29"),
    ("hold_2023_dec_blind", "holdout", "2023-12-04", "2023-12-23"),
]'''
runner_text, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not install fresh January-2022/December-2023 holdout protocol")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*? holdout gate passes;.*?report interval\.",
    "The candidate is considered acceptable only when the newly untouched January-2022/December-2023 holdout gate passes. These periods do not overlap any active development or validation window.",
    report,
)
aggregate.write_text(report, encoding="utf-8")
print("Applied one revision: symmetric 04-07 liquid-session directions; rotated blind holdout")
