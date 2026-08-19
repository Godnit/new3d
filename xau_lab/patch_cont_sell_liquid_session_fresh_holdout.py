from pathlib import Path
import re

engine_path = Path("xau_lab/real_tick_lab.py")
engine = engine_path.read_text(encoding="utf-8")

# One simple, economically defensible strategy revision for this iteration:
# retain the only signal family that had positive development and validation
# expectancy (sell continuation), but broaden its session from 13-21 to 07-22
# server time. This covers the London and New York liquidity windows and is not
# tied to a date, month, or holdout outcome. Entry, exit, risk and spread rules
# remain identical to rev_cont_sell_only.
if 'name="rev_cont_sell_liquid_session"' not in engine:
    boundary = engine.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = engine.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return not found")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_cont_sell_liquid_session",
            baseline_hour_rules=False,
            session_start=7,
            session_end=22,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="off",
            stop_atr=1.15,
            rr=1.10,
            be_trigger=0.55,
            be_lock_atr=0.05,
            trail_start=0.90,
            trail_atr=0.65,
            fail_fast_minutes=3,
            fail_fast_max_mfe_r=0.25,
            fail_fast_current_r=-0.05,
            close_extreme_fraction=0.65,
        )
    )
'''
    engine = engine[:return_pos] + candidate + engine[return_pos:]

anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'c.name.startswith("rev_cont_sell_liquid_session")' not in engine:
    if anchor not in engine:
        raise SystemExit("signal anchor not found")
    replacement = '''    if c.name.startswith("rev_cont_sell_liquid_session"):
        buy_trigger = False
        sell_trigger = cont_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    engine = engine.replace(anchor, replacement, 1)

engine_path.write_text(engine, encoding="utf-8")
print("Added sell-continuation candidate across London/New York liquidity hours")

# Retire every previously inspected 2025 holdout window. February and March
# 2025 have not appeared in any earlier holdout patch on this branch. They are
# kept selection-blind and are used only after development + 2024 validation.
runner_path = Path("xau_lab/hf_window_runner.py")
runner = runner_path.read_text(encoding="utf-8")
windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2025_feb", "holdout", "2025-02-03", "2025-02-22"),
    ("hold_2025_mar", "holdout", "2025-03-03", "2025-03-22"),
]'''
runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not rotate to fresh February/March 2025 holdout")
runner_path.write_text(runner, encoding="utf-8")

aggregate_path = Path("xau_lab/aggregate_results.py")
report = aggregate_path.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*? holdout gate passes\.",
    "The candidate is considered acceptable only when the newly untouched February/March 2025 holdout gate passes.",
    report,
)
aggregate_path.write_text(report, encoding="utf-8")
print("Rotated to untouched February/March 2025 holdout windows")
