from pathlib import Path
import re

# One simple, date-agnostic revision based only on development and validation:
# server hour 07 was negative in both samples, while hours 05-06 were positive
# in validation and materially less weak in development. Remove only the final
# 07:00-07:59 admission hour. Keep signals, trend filters, stops, targets,
# trailing, risk, spread/slippage stress, and all holdout dates unchanged.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

pattern = r"session_start=5,\n(?P<indent>\s*)session_end=8,"
text, count = re.subn(
    pattern,
    lambda m: "session_start=5,\n" + m.group("indent") + "session_end=7,",
    text,
)
if count < 1:
    raise SystemExit("No active symmetric 05:00-08:00 candidate session found")

text = text.replace("_sym0508", "_sym0507")
text = text.replace("sym0508", "sym0507")
path.write_text(text, encoding="utf-8")
print(f"Applied one revision: exclude weak server hour 07 from {count} candidate blocks; holdout unchanged")
