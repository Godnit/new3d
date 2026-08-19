from pathlib import Path

# One simple, economically defensible revision after the completed short-only
# protocol failed development, validation selection, and the untouched holdout.
# Gold can sustain intraday trends in either direction, so remove only the final
# short-only override. All signal definitions, M1/M5/M15 filters, liquid-core
# hours, observed-spread stress, adverse slippage, risk sizing, stops, targets,
# chronological-integrity safeguards, and holdout windows remain unchanged.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''    # Current iteration: directional asymmetry, short entries only.
    buy = False

    if buy:
'''
new = '''    # Symmetric trend-aligned entries restored after the short-only protocol
    # failed independently. The existing buy and sell conditions are unchanged.
    if buy:
'''

count = text.count(old)
if count != 1:
    raise SystemExit(f"Expected one active short-only override, found {count}")

text = text.replace(old, new, 1)
text = text.replace("_shortCore", "_symmetricCore")
text = text.replace("shortCore", "symmetricCore")
path.write_text(text, encoding="utf-8")
print("Restored symmetric trend-aligned entries; all other logic and holdouts unchanged")
