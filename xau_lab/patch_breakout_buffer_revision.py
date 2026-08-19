from pathlib import Path

# One economically defensible revision for this iteration:
# require the completed signal bar to clear the prior bar's extreme by a small
# ATR-normalized buffer, rather than accepting a marginal one-tick breakout.
# This reduces spread-sensitive false breaks without using dates, directions,
# or holdout-specific behavior. All inputs are completed bars.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

old = '''            confirmed = (
                (direction > 0 and signal_bar.close > prior_bar.high)
                or (direction < 0 and signal_bar.close < prior_bar.low)
            )
'''
new = '''            breakout_buffer = atr * 0.10
            confirmed = (
                (direction > 0 and signal_bar.close > prior_bar.high + breakout_buffer)
                or (direction < 0 and signal_bar.close < prior_bar.low - breakout_buffer)
            )
'''
if text.count(old) != 1:
    raise SystemExit(f"Expected one confirmed-breakout block, found {text.count(old)}")
text = text.replace(old, new, 1)
text = text.replace(
    'name="universal_liquid_confirmed_breakout_v1"',
    'name="universal_liquid_buffered_breakout_v2"',
    1,
)
if 'name="universal_liquid_buffered_breakout_v2"' not in text:
    raise SystemExit("Could not rename the sole research candidate")
engine.write_text(text, encoding="utf-8")
print("Applied one revision: 0.10 ATR closed-bar breakout buffer; windows unchanged")
