from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''    if not c.baseline_hour_rules:
        buy_trigger = False

    # Exact baseline keeps its report-driven special hour rules.
'''
new = '''    # One simple revision after the independent sell-only experiment failed
    # development, validation, and untouched holdout. Restore directional
    # symmetry, but retain only the clean EMA9 reclaim/cross family. This
    # removes continuation/follow entries, which were negative in development,
    # without adding any date-specific rule or extra indicator. The frozen
    # Headway baseline remains unchanged.
    if not c.baseline_hour_rules:
        buy_trigger = cross_buy
        sell_trigger = cross_sell

    # Exact baseline keeps its report-driven special hour rules.
'''

if text.count(old) != 1:
    raise SystemExit(f"Expected one sell-only research block, found {text.count(old)}")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one-variable revision: symmetric EMA9 cross-only entries")
