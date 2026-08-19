from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision after the directional 05/06 rule failed
# the independent gate. Keep the same strict cross, M15 alignment, stops,
# targets, risk, observed spread and adverse slippage. Change only direction
# eligibility: permit both trend-aligned directions during the first two
# liquid European-session server hours. This removes the fragile BUY-hour-05 /
# SELL-hour-06 asymmetry and should also raise the sample size.
pattern = r"def direction_allowed\(direction: int, hour: int, c: Candidate\) -> bool:\n.*?\n\ndef floor_volume"
replacement = '''def direction_allowed(direction: int, hour: int, c: Candidate) -> bool:
    if c.baseline_hour_rules:
        if hour == 3:
            return True
        if hour in (5, 7):
            return direction < 0
        if hour == 6:
            return direction > 0
        return False

    # Symmetric opening-liquidity rule: both trend-aligned directions are
    # eligible at server hours 05 and 06. No date, weekday, year, or holdout
    # information is consulted.
    return hour in (5, 6)


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

old_name = 'name=c.name + "_dir56"'
if text.count(old_name) != 1:
    raise SystemExit(f"Expected one directional candidate name, found {text.count(old_name)}")
text = text.replace(old_name, 'name=c.name + "_sym56"', 1)

path.write_text(text, encoding="utf-8")
print("Applied one revision: symmetric BUY/SELL eligibility at server hours 05 and 06")
