from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

marker = '''                    out.append(
                        Candidate(
'''
if marker not in text:
    raise SystemExit("candidate construction marker not found")

# Keep the frozen v5.60 baseline unchanged. For the research candidates only,
# remove the broker-specific absolute spread ceiling and retain the volatility-
# normalized spread/ATR ceiling. This is one simple economic revision: trading
# cost should scale with the current gold volatility regime instead of a fixed
# dollar value learned from one broker and one month.
needle = '''                            fail_fast_current_r=ffcur,
                        )
'''
replacement = '''                            fail_fast_current_r=ffcur,
                            max_spread_price=999.0,
                        )
'''
count = text.count(needle)
if count != 1:
    raise SystemExit(f"expected one robust candidate construction, found {count}")
text = text.replace(needle, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Patched research candidates to use only volatility-normalized spread filtering")
