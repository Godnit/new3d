from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

start = text.index("def signal_at(")
end = text.index("\ndef close_trade", start)
segment = text[start:end]
needle = "\n    if buy:\n"
if segment.count(needle) != 1:
    raise SystemExit(f"Expected one buy return block in signal_at, found {segment.count(needle)}")

segment = segment.replace(
    needle,
    "\n    # One simple global revision after the latest independent failure:\n"
    "    # retain only EMA9 cross/reclaim entries, but restore directional\n"
    "    # symmetry. The prior buy-only restriction lost in development,\n"
    "    # validation, and untouched holdout. Gold trends in both directions,\n"
    "    # so research candidates now permit the same cross trigger for buys\n"
    "    # and sells while preserving all session, M5/M15 trend, spread, risk,\n"
    "    # stop, trailing, chronology, and holdout controls.\n"
    "    if not c.baseline_hour_rules:\n"
    "        buy = buy and cross_buy\n"
    "        sell = sell and cross_sell\n"
    "\n"
    "    if buy:\n",
    1,
)

text = text[:start] + segment + text[end:]
path.write_text(text, encoding="utf-8")
print("Applied symmetric cross-only trend-entry revision")
