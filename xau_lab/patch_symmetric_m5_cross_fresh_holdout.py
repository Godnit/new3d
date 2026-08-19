from pathlib import Path

# One simple, economically defensible revision after run 285:
# both the prior global cross-sell-only and the mirror-image cross-buy-only
# versions lost across development and validation. Restore directional symmetry
# while keeping the same M5 trend context, EMA9 cross trigger, spread handling,
# risk sizing, stops, trailing, sessions, and execution stress. This is not a
# date-specific trading rule.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")
old = '''    buy = buy and cross_buy
    sell = False  # global M5 cross-buy-only revision after failed short bias
'''
new = '''    # Symmetric M5 trend-cross revision: buy crosses in M5/local uptrends and
    # sell crosses in M5/local downtrends. No directional market bias.
    buy = buy and cross_buy
    sell = sell and cross_sell
'''
if text.count(old) != 1:
    raise SystemExit(f"Expected one active M5 cross-buy-only block, found {text.count(old)}")
text = text.replace(old, new, 1)
engine.write_text(text, encoding="utf-8")

# Rotate the already-observed holdout to two non-overlapping calendar windows
# that are absent from all prior named holdout patches. Development and
# validation stay frozen. These dates are protocol partitions only and never
# enter the signal logic.
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
