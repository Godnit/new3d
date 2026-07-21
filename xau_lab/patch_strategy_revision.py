from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

marker = "    return out\n\n\ndef in_session"
insert = '''    # One simple revision based only on development + validation trades:
    # bullish continuation entries were profitable, while bullish follow entries
    # were weak; bearish follow entries were profitable, while bearish continuation
    # entries were weak. Test this directional specialization without adding indicators.
    out.append(
        replace(
            base,
            name="rev_cont_buy_follow_sell",
            baseline_hour_rules=False,
            session_start=13,
            session_end=20,
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
        )
    )
    return out


def in_session'''
if marker not in text:
    raise SystemExit("candidate-list patch marker not found")
text = text.replace(marker, insert, 1)

marker2 = '''    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
insert2 = '''    if c.name == "rev_cont_buy_follow_sell":
        buy_trigger = cont_buy
        sell_trigger = follow_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
if marker2 not in text:
    raise SystemExit("signal patch marker not found")
text = text.replace(marker2, insert2, 1)

path.write_text(text, encoding="utf-8")
print("Added one directional signal specialization revision")
