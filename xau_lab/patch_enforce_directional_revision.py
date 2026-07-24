from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple revision after the latest independent development + validation run
# produced too few trades for a meaningful estimate. Keep the frozen baseline
# unchanged. Research candidates may close within the directional 65% of the
# candle range rather than requiring the directional 40%. This preserves body,
# trend, spread, distance, execution, and risk filters while reducing sample
# starvation. It contains no date-, weekday-, or holdout-specific condition.
return_marker = '''    return out


def in_session'''
return_replacement = '''    out = [
        candidate
        if candidate.baseline_hour_rules
        else replace(candidate, close_extreme_fraction=0.65)
        for candidate in out
    ]
    return out


def in_session'''
if return_marker not in text:
    raise SystemExit("candidate return marker not found")
text = text.replace(return_marker, return_replacement, 1)

marker = '''    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
replacement = '''    # Final enforcement for the directional revision. Earlier protocol patches
    # may alter generic trigger routing; this candidate must remain exactly
    # CONT_BUY on the long side and FOLLOW_SELL on the short side. The rule was
    # chosen from development + validation only, never from the 2025 holdout.
    if c.name == "rev_cont_buy_follow_sell":
        buy_trigger = cont_buy
        sell_trigger = follow_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
if marker not in text:
    raise SystemExit("final directional enforcement marker not found")
text = text.replace(marker, replacement, 1)
path.write_text(text, encoding="utf-8")
print("Enforced directional revision and broadened research candle-close tolerance to 65%")
