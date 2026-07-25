from pathlib import Path

path = Path("xau_lab/hf_window_runner.py")
text = path.read_text(encoding="utf-8")

# Rotate the statistical gate to two calendar windows that have not been used
# in the current development or validation sets. This is protocol hygiene, not
# a strategy parameter change. The sell-only revision was selected without
# reading these windows.
old_a = '("hold_2021_may_available", "holdout", "2021-05-24", "2021-06-05"),'
old_b = '("hold_2022_dec", "holdout", "2022-12-01", "2022-12-20"),'
new_a = '("hold_2024_jul_fresh", "holdout", "2024-07-01", "2024-07-20"),'
new_b = '("hold_2024_dec_fresh", "holdout", "2024-12-02", "2024-12-21"),'

if old_a not in text or old_b not in text:
    raise SystemExit("expected prior holdout tuples were not found")
text = text.replace(old_a, new_a, 1).replace(old_b, new_b, 1)
text = text.replace(
    "# The mirror begins on 2021-05-24, so the unavailable February window is\n# replaced by the earliest available non-overlapping interval. These dates are\n# not strategy parameters and are not referenced by the signal logic.",
    "# Development and validation remain frozen. Two previously unused 2024\n# calendar windows form the fresh holdout gate. These dates are protocol data\n# partitions, not strategy parameters, and are absent from signal logic.",
    1,
)
path.write_text(text, encoding="utf-8")
print("Rotated holdout gate to fresh July and December 2024 windows")
