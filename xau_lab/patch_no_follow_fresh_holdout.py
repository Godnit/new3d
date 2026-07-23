from pathlib import Path
import re

engine_path = Path("xau_lab/real_tick_lab.py")
engine = engine_path.read_text(encoding="utf-8")

# One simple strategy revision for this iteration:
# remove FOLLOW entries, which re-enter after the first EMA9 transition and
# showed materially negative expectancy in development + 2024 validation.
# Keep CROSS and CONT continuation setups, all spread/risk/session rules, and
# all exit logic unchanged.
if 'name="rev_no_follow"' not in engine:
    boundary = engine.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = engine.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return not found")

    candidate = '''    out.append(
        replace(
            base,
            name="rev_no_follow",
            baseline_hour_rules=False,
            session_start=12,
            session_end=21,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="off",
            min_body_atr=0.06,
            stop_atr=1.25,
            rr=1.20,
            be_trigger=0.80,
            be_lock_atr=0.05,
            trail_start=1.20,
            trail_atr=0.80,
            fail_fast_minutes=4,
            fail_fast_max_mfe_r=0.30,
            fail_fast_current_r=-0.10,
            close_extreme_fraction=0.55,
        )
    )
'''
    engine = engine[:return_pos] + candidate + engine[return_pos:]

anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'c.name.startswith("rev_no_follow")' not in engine:
    if anchor not in engine:
        raise SystemExit("signal anchor not found")
    replacement = '''    if c.name.startswith("rev_no_follow"):
        buy_trigger = cross_buy or cont_buy
        sell_trigger = cross_sell or cont_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    engine = engine.replace(anchor, replacement, 1)

engine_path.write_text(engine, encoding="utf-8")
print("Applied one strategy revision: disable FOLLOW entries; retain CROSS and CONT")

# Rotate to two exact, previously uninspected late-month 2025 windows. These
# windows are not used for selection; they remain holdout-only until this run.
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
    ("hold_2025_apr_late", "holdout", "2025-04-21", "2025-05-03"),
    ("hold_2025_nov_late", "holdout", "2025-11-17", "2025-11-29"),
]'''
runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not rotate fresh late-April/late-November holdout")
runner_path.write_text(runner, encoding="utf-8")
print("Rotated to fresh late-April and late-November 2025 holdout windows")

aggregate_path = Path("xau_lab/aggregate_results.py")
report = aggregate_path.read_text(encoding="utf-8")
report = re.sub(
    r"The previously inspected .*? holdout gate passes\.",
    "All previously inspected 2025 windows are retired from holdout use. The candidate is considered acceptable only when the newly untouched late-April/late-November 2025 holdout gate passes.",
    report,
)
aggregate_path.write_text(report, encoding="utf-8")
