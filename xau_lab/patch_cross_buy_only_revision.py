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
    "\n    # One simple global revision after the latest independent run: research\n"
    "    # candidates use only bullish EMA9 reclaim/cross entries. In development\n"
    "    # and validation, cross buys were the only signal family with a positive\n"
    "    # expectancy, while follow/continuation entries and shorts caused most of\n"
    "    # the losses. The frozen Headway baseline remains unchanged.\n"
    "    if not c.baseline_hour_rules:\n"
    "        buy = buy and cross_buy\n"
    "        sell = False\n"
    "\n"
    "    if buy:\n",
    1,
)

text = text[:start] + segment + text[end:]
path.write_text(text, encoding="utf-8")
print("Applied global cross-buy-only research revision")
