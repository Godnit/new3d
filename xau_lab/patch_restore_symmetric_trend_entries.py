from pathlib import Path

# One simple, economically defensible revision after run 267:
# the short-only strategy lost in every development window, failed validation,
# and produced no holdout trades. Gold can sustain both bullish and bearish
# intraday trends, so remove only the directional short-only override while
# preserving the same M1/M5/M15 trend alignment, entry patterns, spread filter,
# risk sizing, stops, trailing logic, sessions, and untouched holdout windows.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''    buy = False  # global cross-sell-only revision
    sell = sell and (cross_sell or cont_sell or follow_sell)
    if buy:
'''
new = '''    # Symmetric trend-following revision: retain the engine's already-defined
    # cross, continuation, and follow-through triggers in both directions.
    if buy:
'''

if text.count(old) != 1:
    raise SystemExit(
        f"Expected exactly one active short-only override, found {text.count(old)}"
    )

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Restored symmetric trend-aligned buy and sell entries; holdout unchanged")
