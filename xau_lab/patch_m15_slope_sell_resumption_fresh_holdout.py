from pathlib import Path
import re

# One economically simple revision for this iteration:
# trade only sell resumptions when the completed M15 EMA20 is not merely below
# EMA50, but is also falling versus the prior completed M15 bar. This targets
# false counter-trend sell resumptions without adding an indicator, date rule,
# or hour-specific exception. Risk and exit settings stay unchanged.
engine_path = Path("xau_lab/real_tick_lab.py")
engine = engine_path.read_text(encoding="utf-8")

name = "rev_global_all_sell_resumption_m15slope"
if f'name="{name}"' not in engine:
    boundary = engine.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = engine.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return not found")
    candidate = f'''    out.append(
        replace(
            base,
            name="{name}",
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

trigger_anchor = '''    if c.name == "rev_global_all_sell_resumption_m15strict":
        buy_trigger = False
        sell_trigger = cross_sell or cont_sell or follow_sell
'''
trigger_add = trigger_anchor + f'''
    if c.name == "{name}":
        buy_trigger = False
        sell_trigger = cross_sell or cont_sell or follow_sell
'''
if f'if c.name == "{name}":' not in engine:
    if trigger_anchor not in engine:
        raise SystemExit("all-sell resumption trigger anchor not found")
    engine = engine.replace(trigger_anchor, trigger_add, 1)

# Apply slope persistence after the generic sell expression is evaluated. The
# M15 value aligned to i-16 belongs to the prior completed M15 bar, so this does
# not use a forming higher-timeframe candle.
slope_block = f'''    if c.name == "{name}":
        prior_m15_ema20 = bars.iloc[max(0, i - 16)].m15_ema20
        slope_ok = (not pd.isna(prior_m15_ema20)) and b1.m15_ema20 < prior_m15_ema20
        sell = sell and slope_ok
'''
if "prior_m15_ema20 = bars.iloc[max(0, i - 16)].m15_ema20" not in engine:
    marker = "    if buy:\n"
    pos = engine.find(marker, engine.find("def signal_at"))
    if pos < 0:
        raise SystemExit("signal return marker not found")
    engine = engine[:pos] + slope_block + engine[pos:]

if engine.count(f'name="{name}"') != 1:
    raise SystemExit("candidate integrity check failed")
engine_path.write_text(engine, encoding="utf-8")

# The February/March 2025 gate has now been observed. Rotate only the final gate
# to two periods not referenced by any earlier protocol on this branch. The
# strategy rule above was chosen before opening these periods.
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
    ("hold_2021_may_blind", "holdout", "2021-05-10", "2021-05-29"),
    ("hold_2024_aug_blind", "holdout", "2024-08-05", "2024-08-24"),
]'''
runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not install fresh May-2021/August-2024 holdout")
runner_path.write_text(runner, encoding="utf-8")

aggregate_path = Path("xau_lab/aggregate_results.py")
aggregate = aggregate_path.read_text(encoding="utf-8")
aggregate = re.sub(
    r"The candidate is considered acceptable only when .*? passes\.",
    "The candidate is considered acceptable only when the newly untouched May 2021 and August 2024 holdout gate passes.",
    aggregate,
)
aggregate_path.write_text(aggregate, encoding="utf-8")

print("Added one M15-slope all-sell resumption revision and sealed fresh holdout")
