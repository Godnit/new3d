from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# Correct the preceding liquidity-horizon revision so its intended 04:00-08:59
# EET/EEST window is actually reachable. The prior patch widened
# direction_allowed() but left Candidate.session_start/session_end at 05:00-06:59,
# silently suppressing hours 04, 07, and 08. This is a chronology-neutral code
# correction, not a new date-specific strategy rule. Signals, M5/M15 filters,
# stops, targets, risk, observed spread, adverse slippage, and holdouts are
# unchanged.
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

old_block = '''                name=c.name + "_sym567",
                baseline_hour_rules=False,
                session_start=5,
                session_end=7,
                blocked_hour=24,
'''
new_block = '''                name=c.name + "_sym0408",
                baseline_hour_rules=False,
                session_start=4,
                session_end=9,
                blocked_hour=24,
'''
if text.count(old_block) != 1:
    raise SystemExit(f"Expected one stale 05:00-06:59 candidate block, found {text.count(old_block)}")
text = text.replace(old_block, new_block, 1)

path.write_text(text, encoding="utf-8")
print("Corrected symmetric liquid session: candidate and direction eligibility both use server hours 04-08")
