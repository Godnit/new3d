from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple revision after the latest independent run produced zero validation
# trades and only one holdout trade: remove the extra M15 EMA20 slope gate while
# retaining the existing M15 trend veto, M5 trend filter, local EMA alignment,
# closed-bar EMA9 cross, spread filter, and all risk controls. This addresses
# over-filtering without adding date-specific rules or a new indicator.
for line in (
    "        and m15_slope_up\n",
    "        and m15_slope_down\n",
):
    if text.count(line) != 1:
        raise SystemExit(f"Expected exactly one slope condition: {line.strip()}")
    text = text.replace(line, "", 1)

path.write_text(text, encoding="utf-8")
print("Removed only the extra M15 slope gate; retained M15 trend veto")
