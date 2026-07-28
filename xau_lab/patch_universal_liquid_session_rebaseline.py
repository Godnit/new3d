from pathlib import Path
import re

# One simple, economically motivated revision after the narrow 05:00-only,
# long-only candidate failed development, validation, and untouched holdout.
# Replace date-derived direction/hour rules with a universal two-sided liquid
# session and one fixed trend-pullback configuration. No holdout result enters
# the trading rule or parameter choice.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

# Symmetric direction permission for all non-baseline research candidates.
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

    # Universal symmetric trend participation. Session and trend filters still
    # control when and in which direction a signal can open.
    return direction != 0


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

# Ensure the session is derived only from candidate fields, including windows
# that cross midnight, rather than any historical hour map.
pattern = r"def in_session\(hour: int, c: Candidate\) -> bool:\n.*?\n\ndef direction_allowed"
replacement = '''def in_session(hour: int, c: Candidate) -> bool:
    if hour == c.blocked_hour:
        return False
    if c.session_start == c.session_end:
        return True
    if c.session_start < c.session_end:
        return c.session_start <= hour < c.session_end
    return hour >= c.session_start or hour < c.session_end


def direction_allowed'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one in_session function, replaced {count}")

# Install one fixed, date-agnostic rebaseline. Server hours 08:00-16:59 span
# the liquid European morning into early US participation without selecting a
# single lucky historical hour. M15 veto avoids trading directly against the
# larger trend while keeping more opportunities than a strict alignment rule.
boundary = re.search(r"(?m)^def in_session\(", text)
if not boundary:
    raise SystemExit("Could not locate in_session boundary")
wrapper = '''_candidates_before_universal_liquid_rebaseline = candidates

def candidates() -> list[Candidate]:
    source = _candidates_before_universal_liquid_rebaseline()
    if not source:
        raise RuntimeError("No source candidate available")
    base = source[0]
    return [replace(
        base,
        name="universal_liquid_cross_follow_v1",
        baseline_hour_rules=False,
        session_start=8,
        session_end=17,
        blocked_hour=24,
        signal_mode="cross_follow",
        m15_mode="veto",
        stop_atr=1.50,
        rr=1.50,
        be_trigger=0.80,
        be_lock_atr=0.04,
        trail_start=1.20,
        trail_atr=0.80,
        fail_fast_minutes=100000,
        fail_fast_max_mfe_r=-999.0,
        fail_fast_current_r=-999.0,
        min_body_atr=0.10,
        max_body_atr=1.10,
        max_entry_distance_atr=1.00,
        max_spread_price=999.0,
        max_spread_atr=0.35,
        cooldown_minutes=3,
        max_trades_daily=8,
    )]


'''
text = text[:boundary.start()] + wrapper + text[boundary.start():]
engine.write_text(text, encoding="utf-8")

# The previously untouched May-2021/December-2022 holdout is now observed.
# Rotate only the evaluation protocol to two non-overlapping 2025 weeks that
# are not referenced by this strategy. Development and validation stay fixed.
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
    ("hold_2025_may_fresh", "holdout", "2025-05-05", "2025-05-17"),
    ("hold_2025_dec_fresh", "holdout", "2025-12-01", "2025-12-13"),
]'''
runner_text, windows_count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    new_windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if windows_count != 1:
    raise SystemExit("Could not install fresh May/December 2025 holdout")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh May/December 2025 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")

print("Applied one revision: universal symmetric 08-17 liquid-session trend-pullback rebaseline; rotated only the untouched holdout")
