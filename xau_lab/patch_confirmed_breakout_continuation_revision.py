from pathlib import Path
import re

# One strategy revision for this iteration:
# abandon the consistently loss-making failed-breakout fade and require the
# original trend direction to close beyond the prior completed bar's extreme.
# The latest statistical audit showed marginal breaks remained loss-making, so
# require a small 0.10 ATR clearance beyond that extreme. This is a universal,
# cost-aware false-break filter using completed bars only.
#
# IMPORTANT: this patch must not alter the evaluation windows. The runner owns
# the frozen development, validation, and holdout protocol. Keeping dates out of
# strategy patches prevents post-result holdout rotation and protocol leakage.
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
            # Confirm continuation with completed bars only. A 0.10 ATR buffer
            # rejects marginal, spread-sensitive breaks of the prior extreme.
            signal_bar = bars.iloc[i - 1]
            prior_bar = bars.iloc[i - 2]
            breakout_buffer = atr * 0.10
            confirmed = (
                (direction > 0 and signal_bar.close > prior_bar.high + breakout_buffer)
                or (direction < 0 and signal_bar.close < prior_bar.low - breakout_buffer)
            )
            if not confirmed:
                direction = 0
            else:
                sig_name = "BUFFERED_BREAKOUT_" + sig_name
        if direction == 0 or not direction_allowed(direction, hour, c):
'''
if text.count(old) != 1:
    raise SystemExit(f"Expected one failed-fade entry block, found {text.count(old)}")
text = text.replace(old, new, 1)

text, renamed = re.subn(
    r'name="universal_liquid_failed_breakout_fade_v1"',
    'name="universal_liquid_buffered_breakout_v2"',
    text,
    count=1,
)
if renamed != 1:
    raise SystemExit("Could not rename the sole research candidate")
engine.write_text(text, encoding="utf-8")

print(
    "Applied one revision: 0.10 ATR closed-bar buffered breakout continuation; "
    "evaluation windows left frozen by design"
)
