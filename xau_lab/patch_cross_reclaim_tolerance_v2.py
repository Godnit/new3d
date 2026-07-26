from pathlib import Path

# One simple, date-agnostic revision for this iteration.
# The latest audited real-tick run produced only 15 trades across ten independent
# windows. Validation was positive, but the untouched holdout was flat and the
# sample was too small. Keep direction (long only), session, trend filters,
# stops, targets, risk, spread, slippage, and all frozen windows unchanged.
# Relax only the prior-bar EMA9 crossing test into a small reclaim tolerance:
# the previous close may sit no more than 0.08 ATR above EMA9, while the signal
# bar must still touch EMA9 and close back above it. This accounts for quote
# noise and shallow pullbacks without introducing a new indicator or a
# date-specific rule.

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = "    cross_buy = b2.close <= b2.ema9 and b1.low <= b1.ema9 and b1.close > b1.ema9\n"
new = (
    "    cross_buy = (\n"
    "        b2.close <= b2.ema9 + atr * 0.08\n"
    "        and b1.low <= b1.ema9\n"
    "        and b1.close > b1.ema9\n"
    "    )\n"
)

if text.count(old) != 1:
    raise SystemExit(
        f"Expected exactly one canonical cross_buy expression, found {text.count(old)}"
    )

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one revision: 0.08 ATR tolerance for bullish EMA9 reclaim")
