from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# Archived strategy revision retained for reproducibility:
# - keep every existing sell signal family (cross, continuation, follow)
# - remove the historically weak long side
# - trade only the broad European/US liquid session
# - veto entries only when M15 is explicitly bullish.
if 'name="rev_sell_only_liquid_veto"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return boundary not found")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_sell_only_liquid_veto",
            baseline_hour_rules=False,
            session_start=7,
            session_end=21,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="veto",
            stop_atr=1.80,
            rr=1.00,
            be_trigger=0.90,
            be_lock_atr=0.05,
            trail_start=1.15,
            trail_atr=1.00,
            fail_fast_minutes=6,
            fail_fast_max_mfe_r=0.40,
            fail_fast_current_r=-0.15,
            close_extreme_fraction=0.55,
            max_spread_price=1.20,
            max_spread_atr=0.65,
        )
    )
'''
    text = text[:return_pos] + candidate + text[return_pos:]

anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'c.name.startswith("rev_sell_only_liquid_veto")' not in text:
    if anchor not in text:
        raise SystemExit("signal anchor not found")
    replacement = '''    if c.name.startswith("rev_sell_only_liquid_veto"):
        buy_trigger = False

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(anchor, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Added archived broad-liquid-session sell-only M15-veto revision")

# Exactly one new strategy revision for the current iteration. This downstream
# patch also seals fresh December holdouts before the workflow starts testing.
revision = Path("xau_lab/patch_focused_sell_resumption_fresh_dec_holdout.py")
namespace = {"__name__": "__main__", "__file__": str(revision)}
exec(compile(revision.read_text(encoding="utf-8"), str(revision), "exec"), namespace)
