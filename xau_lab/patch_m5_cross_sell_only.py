from pathlib import Path

# Single economically coherent revision after run 269:
# independent results showed continuation/follow sell entries lost in every
# observed development instance, while EMA9 cross sells were the only setup
# with near-breakeven/positive behavior. The M15 veto also left the untouched
# holdout with zero trades. Use one simple entry definition globally:
# EMA9 cross sell in the existing M5 downtrend/local-downtrend context, without
# an additional M15 veto. No date, weekday, hour, holdout, risk, or exit rule is
# changed.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old_sell = "    sell = sell and (cross_sell or cont_sell or follow_sell)\n"
new_sell = "    sell = sell and cross_sell\n"
if text.count(old_sell) != 1:
    raise SystemExit(f"Expected one expanded sell restriction, found {text.count(old_sell)}")
text = text.replace(old_sell, new_sell, 1)

old_m15 = '''    m15_sell_ok = (not m15_up) if c.m15_mode == "veto" else m15_down
'''
new_m15 = '''    m15_sell_ok = True  # M5-only cross-sell revision; remove lagging M15 veto
'''
if text.count(old_m15) != 1:
    raise SystemExit(f"Expected one M15 sell gate, found {text.count(old_m15)}")
text = text.replace(old_m15, new_m15, 1)

path.write_text(text, encoding="utf-8")
print("Applied M5-only EMA9 cross-sell entry revision")
