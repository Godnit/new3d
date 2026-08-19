from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

marker = "    return out\n\n\ndef in_session"
insert = '''    # One simple revision based only on development + validation trades:
    # keep the profitable directional specialization, but use a less reactive
    # exit profile. Development + validation showed most expectancy came from
    # full targets, while frequent early stop management contributed little.
    # Wider ATR protection and later break-even/trailing are economically
    # defensible for a trend-continuation system and are not date-specific.
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
            stop_atr=1.25,
            rr=1.35,
            be_trigger=0.80,
            be_lock_atr=0.05,
            trail_start=1.20,
            trail_atr=0.80,
            fail_fast_minutes=4,
            fail_fast_max_mfe_r=0.30,
            fail_fast_current_r=-0.10,
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
print("Applied one revision: balanced exit management for directional continuation strategy")
