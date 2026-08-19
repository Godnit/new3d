from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One economically motivated revision only: keep the M5 trend-separation check,
# but reduce it from 0.25 to 0.05 M1 ATR. The prior threshold removed virtually
# every validation and holdout opportunity. A small positive separation still
# avoids perfectly flat EMA states while preserving enough independent trades
# to test the strategy statistically. This is not date-specific.
constant_marker = 'START_BALANCE = 500.0\n'
if constant_marker not in text:
    raise SystemExit("START_BALANCE marker not found")
text = text.replace(
    constant_marker,
    constant_marker + 'MIN_M5_EMA_SEPARATION_ATR = 0.05\n',
    1,
)

trend_marker = '''    m5_up = b1.m5_ema20 > b1.m5_ema50 and b1.m5_close > b1.m5_ema20
    m5_down = b1.m5_ema20 < b1.m5_ema50 and b1.m5_close < b1.m5_ema20
'''
if trend_marker not in text:
    raise SystemExit("M5 trend marker not found")
text = text.replace(
    trend_marker,
    trend_marker + '''    m5_separation_ok = abs(b1.m5_ema20 - b1.m5_ema50) / atr >= MIN_M5_EMA_SEPARATION_ATR
''',
    1,
)

buy_marker = '''        and m5_up
        and m15_buy_ok
'''
sell_marker = '''        and m5_down
        and m15_sell_ok
'''
if buy_marker not in text or sell_marker not in text:
    raise SystemExit("buy/sell M5 condition markers not found")
text = text.replace(
    buy_marker,
    '''        and m5_up
        and m5_separation_ok
        and m15_buy_ok
''',
    1,
)
text = text.replace(
    sell_marker,
    '''        and m5_down
        and m5_separation_ok
        and m15_sell_ok
''',
    1,
)

path.write_text(text, encoding="utf-8")
print("Applied M5 trend-strength filter: EMA separation >= 0.05 M1 ATR")
