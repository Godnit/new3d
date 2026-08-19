from pathlib import Path

# One simple strategy revision for this iteration, chosen from development and
# validation diagnostics only: retain the globally available sell-side
# continuation/follow-through setup and the strict falling M15 trend filter,
# but relax only the candle close-location requirement from 0.55 to 0.65.
# Economically, this allows a bearish resumption candle to close within the
# lower 65% of its range instead of requiring the lower 55%, increasing sample
# size without adding an indicator, date rule, hour exception, or new signal
# family. Risk, stop, target, spread and loss controls remain unchanged.
engine_path = Path("xau_lab/real_tick_lab.py")
engine = engine_path.read_text(encoding="utf-8")

name = "rev_global_sell_cont_follow_m15strict_cl65"
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
            close_extreme_fraction=0.65,
            max_spread_price=1.20,
            max_spread_atr=0.65,
        )
    )
'''
    engine = engine[:return_pos] + candidate + engine[return_pos:]

# patch_global_sell_cont_follow.py already supplies the economically intended
# sell-only continuation/follow-through trigger to every candidate whose name
# begins with rev_global_sell_cont_follow. Verify that stable hook exists.
if 'if c.name.startswith("rev_global_sell_cont_follow"):' not in engine:
    raise SystemExit("global sell continuation/follow trigger hook not found")
if engine.count(f'name="{name}"') != 1:
    raise SystemExit("close65 candidate integrity check failed")

engine_path.write_text(engine, encoding="utf-8")
print("Added strict M15 sell-resumption candidate with one close-location relaxation: 0.55 -> 0.65")
