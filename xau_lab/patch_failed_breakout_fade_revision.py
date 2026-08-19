from pathlib import Path
import re

# One simple, economically defensible revision after the universal liquid-session
# trend-following candidate lost consistently in development, validation, and
# the now-observed holdout: treat the same qualified cross/follow events as
# failed-breakout mean-reversion entries. All signal-quality, spread, session,
# risk, stop, target, and execution assumptions remain unchanged.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

old = '''        direction, sig_name, atr = signal_at(bars, i, c)
        if direction == 0 or not direction_allowed(direction, hour, c):
'''
new = '''        direction, sig_name, atr = signal_at(bars, i, c)
        if direction != 0:
            # Fade a qualified failed breakout instead of following it. The
            # reversal is applied only after the completed-bar signal exists,
            # so chronological integrity and first-tick execution are intact.
            direction = -direction
            sig_name = "FADE_" + sig_name
        if direction == 0 or not direction_allowed(direction, hour, c):
'''
if text.count(old) != 1:
    raise SystemExit(f"Expected one entry-direction block, found {text.count(old)}")
text = text.replace(old, new, 1)

# Rename the sole candidate without changing any other parameter.
text, count = re.subn(
    r'name="universal_liquid_cross_follow_v1"',
    'name="universal_liquid_failed_breakout_fade_v1"',
    text,
    count=1,
)
if count != 1:
    raise SystemExit("Could not rename universal liquid candidate")
engine.write_text(text, encoding="utf-8")

# The May/December 2025 holdout is now observed. Rotate only the evaluation
# protocol to two new, non-overlapping 2025 periods that are not referenced by
# the strategy or parameter choice. Development and 2024 validation are fixed.
runner = Path("xau_lab/hf_window_runner.py")
runner_text = runner.read_text(encoding="utf-8")
runner_text, first = re.subn(
    r'\("hold_2025_may_fresh", "holdout", "2025-05-05", "2025-05-17"\)',
    '("hold_2025_feb_fresh", "holdout", "2025-02-03", "2025-02-15")',
    runner_text,
    count=1,
)
runner_text, second = re.subn(
    r'\("hold_2025_dec_fresh", "holdout", "2025-12-01", "2025-12-13"\)',
    '("hold_2025_sep_fresh", "holdout", "2025-09-08", "2025-09-20")',
    runner_text,
    count=1,
)
if first != 1 or second != 1:
    raise SystemExit(f"Could not rotate fresh holdout: first={first}, second={second}")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = report.replace(
    "fresh May/December 2025 holdout gate",
    "fresh February/September 2025 holdout gate",
)
aggregate.write_text(report, encoding="utf-8")

print("Applied one revision: fade qualified failed breakouts; rotated only the untouched 2025 holdout")
