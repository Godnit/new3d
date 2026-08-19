from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision after the latest independent
# development + validation run produced too few trades to evaluate reliably.
# Keep the frozen report baseline unchanged. For research candidates, allow a
# trend candle to close within the directional 65% of its range instead of the
# directional 40%. This retains direction, body-size, M1/M5 trend, distance,
# spread, and risk filters, but avoids requiring an unusually perfect candle
# close that starved the sample. No date, weekday, or holdout-specific rule is
# introduced.
marker = '''    return out


def in_session'''
replacement = '''    out = [
        candidate
        if candidate.baseline_hour_rules
        else replace(candidate, close_extreme_fraction=0.65)
        for candidate in out
    ]
    return out


def in_session'''

if marker not in text:
    raise SystemExit("candidate return marker not found")
text = text.replace(marker, replacement, 1)
path.write_text(text, encoding="utf-8")
print("Relaxed research-candidate candle close location from directional 40% to 65%")
