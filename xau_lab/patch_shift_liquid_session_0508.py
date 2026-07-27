from pathlib import Path
import re

# One simple, date-agnostic revision after the audited real-tick run 411.
# Across the six development and two validation windows, server hour 04 was the
# dominant loss source (-10.92 USD, PF 0.67 across 38 trades). The strategy is
# a trend/pullback system, so waiting until the more liquid London hand-off and
# extending one hour later is economically defensible. This patch changes only
# the admission window from 04:00-07:00 to 05:00-08:00. It does not alter the
# signals, closed-bar trend logic, spread/slippage stress, stops, targets,
# sizing, daily protections, or any development/validation/holdout dates.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

pattern = r"session_start=4,\n(?P<indent>\s*)session_end=7,"
text, count = re.subn(
    pattern,
    lambda m: "session_start=5,\n" + m.group("indent") + "session_end=8,",
    text,
)
if count < 1:
    raise SystemExit("No active 04:00-07:00 candidate session found")

text = text.replace("_sym0407", "_sym0508")
text = text.replace("s0407", "s0508")
engine.write_text(text, encoding="utf-8")
print(f"Applied one revision: shifted {count} candidate session block(s) from 04-07 to 05-08; holdout unchanged")
