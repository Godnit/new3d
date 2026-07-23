from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision after run 154:
# continuation sells were the only signal family positive in development,
# validation, and untouched holdout, but the strict M15 variant produced too
# few observations. Test the middle ground: global continuation sells with an
# M15 veto (blocks counter-trend M15, but does not require fully aligned M15).
# No date, month, weekday, or single-window exception is introduced.
if 'name="rev_global_cont_sell_m15veto"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return not found")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_global_cont_sell_m15veto",
            baseline_hour_rules=False,
            session_start=0,
            session_end=0,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="veto",
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
    text = text[:return_pos] + candidate + text[return_pos:]

anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'if c.name.startswith("rev_global_cont_sell_m15veto"):' not in text:
    if anchor not in text:
        raise SystemExit("signal override anchor not found")
    replacement = '''    if c.name.startswith("rev_global_cont_sell_m15veto"):
        buy_trigger = False
        sell_trigger = cont_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(anchor, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Added global continuation-sell candidate with M15 veto")
