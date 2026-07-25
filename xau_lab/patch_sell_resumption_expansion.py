from pathlib import Path

# One simple statistical revision after run 263:
# the global cross-sell-only rule produced too few observations (22 total and
# zero holdout trades). Preserve the short-only, trend-aligned thesis and all
# risk/execution controls, but allow the two already-defined sell-resumption
# setups (continuation and follow-through) alongside EMA9 cross sells.
# No date, weekday, hour, or holdout rule is changed.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")
old = "    sell = sell and cross_sell\n"
new = "    sell = sell and (cross_sell or cont_sell or follow_sell)\n"
if text.count(old) != 1:
    raise SystemExit(f"Expected exactly one cross-sell restriction, found {text.count(old)}")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Expanded global short-only entry from cross sell to cross/continuation/follow sell")
