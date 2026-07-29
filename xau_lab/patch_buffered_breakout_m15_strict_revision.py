from pathlib import Path

# One economically defensible revision for this iteration:
# require completed M15 trend alignment instead of merely vetoing the opposite
# M15 trend. The previous buffered-breakout candidate lost broadly in both
# development and validation, which is consistent with one-minute breakouts
# occurring inside weak or sideways higher-timeframe structure. This universal
# filter uses only completed M15 bars and does not alter any evaluation dates.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

old_name = 'name="universal_liquid_buffered_breakout_v2"'
new_name = 'name="universal_liquid_buffered_breakout_m15strict_v3"'
if text.count(old_name) != 1:
    raise SystemExit(f"Expected one buffered-breakout candidate, found {text.count(old_name)}")
text = text.replace(old_name, new_name, 1)

old_mode = 'm15_mode="veto"'
new_mode = 'm15_mode="strict"'
if text.count(old_mode) != 1:
    raise SystemExit(f"Expected one M15 veto mode, found {text.count(old_mode)}")
text = text.replace(old_mode, new_mode, 1)

engine.write_text(text, encoding="utf-8")
print(
    "Applied one revision: require strict completed-M15 trend alignment for "
    "buffered M1 breakouts; frozen dev/validation/holdout windows unchanged"
)
