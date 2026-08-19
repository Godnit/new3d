from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

marker = "\ndef in_session(hour: int, c: Candidate) -> bool:\n"
if marker not in text:
    raise SystemExit("candidate insertion marker not found")
if 'name="rev_body_floor06"' in text:
    raise SystemExit("body-floor revision already applied")

boundary = text.find(marker)
return_pos = text.rfind("    return out", 0, boundary)
if return_pos < 0:
    raise SystemExit("candidate return not found")

# Exactly one economically defensible strategy revision for this iteration:
# keep all trend, session, spread and risk logic, but lower the minimum candle
# body from 0.10 ATR to 0.06 ATR. The prior independent run produced too few
# observations (13 trades across ten windows), so this targets sample scarcity
# without adding an indicator, date exception, or directional bias.
candidate = '''    out.append(
        replace(
            base,
            name="rev_body_floor06",
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
text = text[:return_pos] + candidate + text[return_pos:]
path.write_text(text, encoding="utf-8")
print("Added one simple revision: minimum candle body 0.10 ATR -> 0.06 ATR")
