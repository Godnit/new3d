from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision after the independent cross-only
# failure: stop buying/selling the instant EMA9 is crossed. On M1 that trigger
# is highly exposed to spread and whipsaw. Require an already-established local
# trend to pull back toward EMA9/EMA21 and then resume through the previous
# candle (CONT or FOLLOW). M15 remains a directional veto. No date/hour/weekday
# or holdout-specific rule is introduced.
old_buy = "        buy = buy and cross_buy"
old_sell = "        sell = sell and cross_sell"
new_buy = "        buy = buy and (cont_buy or follow_buy)"
new_sell = "        sell = sell and (cont_sell or follow_sell)"

if text.count(old_buy) != 1:
    raise SystemExit(f"Expected one cross-only buy restriction, found {text.count(old_buy)}")
if text.count(old_sell) != 1:
    raise SystemExit(f"Expected one cross-only sell restriction, found {text.count(old_sell)}")

text = text.replace(old_buy, new_buy, 1)
text = text.replace(old_sell, new_sell, 1)
path.write_text(text, encoding="utf-8")
print("Applied single revision: pullback-continuation entries instead of immediate EMA crosses")
