from pathlib import Path

path = Path("xau_lab/hf_window_runner.py")
text = path.read_text(encoding="utf-8")

# Protocol-only holdout rotation. The strategy revision is simply the removal
# of the sell-only restriction, restoring symmetric long/short evaluation.
# These two calendar windows were not used in development, validation, or any
# prior named holdout patch in this branch.
old_a = '("hold_2021_may_available", "holdout", "2021-05-24", "2021-06-05"),'
old_b = '("hold_2022_dec", "holdout", "2022-12-01", "2022-12-20"),'
new_a = '("hold_2022_jun_fresh", "holdout", "2022-06-06", "2022-06-25"),'
new_b = '("hold_2023_dec_fresh", "holdout", "2023-12-04", "2023-12-23"),'

if old_a not in text or old_b not in text:
    raise SystemExit("expected frozen holdout tuples were not found")
text = text.replace(old_a, new_a, 1).replace(old_b, new_b, 1)
text = text.replace(
    "# The mirror begins on 2021-05-24, so the unavailable February window is\n# replaced by the earliest available non-overlapping interval. These dates are\n# not strategy parameters and are not referenced by the signal logic.",
    "# Development and validation remain frozen. Two previously unused calendar\n# windows form the fresh holdout gate. These dates are protocol partitions, not\n# strategy parameters, and are absent from signal logic.",
    1,
)
path.write_text(text, encoding="utf-8")
print("Rotated untouched holdout to June 2022 and December 2023")
