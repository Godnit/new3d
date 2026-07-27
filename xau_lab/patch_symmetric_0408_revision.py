from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One date-agnostic statistical revision after the 05-07 window produced only
# 35 trades across ten independent weeks and failed development/holdout.
# Preserve signal, trend, risk, stops, targets, real spread, and slippage.
# Expand only the liquid-session horizon by one adjacent hour on each side.
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

    # Symmetric European liquid-session rule. Both directions remain subject
    # to the existing M5/M15 trend and closed-bar signal requirements.
    return hour in (4, 5, 6, 7, 8)


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

old_name = 'name=c.name + "_sym567"'
if text.count(old_name) != 1:
    raise SystemExit(f"Expected one symmetric candidate name, found {text.count(old_name)}")
text = text.replace(old_name, 'name=c.name + "_sym0408"', 1)

path.write_text(text, encoding="utf-8")
print("Applied one revision: symmetric trend-aligned eligibility at server hours 04-08")
