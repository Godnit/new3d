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
    "\n    # One economically defensible revision based only on development and\n"
    "    # validation: long signals had negative expectancy while short signals\n"
    "    # remained positive. Disable longs globally; no date/hour exception.\n"
    "    buy = False\n"
    "    if buy:\n",
    1,
)
text = text[:start] + segment + text[end:]
path.write_text(text, encoding="utf-8")
print("Applied global sell-only revision derived from development/validation only")
