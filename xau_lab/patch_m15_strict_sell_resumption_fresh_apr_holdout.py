from pathlib import Path
import re

# One simple strategy revision for this iteration:
# require the existing sell-side continuation/follow-through setup to agree
# with the closed M15 downtrend. This is a standard multi-timeframe trend
# confirmation intended to avoid selling countertrend rallies; it adds no
# date-, month-, weekday-, or broker-specific rule.
engine_path = Path("xau_lab/real_tick_lab.py")
engine = engine_path.read_text(encoding="utf-8")

if 'name="rev_global_sell_cont_follow_m15strict"' not in engine:
    boundary = engine.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = engine.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return not found")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_global_sell_cont_follow_m15strict",
            baseline_hour_rules=False,
            session_start=0,
            session_end=0,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="strict",
            stop_atr=1.15,
            rr=1.10,
            be_trigger=0.55,
            be_lock_atr=0.05,
            trail_start=0.90,
            trail_atr=0.65,
            fail_fast_minutes=3,
            fail_fast_max_mfe_r=0.25,
            fail_fast_current_r=-0.05,
            close_extreme_fraction=0.55,
            max_spread_price=1.20,
            max_spread_atr=0.65,
        )
    )
'''
    engine = engine[:return_pos] + candidate + engine[return_pos:]

if engine.count('name="rev_global_sell_cont_follow_m15strict"') != 1:
    raise SystemExit("M15-strict candidate integrity check failed")
engine_path.write_text(engine, encoding="utf-8")
print("Added M15-strict global sell continuation/follow candidate")

# The previous Feb/Mar 2025 holdout has now been observed. Rotate to two
# windows not used by earlier runs: April 2020 and April 2025. The strategy
# change above was chosen from development/validation diagnostics only; these
# windows remain sealed until the aggregate gate evaluates them.
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
    ("hold_2020_apr", "holdout", "2020-04-06", "2020-04-25"),
    ("hold_2025_apr", "holdout", "2025-04-07", "2025-04-26"),
]'''
runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not rotate to fresh April holdout windows")
runner_path.write_text(runner, encoding="utf-8")
print("Applied fresh April 2020/2025 holdout protocol")
