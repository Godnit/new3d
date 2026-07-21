from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision for this iteration:
# require the closed M15 EMA20 to be moving in the intended direction.
# This adds no new indicator, uses only closed information, and is intended
# to avoid taking M1 continuation entries while the higher-timeframe trend
# is already flattening or turning.
trend_marker = '''    m15_up = b1.m15_ema20 > b1.m15_ema50 and b1.m15_close > b1.m15_ema50
    m15_down = b1.m15_ema20 < b1.m15_ema50 and b1.m15_close < b1.m15_ema50
'''
if trend_marker not in text:
    raise SystemExit("M15 trend marker not found")
text = text.replace(
    trend_marker,
    trend_marker + '''    m15_slope_up = b1.m15_ema20 > b2.m15_ema20
    m15_slope_down = b1.m15_ema20 < b2.m15_ema20
''',
    1,
)

buy_marker = '''        and m15_buy_ok
        and local_up
'''
sell_marker = '''        and m15_sell_ok
        and local_down
'''
if buy_marker not in text or sell_marker not in text:
    raise SystemExit("M15 buy/sell condition markers not found")
text = text.replace(
    buy_marker,
    '''        and m15_buy_ok
        and m15_slope_up
        and local_up
''',
    1,
)
text = text.replace(
    sell_marker,
    '''        and m15_sell_ok
        and m15_slope_down
        and local_down
''',
    1,
)

path.write_text(text, encoding="utf-8")
print("Applied one simple revision: closed M15 EMA20 slope must align with trade direction")
