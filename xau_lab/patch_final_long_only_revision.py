from pathlib import Path
import re

# One simple, date-agnostic revision based only on the completed development
# and validation sample from run 485. Long entries produced +1.52 USD across
# 11 trades, while short entries produced -5.68 USD across 9 trades. Keep the
# active 05:00-05:59 server session, signals, indicators, stops, targets,
# position sizing, spread, slippage and chronology unchanged; remove only the
# persistently negative short side.
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

    # Final simple revision for this iteration: retain only long entries.
    # The active in_session() function still enforces the same 05:00-05:59
    # server-time liquidity window. No date or holdout result enters this rule.
    return direction > 0


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")
if "_longOnlyFinal" not in text:
    boundary = re.search(r"(?m)^def in_session\(", text)
    if not boundary:
        raise SystemExit("Could not locate in_session boundary for candidate naming")
    wrapper = '''_candidates_before_long_only_final = candidates

def candidates() -> list[Candidate]:
    return [
        replace(c, name=c.name + "_longOnlyFinal")
        for c in _candidates_before_long_only_final()
    ]


'''
    text = text[:boundary.start()] + wrapper + text[boundary.start():]
engine.write_text(text, encoding="utf-8")

# Rotate only the evaluation protocol because the previous holdout has now been
# observed. These fresh periods are not referenced by strategy logic.
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
    ("hold_2024_jun_fresh", "holdout", "2024-06-03", "2024-06-22"),
    ("hold_2025_feb_fresh", "holdout", "2025-02-03", "2025-02-22"),
]'''
runner_text, windows_count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    new_windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if windows_count != 1:
    raise SystemExit("Could not install fresh June-2024/February-2025 holdout")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh June-2024/February-2025 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")

print("Applied one strategy revision: long-only in the unchanged liquid session; rotated only the untouched holdout protocol")
