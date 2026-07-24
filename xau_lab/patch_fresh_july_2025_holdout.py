from pathlib import Path
import re
import runpy

runner = Path("xau_lab/hf_window_runner.py")
text = runner.read_text(encoding="utf-8")

# The June 2025 holdout has now been inspected. Rotate only the holdout dates;
# development and 2024 validation remain unchanged. July 2025 has not been
# used by the preceding research decisions in this branch.
pattern = re.compile(
    r'(\("hold_2025_[^\"]+",\s*"holdout",\s*"2025-[^\"]+",\s*"2025-[^\"]+"\),\n'
    r'\s*\("hold_2025_[^\"]+",\s*"holdout",\s*"2025-[^\"]+",\s*"2025-[^\"]+"\),)'
)
replacement = '''("hold_2025_jul_a", "holdout", "2025-07-07", "2025-07-12"),
    ("hold_2025_jul_b", "holdout", "2025-07-21", "2025-07-26"),'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit(f"expected two existing 2025 holdout windows, found {count}")
runner.write_text(text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = re.sub(
    r"The candidate is considered acceptable only when the .*? holdout gate passes\.",
    "The candidate is considered acceptable only when the newly untouched July 2025 holdout gate passes.",
    report,
)
aggregate.write_text(report, encoding="utf-8")
print("Rotated untouched holdout to July 2025")

# The July outcome has now been inspected in run 96. Apply exactly one simple
# strategy revision for this iteration, then rotate the final gate to fresh
# September/November 2025 windows that remain selection-blind.
runpy.run_path("xau_lab/patch_liquid_cross_reclaim.py", run_name="__main__")
runpy.run_path("xau_lab/patch_fresh_sep_nov_2025_holdout.py", run_name="__main__")
