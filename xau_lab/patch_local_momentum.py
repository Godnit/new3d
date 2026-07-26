from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One economically motivated revision: let the M1 EMA9/EMA21 structure drive
# entries while M15 remains the higher-timeframe veto. The previous mandatory
# M5 alignment made the strategy extremely sparse and almost long-only in the
# independent sample. No date- or weekday-specific rule is added.
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

# Make result names self-identifying without changing candidate parameters.
old_return = "    return out\n\n\ndef in_session"
new_return = "    return [replace(c, name=c.name + '_localM1_M15veto') for c in out]\n\n\ndef in_session"
if old_return not in text:
    raise SystemExit("Candidate return marker not found")
text = text.replace(old_return, new_return, 1)

path.write_text(text, encoding="utf-8")
print("Applied single revision: local M1 momentum with M15 veto; removed mandatory M5 alignment")
