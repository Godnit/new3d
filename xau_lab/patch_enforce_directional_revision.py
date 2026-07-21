from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

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
print("Enforced exact CONT_BUY / FOLLOW_SELL routing after all protocol patches")
