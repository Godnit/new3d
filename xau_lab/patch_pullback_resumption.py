from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One economically defensible revision after run 73 failed across development,
# validation, and untouched holdout: replace immediate continuation entries with
# a two-bar pullback-and-resumption trigger. The prior candle must retrace into
# the EMA21 area against the trend, and the closed signal candle must resume the
# trend by reclaiming EMA9 and breaking the prior candle's extreme. This is
# date-agnostic, uses only closed bars, and adds no new indicator family.
return_marker = '''    return out


def in_session'''
return_replacement = '''    out.append(
        replace(
            base,
            name="rev_pullback_resumption",
            baseline_hour_rules=False,
            session_start=8,
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
            close_extreme_fraction=0.65,
        )
    )
    return out


def in_session'''
if return_marker not in text:
    raise SystemExit("candidate return marker not found")
text = text.replace(return_marker, return_replacement, 1)

signal_marker = '''    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
signal_replacement = '''    # Closed-bar pullback resumption: b2 retraces against the prevailing EMA
    # structure, while b1 confirms resumption by breaking b2's extreme.
    pullback_buy = (
        b2.close <= b2.open
        and b2.low <= b2.ema21 + atr * 0.15
        and b2.close >= b2.ema21 - atr * 0.10
        and b1.close > b1.ema9
        and b1.close > b2.high
        and b1.ema9 > b1.ema21
    )
    pullback_sell = (
        b2.close >= b2.open
        and b2.high >= b2.ema21 - atr * 0.15
        and b2.close <= b2.ema21 + atr * 0.10
        and b1.close < b1.ema9
        and b1.close < b2.low
        and b1.ema9 < b1.ema21
    )
    if c.name == "rev_pullback_resumption":
        buy_trigger = pullback_buy
        sell_trigger = pullback_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
if signal_marker not in text:
    raise SystemExit("signal routing marker not found")
text = text.replace(signal_marker, signal_replacement, 1)

path.write_text(text, encoding="utf-8")
print("Applied one revision: closed-bar EMA pullback resumption trigger")
