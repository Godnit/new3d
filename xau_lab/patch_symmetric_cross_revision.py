from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''    # One simple global revision after the latest independent run: research
    # candidates use only bullish EMA9 reclaim/cross entries. In development
    # and validation, cross buys were the only signal family with a positive
    # expectancy, while follow/continuation entries and shorts caused most of
    # the losses. The frozen Headway baseline remains unchanged.
    if not c.baseline_hour_rules:
        buy = buy and cross_buy
        sell = False
'''
new = '''    # One simple global revision after the independent cross-buy run produced
    # too few opportunities and zero validation trades: retain only the clean
    # EMA9 reclaim/cross family, but apply it symmetrically in both directions.
    # Follow and continuation entries remain disabled. The frozen Headway
    # baseline remains unchanged, and validation/holdout windows are not moved.
    if not c.baseline_hour_rules:
        buy = buy and cross_buy
        sell = sell and cross_sell
'''

if text.count(old) != 1:
    raise SystemExit(f"Expected one cross-buy-only research block, found {text.count(old)}")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied symmetric EMA9 cross-only research revision")
