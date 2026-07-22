from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

marker = "\ndef in_session(hour: int, c: Candidate) -> bool:\n"
if marker not in text:
    raise SystemExit("candidate wrapper insertion marker not found")
if "def candidates_before_close_location_relax" in text:
    raise SystemExit("close-location revision already applied")

wrapper = '''

# Single strategy revision for this iteration:
# retain every existing trend, risk, spread and session rule, but relax the
# directional candle-close requirement from the upper/lower 35% of the candle
# to the upper/lower 45%. This increases sample size without adding a new
# indicator or a date-specific rule.
candidates_before_close_location_relax = candidates

def candidates() -> list[Candidate]:
    revised: list[Candidate] = []
    for candidate in candidates_before_close_location_relax():
        revised.append(
            replace(
                candidate,
                name=candidate.name + "_cl55",
                close_extreme_fraction=0.55,
            )
        )
    return revised
'''

text = text.replace(marker, wrapper + marker, 1)
path.write_text(text, encoding="utf-8")
print("Applied one strategy revision: close-location threshold 0.65 -> 0.55")
