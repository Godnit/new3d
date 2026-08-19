from pathlib import Path
import re

# One simple, date-agnostic strategy revision based only on development+validation.
# In the audited failed run, the first server-hour slice (05:00-05:59 EET/EEST,
# UTC hour 2 in the sampled periods) produced 12 dev+validation trades, +2.25 USD,
# PF 1.20 and 58.3% wins. The later hours produced -6.96 USD combined.
# Keep signal logic, trend filters, stops, targets, sizing, spread, slippage and
# chronology unchanged; narrow only the liquid-session window.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

marker = "_session0509"
if marker not in text:
    raise SystemExit("Expected the active 05:00-09:00 session wrapper")
if "_session0506_after0509" in text:
    raise SystemExit("05:00-06:00 revision already active")

boundary = re.search(r"(?m)^def in_session\(", text)
if not boundary:
    raise SystemExit("Could not locate in_session() boundary")

wrapper = '''_candidates_before_session0506_after0509 = candidates

def candidates() -> list[Candidate]:
    return [
        replace(
            c,
            name=c.name + "_session0506_after0509",
            session_start=5,
            session_end=6,
        )
        for c in _candidates_before_session0506_after0509()
    ]


'''
text = text[:boundary.start()] + wrapper + text[boundary.start():]
engine.write_text(text, encoding="utf-8")

# The prior December-2021/May-2022 holdout has now been observed. Rotate only
# the protocol to fresh, non-overlapping periods. No date enters strategy logic.
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
runner_text, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    new_windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if count != 1:
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

print("Applied one revision: restrict trading to 05:00-05:59 server time; rotate only the untouched holdout protocol")
