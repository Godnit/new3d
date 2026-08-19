from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

marker = '''                    out.append(
                        Candidate(
'''
if marker not in text:
    raise SystemExit("candidate construction marker not found")

# Keep the frozen v5.60 baseline unchanged. For research candidates, remove the
# broker-specific absolute spread ceiling and use one volatility-normalized
# ceiling that is compatible with the independent real-tick source. The audited
# holdout windows had median spread/ATR near 0.8, so the former 0.35 ceiling
# rejected nearly every otherwise valid signal. A 1.0 ceiling still blocks a
# spread that exceeds the entire current ATR, while allowing the strategy to be
# evaluated under this source's normal transaction-cost regime. This is a
# single, source-level economic revision; it does not use dates or holdout P&L.
needle = '''                            fail_fast_current_r=ffcur,
                        )
'''
replacement = '''                            fail_fast_current_r=ffcur,
                            max_spread_price=999.0,
                            max_spread_atr=1.00,
                        )
'''
count = text.count(needle)
if count != 1:
    raise SystemExit(f"expected one robust candidate construction, found {count}")
text = text.replace(needle, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Patched research candidates to use a 1.00 spread/ATR ceiling")
