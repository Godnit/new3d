from pathlib import Path
import re

# Existing closed-candle directional-efficiency filter.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = "    body_ok = c.min_body_atr <= body_atr <= c.max_body_atr"
new = '''    directional_efficiency = body / rng
    body_ok = (
        c.min_body_atr <= body_atr <= c.max_body_atr
        and directional_efficiency >= 0.55
    )'''

if text.count(old) != 1:
    raise SystemExit(
        f"Expected one body-quality marker, found {text.count(old)}; refusing an ambiguous patch"
    )
text = text.replace(old, new, 1)

# One new simple, date-agnostic revision based only on development and
# validation results from the previous completed run: server hour 07 was
# negative in both samples. Remove only 07:00-07:59 from the active symmetric
# liquidity session. Signals, trend filters, stops, targets, risk, costs,
# execution stress, and every holdout date remain unchanged.
pattern = r"session_start=5,\n(?P<indent>\s*)session_end=8,"
text, session_count = re.subn(
    pattern,
    lambda m: "session_start=5,\n" + m.group("indent") + "session_end=7,",
    text,
)
if session_count < 1:
    raise SystemExit("No active symmetric 05:00-08:00 candidate session found")

text = text.replace("_sym0508", "_sym0507")
text = text.replace("sym0508", "sym0507")
path.write_text(text, encoding="utf-8")
print(
    f"Applied directional efficiency >= 0.55 and one new revision: "
    f"excluded weak server hour 07 from {session_count} candidate blocks; holdout unchanged"
)
