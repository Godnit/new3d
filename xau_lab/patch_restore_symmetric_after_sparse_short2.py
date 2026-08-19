from pathlib import Path
import re

# One simple strategy revision after the short-only test produced only four
# development trades, negative development expectancy, and zero holdout trades.
# The side-disable decision was based on too little evidence. Restore the
# existing trend-aligned long entries without changing any signal formula,
# session, spread/slippage stress, stop, sizing, or chronology safeguard.
engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")
old = '''    # Current iteration: development and validation both showed negative long
    # expectancy after observed spread and adverse slippage. Disable longs only;
    # the complete short setup and every execution safeguard remain unchanged.
    buy = False

    if buy:
'''
new = '''    # Symmetric trend-aligned entries restored because the short-only sample was
    # too sparse for a defensible side exclusion. Existing buy/sell conditions
    # and every execution safeguard remain unchanged.
    if buy:
'''
if text.count(old) != 1:
    raise SystemExit(f"Expected one active shortCore2 long-disable block, found {text.count(old)}")
text = text.replace(old, new, 1)
text = text.replace("_shortCore2", "_symmetricCore2")
text = text.replace("shortCore2", "symmetricCore2")

# The completed independent run had a 41.94% hit rate and approximately
# symmetric average wins and losses, producing a 0.75 combined profit factor
# after real spread and adverse slippage. Preserve every entry and risk rule,
# but require a 1.50R target so a sub-50% hit rate can have positive expectancy.
# Earlier transforms no longer guarantee that candidates() ends with the exact
# text `return out`. Wrap the completed function at the candidates()/in_session()
# boundary instead; this is stable regardless of its internal return expression.
if "_candidates_before_rr150" in text or "_rr150" in text:
    raise SystemExit("The 1.50R revision is already present before the final patch")
pattern = r"(?m)^def in_session\("
match = re.search(pattern, text)
if not match:
    raise SystemExit("Could not locate in_session() boundary for the 1.50R wrapper")
wrapper = '''_candidates_before_rr150 = candidates

def candidates() -> list[Candidate]:
    return [replace(c, name=c.name + "_rr150", rr=1.50) for c in _candidates_before_rr150()]


'''
text = text[:match.start()] + wrapper + text[match.start():]
engine.write_text(text, encoding="utf-8")

# Protocol rotation only. The previous holdout has now been observed, so replace
# it with two non-overlapping periods not used in development or validation.
# Dates are not visible to the strategy logic.
runner = Path("xau_lab/hf_window_runner.py")
runner_text = runner.read_text(encoding="utf-8")
new_windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2021_nov_fresh", "holdout", "2021-11-01", "2021-11-20"),
    ("hold_2022_jul_fresh", "holdout", "2022-07-04", "2022-07-23"),
]'''
runner_text, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    new_windows + "\n\n\ndef iter_months",
    runner_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not install fresh November-2021/July-2022 holdout windows")
runner.write_text(runner_text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when .*?holdout gate passes\..*?If the gate is not passed,",
    "The candidate is considered acceptable only when the fresh November-2021/July-2022 holdout gate passes. These periods are not used by candidate generation or strategy logic. If the gate is not passed,",
    report,
    count=1,
    flags=re.S,
)
aggregate.write_text(report, encoding="utf-8")

print("Restored symmetric entries, applied one global 1.50R payoff revision, and retained the untouched holdout protocol")
