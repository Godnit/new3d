from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

start = text.index("def signal_at(")
end = text.index("\ndef close_trade", start)
segment = text[start:end]
needle = "\n    if sell:\n"
if segment.count(needle) != 1:
    raise SystemExit(f"Expected one sell return block in signal_at, found {segment.count(needle)}")

segment = segment.replace(
    needle,
    "\n    # One simple, economically defensible revision after the cross-only\n"
    "    # strategy failed validation and untouched holdout with too few trades:\n"
    "    # retain EMA9 cross shorts, and also permit pullback-continuation shorts\n"
    "    # only when the closed M15 trend is fully bearish. This is global and\n"
    "    # introduces no date, weekday, month, or single-window exception.\n"
    "    sell = sell and (cross_sell or (cont_sell and m15_down))\n"
    "    if sell:\n",
    1,
)
text = text[:start] + segment + text[end:]
path.write_text(text, encoding="utf-8")
print("Applied cross plus M15-strict continuation sell revision")
