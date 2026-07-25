from pathlib import Path

# One simple, economically defensible revision after run 285:
# both the prior global cross-sell-only and the mirror-image cross-buy-only
# versions lost across development and validation. Restore directional symmetry
# while keeping the same M5 trend context, EMA9 cross trigger, spread handling,
# risk sizing, stops, trailing, sessions, and execution stress. This is not a
# date-specific trading rule.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

old_direction = '''    buy = False  # global cross-sell-only revision
    sell = sell and cross_sell
'''
new_direction = '''    # Symmetric M5 trend-cross revision: buy crosses in M5/local uptrends and
    # sell crosses in M5/local downtrends. No directional market bias.
    buy = buy and cross_buy
    sell = sell and cross_sell
'''
if text.count(old_direction) != 1:
    raise SystemExit(f"Expected one cross-sell direction block, found {text.count(old_direction)}")
text = text.replace(old_direction, new_direction, 1)

old_m15 = '''    m15_buy_ok = (not m15_down) if c.m15_mode == "veto" else m15_up
'''
new_m15 = '''    m15_buy_ok = True  # symmetric M5-only cross revision; no lagging M15 gate
'''
if text.count(old_m15) != 1:
    raise SystemExit(f"Expected one M15 buy gate, found {text.count(old_m15)}")
text = text.replace(old_m15, new_m15, 1)
engine.write_text(text, encoding="utf-8")

# Rotate the already-observed holdout to two non-overlapping windows absent from
# prior named holdout patches. Development and validation remain frozen. These
# dates are protocol partitions only and never enter the signal logic.
runner = Path("xau_lab/hf_window_runner.py")
rtext = runner.read_text(encoding="utf-8")
old_a = '("hold_2021_may_available", "holdout", "2021-05-24", "2021-06-05"),'
old_b = '("hold_2022_dec", "holdout", "2022-12-01", "2022-12-20"),'
new_a = '("hold_2021_sep_fresh", "holdout", "2021-09-06", "2021-09-25"),'
new_b = '("hold_2022_nov_fresh", "holdout", "2022-11-01", "2022-11-20"),'
if rtext.count(old_a) != 1 or rtext.count(old_b) != 1:
    raise SystemExit("Expected frozen holdout tuples were not found exactly once")
rtext = rtext.replace(old_a, new_a, 1).replace(old_b, new_b, 1)
runner.write_text(rtext, encoding="utf-8")

print("Restored symmetric M5 EMA9 cross entries and rotated to fresh Sep-2021/Nov-2022 holdout")
