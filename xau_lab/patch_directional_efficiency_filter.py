from pathlib import Path

# One simple, date-agnostic revision after the latest independent run failed in
# development, validation, and holdout: require the closed M1 signal candle to
# express genuine directional efficiency rather than a small body inside a long
# two-sided range. This targets EMA-cross whipsaws without adding another
# indicator, changing risk, selecting a preferred direction/hour, or touching
# any development/validation/holdout dates.
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
path.write_text(text, encoding="utf-8")
print("Applied one revision: closed-candle directional efficiency >= 0.55; holdout unchanged")
