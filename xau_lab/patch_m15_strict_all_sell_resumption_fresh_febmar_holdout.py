from pathlib import Path
import re

# One simple strategy revision for this iteration, chosen from development and
# 2024 validation diagnostics only: the sell continuation/follow candidate was
# the only family positive in both splits, and M15 strict confirmation improved
# its profit factor. Add EMA9 cross-back sells to the same M15-confirmed
# resumption family to increase the sample without adding date/hour rules or a
# new indicator. Risk and exit parameters remain unchanged.
engine_path = Path("xau_lab/real_tick_lab.py")
engine = engine_path.read_text(encoding="utf-8")

name = "rev_global_all_sell_resumption_m15strict"
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

anchor = '''    if c.name.startswith("rev_global_sell_cont_follow"):
        buy_trigger = False
        sell_trigger = cont_sell or follow_sell
'''
replacement = anchor + f'''
    if c.name == "{name}":
        buy_trigger = False
        sell_trigger = cross_sell or cont_sell or follow_sell
'''
if f'if c.name == "{name}":' not in engine:
    if anchor not in engine:
        raise SystemExit("global sell trigger anchor not found")
    engine = engine.replace(anchor, replacement, 1)

if engine.count(f'name="{name}"') != 1 or engine.count(f'if c.name == "{name}":') != 1:
    raise SystemExit("new revision integrity check failed")
engine_path.write_text(engine, encoding="utf-8")

# The June 2022/June 2024 audit windows have now been observed and are retired.
# Rotate only the final gate to two previously unused 2025 periods. Development
# and validation remain unchanged, and these holdout dates are not used by the
# strategy rule above.
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
    ("hold_2025_feb_blind", "holdout", "2025-02-03", "2025-02-22"),
    ("hold_2025_mar_blind", "holdout", "2025-03-03", "2025-03-22"),
]'''
runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not install fresh February/March 2025 holdout")
runner_path.write_text(runner, encoding="utf-8")

aggregate_path = Path("xau_lab/aggregate_results.py")
aggregate = aggregate_path.read_text(encoding="utf-8")
aggregate = re.sub(
    r"The candidate is considered acceptable only when .*? passes\.",
    "The candidate is considered acceptable only when the newly untouched February/March 2025 holdout gate passes.",
    aggregate,
)
aggregate_path.write_text(aggregate, encoding="utf-8")

print("Added one M15-confirmed all-sell resumption revision and sealed Feb/Mar 2025 holdout")
