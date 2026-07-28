from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = "and directional_efficiency >= 0.55"
new = "and directional_efficiency >= 0.35"

if text.count(old) != 1:
    raise SystemExit(
        f"Expected exactly one active 0.55 directional-efficiency threshold, found {text.count(old)}"
    )

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print(
    "Relaxed the single candle directional-efficiency threshold from 0.55 to 0.35 "
    "after the prior protocol produced only 29 combined trades. Sessions, signal types, "
    "trend filters, risk, execution stress, and untouched holdout windows are unchanged."
)
