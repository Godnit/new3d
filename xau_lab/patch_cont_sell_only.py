from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One economically simple revision based only on development + 2024 validation:
# long continuation and both follow-through directions had negative aggregate
# expectancy, while continuation sells were the only signal family with
# non-negative expectancy. Test a sell-only trend-continuation candidate rather
# than adding another indicator or date-specific exception.
marker = "    return out\n\n\ndef in_session"
insert = '''    out.append(
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
    return out


def in_session'''
if marker not in text:
    raise SystemExit("candidate return marker not found for sell-only revision")
text = text.replace(marker, insert, 1)

signal_marker = '''    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
signal_insert = '''    if c.name == "rev_cont_sell_only":
        buy_trigger = False
        sell_trigger = cont_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
if signal_marker not in text:
    raise SystemExit("signal marker not found for sell-only revision")
text = text.replace(signal_marker, signal_insert, 1)

path.write_text(text, encoding="utf-8")
print("Added one simple revision: continuation-sell-only candidate")
