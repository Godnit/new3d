from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One economically simple revision based only on development + 2024 validation:
# long continuation and both follow-through directions had negative aggregate
# expectancy, while continuation sells were the only signal family with
# non-negative expectancy. Test a sell-only trend-continuation candidate rather
# than adding another indicator or date-specific exception.
if 'name="rev_cont_sell_only"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found for sell-only revision")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("final candidate return not found for sell-only revision")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_cont_sell_only",
            baseline_hour_rules=False,
            session_start=13,
            session_end=21,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="off",
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
        )
    )
'''
    text = text[:return_pos] + candidate + text[return_pos:]

signal_anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'if c.name.startswith("rev_cont_sell_only"):' not in text:
    if signal_anchor not in text:
        raise SystemExit("signal anchor not found for sell-only revision")
    signal_insert = '''    # Later protocol patches append suffixes such as _cl55 to candidate names.
    # Use prefix matching so the directional rule survives those systematic
    # renames. The previous exact-name check silently allowed long trades.
    if c.name.startswith("rev_cont_sell_only"):
        buy_trigger = False
        sell_trigger = cont_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(signal_anchor, signal_insert, 1)

# Broad sell-only diagnostic candidate. Its original exact-name comparison was
# also invalidated by protocol suffixes, so enforce the rule by prefix.
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

signal_anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'if c.name.startswith("rev_sell_only_all"):' not in text:
    if signal_anchor not in text:
        raise SystemExit("signal anchor not found for sell-only-all revision")
    signal_insert = '''    if c.name.startswith("rev_sell_only_all"):
        buy_trigger = False

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(signal_anchor, signal_insert, 1)

# Run-111 development and validation diagnostics showed that continuation sells
# were positive in both splits and follow-through sells were positive in the
# development split, while both long families were negative. The prior narrow
# session produced too few trades. This single revision tests the same economic
# idea globally: sell-side trend resumption only, with no date/month/weekday
# exception and with all existing spread, ATR, risk and loss-pause protections.
if 'name="rev_global_sell_cont_follow"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found for global sell revision")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return not found for global sell revision")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_global_sell_cont_follow",
            baseline_hour_rules=False,
            session_start=0,
            session_end=0,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="off",
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

signal_anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'if c.name.startswith("rev_global_sell_cont_follow"):' not in text:
    if signal_anchor not in text:
        raise SystemExit("signal anchor not found for global sell revision")
    signal_insert = '''    if c.name.startswith("rev_global_sell_cont_follow"):
        buy_trigger = False
        sell_trigger = cont_sell or follow_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(signal_anchor, signal_insert, 1)

path.write_text(text, encoding="utf-8")
print("Added suffix-safe sell-only continuation, broad sell-only, and global sell-resumption candidates")
