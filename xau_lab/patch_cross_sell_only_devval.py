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
    "\n    # One simple revision derived strictly from development and validation:\n"
    "    # continuation/follow short entries had materially negative expectancy,\n"
    "    # while EMA9 reclaim cross shorts were slightly positive. Keep only the\n"
    "    # cross-short trigger globally; no date, weekday, or hour exception.\n"
    "    sell = sell and cross_sell\n"
    "    if sell:\n",
    1,
)
text = text[:start] + segment + text[end:]
path.write_text(text, encoding="utf-8")
print("Applied global cross-sell-only revision derived from development/validation")
