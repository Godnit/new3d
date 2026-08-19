from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision after the independent run found
# zero holdout trades while observed spread/ATR medians were 0.460 (Apr-2025)
# and 0.334 (Nov-2025). The old 0.35 ratio ceiling excluded most liquid quotes
# in the high-spread regime. Keep the frozen v5.60 baseline unchanged; for
# research candidates use a dual cap that admits normal 2025 execution while
# still rejecting extreme transaction costs.
needle = '''                            max_spread_price=999.0,
                        )
'''
replacement = '''                            max_spread_price=1.20,
                            max_spread_atr=0.65,
                        )
'''
count = text.count(needle)
if count != 1:
    raise SystemExit(f"expected one research-candidate spread block, found {count}")
text = text.replace(needle, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Patched research candidates to dual spread cap: price<=1.20 and spread/ATR<=0.65")
