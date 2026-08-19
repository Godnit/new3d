from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple economic revision, chosen only from development + validation:
# long CROSS signals lost -12.01 USD over 30 trades while short CROSS signals
# made +1.86 USD over 22 trades. Keep every timing, trend, spread, stop, target,
# trailing and risk rule unchanged; disable only the weak long direction for
# research candidates. The frozen v5.60 baseline remains unchanged.
anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
replacement = '''    if not c.baseline_hour_rules:
        buy_trigger = False

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''

if "if not c.baseline_hour_rules:\n        buy_trigger = False" not in text:
    if anchor not in text:
        raise SystemExit("signal-direction anchor not found")
    text = text.replace(anchor, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Applied one-variable research revision: sell-only direction")
