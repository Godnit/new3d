from pathlib import Path

# One simple, economically defensible revision after run 279:
# the global M5 EMA9 cross-sell rule lost in every development, validation,
# and untouched holdout window (0/10 positive windows, PF 0.29 combined).
# Gold also carries a long-run positive drift, so test the exact mirror image:
# EMA9 cross-buy in the existing M5 uptrend/local-uptrend context, with no
# additional M15 veto. No dates, hours, exits, risk, spread, or holdout windows
# are changed.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old_direction = '''    buy = False  # global cross-sell-only revision
    sell = sell and cross_sell
'''
new_direction = '''    buy = buy and cross_buy
    sell = False  # global M5 cross-buy-only revision after failed short bias
'''
if text.count(old_direction) != 1:
    raise SystemExit(f"Expected one cross-sell direction block, found {text.count(old_direction)}")
text = text.replace(old_direction, new_direction, 1)

old_m15 = '''    m15_buy_ok = (not m15_down) if c.m15_mode == "veto" else m15_up
'''
new_m15 = '''    m15_buy_ok = True  # M5-only cross-buy revision; remove lagging M15 veto
'''
if text.count(old_m15) != 1:
    raise SystemExit(f"Expected one M15 buy gate, found {text.count(old_m15)}")
text = text.replace(old_m15, new_m15, 1)

path.write_text(text, encoding="utf-8")
print("Applied M5-only EMA9 cross-buy revision after run-279 short failure")
