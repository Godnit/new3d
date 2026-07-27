from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision after the latest development
# and validation failure: remove server hours 07 and 08, which were negative
# in both splits, while retaining the earlier European-session hours 04-06.
# Signals, M5/M15 filters, stops, targets, risk, observed spread, adverse
# slippage and position-management logic are unchanged.
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

    # Earlier European-session window. Both directions remain subject to all
    # existing closed-bar trend and signal confirmations.
    return hour in (4, 5, 6)


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

old_block = '''                name=c.name + "_sym567",
                baseline_hour_rules=False,
                session_start=5,
                session_end=7,
                blocked_hour=24,
'''
new_block = '''                name=c.name + "_early0406",
                baseline_hour_rules=False,
                session_start=4,
                session_end=7,
                blocked_hour=24,
'''
if text.count(old_block) != 1:
    raise SystemExit(f"Expected one stale 05:00-06:59 candidate block, found {text.count(old_block)}")
text = text.replace(old_block, new_block, 1)

path.write_text(text, encoding="utf-8")
print("Applied one revision: removed consistently weak server hours 07 and 08")
