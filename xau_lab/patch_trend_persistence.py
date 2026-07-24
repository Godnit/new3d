from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''    local_up = b1.ema9 > b1.ema21
    local_down = b1.ema9 < b1.ema21
    distance = abs(b1.close - b1.ema21) / atr
'''
new = '''    local_up = b1.ema9 > b1.ema21
    local_down = b1.ema9 < b1.ema21
    # One simple anti-whipsaw revision: require the fast M1 EMA to have
    # persisted in the trade direction across the last three closed bars.
    # This uses closed bars only and is independent of calendar dates.
    m1_persist_up = b1.ema9 > b2.ema9 > b3.ema9
    m1_persist_down = b1.ema9 < b2.ema9 < b3.ema9
    distance = abs(b1.close - b1.ema21) / atr
'''
if old not in text:
    raise SystemExit("local trend marker not found")
text = text.replace(old, new, 1)

old_buy = '''        and local_up
        and not_extended
        and buy_trigger
'''
new_buy = '''        and local_up
        and m1_persist_up
        and not_extended
        and buy_trigger
'''
if old_buy not in text:
    raise SystemExit("buy persistence marker not found")
text = text.replace(old_buy, new_buy, 1)

old_sell = '''        and local_down
        and not_extended
        and sell_trigger
'''
new_sell = '''        and local_down
        and m1_persist_down
        and not_extended
        and sell_trigger
'''
if old_sell not in text:
    raise SystemExit("sell persistence marker not found")
text = text.replace(old_sell, new_sell, 1)

path.write_text(text, encoding="utf-8")
print("Added one simple revision: three-closed-bar M1 EMA9 trend persistence")
