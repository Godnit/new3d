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

# Install the sell-only trigger without depending on a legacy candidate name.
# Earlier iterations renamed or removed that anchor, so locate the stable final
# buy/sell expression inside signal_at and place the override immediately before it.
trigger_signature = f'    if c.name == "{name}":\n        buy_trigger = False\n'
if trigger_signature not in engine:
    signal_start = engine.find("def signal_at")
    if signal_start < 0:
        raise SystemExit("signal_at not found")
    buy_expr = engine.find("    buy = (", signal_start)
    if buy_expr < 0:
        raise SystemExit("final buy expression not found")
    trigger_block = f'''    if c.name == "{name}":
        buy_trigger = False
        sell_trigger = cross_sell or cont_sell or follow_sell

'''
    engine = engine[:buy_expr] + trigger_block + engine[buy_expr:]

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

# Do not rotate the protocol here. patch_available_blind_holdout.py installs the
# data-available holdout windows before invoking this strategy-only revision.
# Keeping protocol selection separate prevents an accidental window override.
print("Added one M15-slope all-sell resumption revision; preserved installed protocol")
