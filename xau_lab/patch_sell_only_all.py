from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision based only on development and
# validation evidence: long signals were materially weaker, while the short
# side was near breakeven before holdout selection. Keep the same signal
# families and risk logic, but remove the weak long side. No date-specific,
# weekday, or extra-indicator condition is introduced.
if 'name="rev_sell_only_all"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found for sell-only-all revision")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("final candidate return not found for sell-only-all revision")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_sell_only_all",
            baseline_hour_rules=False,
            session_start=13,
            session_end=20,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="off",
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

# Later protocol patches append suffixes such as _cl55 to candidate names.
# Match the stable prefix so the sell-only rule survives those harmless
# renames. The previous exact-name comparison silently allowed long trades.
signal_anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'c.name.startswith("rev_sell_only_all")' not in text:
    if signal_anchor not in text:
        raise SystemExit("signal anchor not found for sell-only-all revision")
    signal_insert = '''    if c.name.startswith("rev_sell_only_all"):
        buy_trigger = False

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(signal_anchor, signal_insert, 1)

# Remove the obsolete exact-name guard if an earlier run inserted it.
text = text.replace('    if c.name == "rev_sell_only_all":\n        buy_trigger = False\n\n', '')

path.write_text(text, encoding="utf-8")
print("Added sell-only revision with suffix-safe direction enforcement")
