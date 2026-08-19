from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One economically motivated revision: let the closed M1 EMA9/EMA21 structure
# drive entries while M15 remains the higher-timeframe veto. The previous
# mandatory M5 alignment made the independently tested strategy sparse and
# almost long-only. No date, weekday, or holdout-specific rule is added.
old_buy = "        and m5_up\n        and m15_buy_ok"
new_buy = "        and m15_buy_ok"
old_sell = "        and m5_down\n        and m15_sell_ok"
new_sell = "        and m15_sell_ok"

if text.count(old_buy) != 1:
    raise SystemExit(f"Expected one buy M5 alignment block, found {text.count(old_buy)}")
if text.count(old_sell) != 1:
    raise SystemExit(f"Expected one sell M5 alignment block, found {text.count(old_sell)}")

text = text.replace(old_buy, new_buy, 1)
text = text.replace(old_sell, new_sell, 1)
path.write_text(text, encoding="utf-8")
print("Applied single revision: local M1 momentum with M15 veto; removed mandatory M5 alignment")
