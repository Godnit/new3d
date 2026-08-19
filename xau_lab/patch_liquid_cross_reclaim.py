from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

patch = r'''

# One simple post-validation strategy revision:
# trade only a first EMA9 reclaim/cross in the established M5 trend during
# the globally liquid 08:00-20:00 EET/EEST window.  This deliberately removes
# continuation/follow entries rather than adding more indicators or date rules.
_previous_candidates_liquid_cross = candidates

def candidates():
    out = _previous_candidates_liquid_cross()
    if any(c.name == "rev_liquid_cross_reclaim_v1" for c in out):
        return out
    template = next((c for c in out if c.name.startswith("rob_s1320_all_off_bal")), out[0])
    out.append(replace(
        template,
        name="rev_liquid_cross_reclaim_v1",
        baseline_hour_rules=False,
        session_start=8,
        session_end=20,
        blocked_hour=24,
        signal_mode="cross",
        m15_mode="off",
        stop_atr=1.25,
        rr=1.35,
        be_trigger=0.80,
        be_lock_atr=0.05,
        trail_start=1.20,
        trail_atr=0.80,
        fail_fast_minutes=4,
        fail_fast_max_mfe_r=0.30,
        fail_fast_current_r=-0.10,
        min_body_atr=0.06,
        max_body_atr=1.10,
        max_entry_distance_atr=1.10,
        close_extreme_fraction=0.45,
        max_spread_price=1.20,
        max_spread_atr=0.65,
    ))
    return out
'''

if "rev_liquid_cross_reclaim_v1" not in text:
    text += patch
path.write_text(text, encoding="utf-8")
print("Added one liquid-session EMA9 cross/reclaim candidate")
