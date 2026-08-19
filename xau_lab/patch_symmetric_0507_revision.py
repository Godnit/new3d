from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One date-agnostic revision after the symmetric 05/06 opening window produced
# too few trades and failed development plus holdout. Keep the signal, trend,
# risk, stop, target, observed spread, and slippage logic unchanged. Extend
# eligibility by one adjacent liquid European-session hour (07) for both
# trend-aligned directions. This is a liquidity/session-horizon change only.
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

    # Symmetric liquid-session rule: both trend-aligned directions are eligible
    # at server hours 05, 06, and 07. No date, weekday, year, or holdout result
    # is consulted.
    return hour in (5, 6, 7)


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

old_name = 'name=c.name + "_sym56"'
if text.count(old_name) != 1:
    raise SystemExit(f"Expected one symmetric candidate name, found {text.count(old_name)}")
text = text.replace(old_name, 'name=c.name + "_sym567"', 1)

path.write_text(text, encoding="utf-8")
print("Applied one revision: symmetric BUY/SELL eligibility at server hours 05, 06, and 07")
