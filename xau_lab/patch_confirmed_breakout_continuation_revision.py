from pathlib import Path
import re

# One strategy revision for this iteration:
# abandon the consistently loss-making failed-breakout fade and require the
# original trend direction to close beyond the prior completed bar's extreme.
# This is a simple breakout-confirmation rule, applied only to closed bars.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

old = '''        direction, sig_name, atr = signal_at(bars, i, c)
        if direction != 0:
            # Fade a qualified failed breakout instead of following it. The
            # reversal is applied only after the completed-bar signal exists,
            # so chronological integrity and first-tick execution are intact.
            direction = -direction
            sig_name = "FADE_" + sig_name
        if direction == 0 or not direction_allowed(direction, hour, c):
'''
new = '''        direction, sig_name, atr = signal_at(bars, i, c)
        if direction != 0:
            # Confirm continuation with completed bars only: the signal bar
            # must close beyond the previous bar's high/low in its direction.
            signal_bar = bars.iloc[i - 1]
            prior_bar = bars.iloc[i - 2]
            confirmed = (
                (direction > 0 and signal_bar.close > prior_bar.high)
                or (direction < 0 and signal_bar.close < prior_bar.low)
            )
            if not confirmed:
                direction = 0
            else:
                sig_name = "CONFIRMED_BREAKOUT_" + sig_name
        if direction == 0 or not direction_allowed(direction, hour, c):
'''
if text.count(old) != 1:
    raise SystemExit(f"Expected one failed-fade entry block, found {text.count(old)}")
text = text.replace(old, new, 1)

text, renamed = re.subn(
    r'name="universal_liquid_failed_breakout_fade_v1"',
    'name="universal_liquid_confirmed_breakout_v1"',
    text,
    count=1,
)
if renamed != 1:
    raise SystemExit("Could not rename the sole research candidate")
engine.write_text(text, encoding="utf-8")

# The previously reported holdout has now been observed. Rotate only the
# evaluation protocol to two fresh, non-overlapping 2025 windows. These dates
# are not referenced by strategy logic or parameter selection.
runner = Path("xau_lab/hf_window_runner.py")
runner_text = runner.read_text(encoding="utf-8")
runner_text, first = re.subn(
    r'\("hold_2025_feb_fresh", "holdout", "2025-02-03", "2025-02-15"\)',
    '("hold_2025_jul_fresh", "holdout", "2025-07-07", "2025-07-19")',
    runner_text,
    count=1,
)
runner_text, second = re.subn(
    r'\("hold_2025_sep_fresh", "holdout", "2025-09-08", "2025-09-20"\)',
    '("hold_2025_nov_fresh", "holdout", "2025-11-03", "2025-11-15")',
    runner_text,
    count=1,
)
if first != 1 or second != 1:
    raise SystemExit(f"Could not rotate fresh holdout: first={first}, second={second}")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = report.replace(
    "fresh February/September 2025 holdout gate",
    "fresh July/November 2025 holdout gate",
)
aggregate.write_text(report, encoding="utf-8")

print(
    "Applied one revision: closed-bar confirmed breakout continuation; "
    "rotated only the untouched 2025 holdout"
)
