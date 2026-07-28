from pathlib import Path
import re

# One simple, date-agnostic revision after the long-only first-hour setup was
# too sparse to validate: keep the same long pullback logic, indicators, risk,
# stops, targets and execution costs, but allow it throughout each candidate's
# existing liquid session instead of only server hour 05.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

old = '''    # Date-agnostic long-only revision: retain the first liquid-hour pullback
    # setup and remove the short side, which was negative in the frozen
    # development + validation sample. No date is referenced by this rule.
    return hour == 5 and direction > 0
'''
new = '''    # Date-agnostic long-only liquid-session revision. The previous first-hour
    # restriction produced too few independent trades to validate. Preserve the
    # same signal and risk logic, but permit long entries throughout the
    # candidate's already-defined liquid session.
    if c.session_start < c.session_end:
        session_ok = c.session_start <= hour < c.session_end
    else:
        session_ok = hour >= c.session_start or hour < c.session_end
    return session_ok and direction > 0
'''
if old not in text:
    raise SystemExit("Could not find the long-only first-hour rule")
text = text.replace(old, new, 1)
text = text.replace("_longL5", "_longLiquid")
text = text.replace("longL5", "longLiquid")
engine.write_text(text, encoding="utf-8")

print(
    "Applied one revision: preserve long-only pullback logic but extend entries "
    "from hour 05 to each candidate's existing liquid session; holdout unchanged"
)
