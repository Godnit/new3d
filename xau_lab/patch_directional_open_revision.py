from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision selected from development + validation only.
# In the 05:00-08:59 EET/EEST session, the only direction/hour groups with
# positive combined expectancy were BUY at server hour 05 and SELL at server
# hour 06. Later hours were negative for both directions. This keeps the same
# cross signal, M15 trend alignment, stops, targets, risk, spread and slippage;
# it changes only the direction allowed in the first two liquid hours.
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

    # Global, symmetric-in-construction opening-liquidity rule:
    # early hour accepts trend-aligned buys; following hour accepts
    # trend-aligned sells. No date, weekday, year or holdout lookup.
    if hour == 5:
        return direction > 0
    if hour == 6:
        return direction < 0
    return False


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

old_name = 'name=c.name + "_s0509"'
if text.count(old_name) != 1:
    raise SystemExit(f"Expected one final session candidate name, found {text.count(old_name)}")
text = text.replace(old_name, 'name=c.name + "_dir56"', 1)

old_session = '''                session_start=5,
                session_end=9,
                blocked_hour=24,
'''
new_session = '''                session_start=5,
                session_end=7,
                blocked_hour=24,
'''
if text.count(old_session) != 1:
    raise SystemExit(f"Expected one 05:00-09:00 candidate session, found {text.count(old_session)}")
text = text.replace(old_session, new_session, 1)

path.write_text(text, encoding="utf-8")
print("Applied one revision: BUY hour 05, SELL hour 06; all later session hours disabled")
