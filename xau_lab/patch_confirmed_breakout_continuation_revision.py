from pathlib import Path
import re

# Strategy state carried forward:
# abandon the consistently loss-making failed-breakout fade and require the
# original trend direction to close beyond the prior completed bar's extreme.
# A 0.10 ATR clearance rejects marginal spread-sensitive breaks.
#
# One new economically defensible revision for this iteration:
# require strict completed-M15 trend alignment instead of merely vetoing the
# opposite M15 trend. The previous buffered-breakout candidate lost broadly in
# development and validation, consistent with M1 breaks occurring inside weak
# or sideways higher-timeframe structure. This is universal and date-agnostic.
#
# IMPORTANT: this patch must not alter evaluation windows. The runner owns the
# frozen development, validation, and holdout protocol. Keeping dates out of
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
    'name="universal_liquid_buffered_breakout_m15strict_v3"',
    text,
    count=1,
)
if renamed != 1:
    raise SystemExit("Could not rename the sole research candidate")

old_mode = 'm15_mode="veto"'
new_mode = 'm15_mode="strict"'
if text.count(old_mode) != 1:
    raise SystemExit(f"Expected one M15 veto mode, found {text.count(old_mode)}")
text = text.replace(old_mode, new_mode, 1)

engine.write_text(text, encoding="utf-8")

print(
    "Applied buffered breakout continuation plus one new revision: strict "
    "completed-M15 trend alignment; evaluation windows remain frozen"
)
