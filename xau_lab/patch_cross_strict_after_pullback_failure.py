from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One economically coherent revision after pullback/continuation failed across
# development and validation: use only a fresh EMA9 reclaim/cross, and require
# full M15 trend agreement. This avoids the late continuation entries that paid
# spread after much of the move had already occurred. It is global, symmetric,
# and contains no date-, weekday-, or holdout-specific rule.
old_buy = "        buy = buy and (cont_buy or follow_buy)"
old_sell = "        sell = sell and (cont_sell or follow_sell)"
if text.count(old_buy) != 1 or text.count(old_sell) != 1:
    raise SystemExit(
        f"Expected one pullback restriction per side; buy={text.count(old_buy)} sell={text.count(old_sell)}"
    )
text = text.replace(old_buy, "        buy = buy and cross_buy", 1)
text = text.replace(old_sell, "        sell = sell and cross_sell", 1)

old_m15_buy = '    m15_buy_ok = (not m15_down) if c.m15_mode == "veto" else m15_up'
old_m15_sell = '    m15_sell_ok = (not m15_up) if c.m15_mode == "veto" else m15_down'
if text.count(old_m15_buy) != 1 or text.count(old_m15_sell) != 1:
    raise SystemExit(
        f"Expected M15 mode lines; buy={text.count(old_m15_buy)} sell={text.count(old_m15_sell)}"
    )
text = text.replace(old_m15_buy, "    m15_buy_ok = m15_up", 1)
text = text.replace(old_m15_sell, "    m15_sell_ok = m15_down", 1)

path.write_text(text, encoding="utf-8")
print("Applied single revision: fresh symmetric cross entries with strict M15 alignment")
