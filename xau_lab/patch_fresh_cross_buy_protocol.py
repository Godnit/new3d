from pathlib import Path

path = Path("xau_lab/hf_window_runner.py")
text = path.read_text(encoding="utf-8")

# The base window lengths were expanded after this protocol was first written.
# Accept the current long validation tuples, while retaining compatibility with
# the earlier short tuples. This is a data-protocol repair only: no strategy
# parameter or signal rule is changed.
replacement_groups = [
    (
        [
            '("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),',
            '("val_2024_mar", "validation", "2024-03-04", "2024-03-09"),',
        ],
        '("val_2024_jan_fresh", "validation", "2024-01-08", "2024-01-20"),',
    ),
    (
        [
            '("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),',
            '("val_2024_oct", "validation", "2024-10-21", "2024-10-26"),',
        ],
        '("val_2024_jul_fresh", "validation", "2024-07-08", "2024-07-20"),',
    ),
    (
        ['("hold_2025_dec_a", "holdout", "2025-12-01", "2025-12-13"),'],
        '("hold_2021_jul_fresh", "holdout", "2021-07-05", "2021-07-17"),',
    ),
    (
        ['("hold_2025_dec_b", "holdout", "2025-12-15", "2025-12-27"),'],
        '("hold_2022_jan_fresh", "holdout", "2022-01-10", "2022-01-22"),',
    ),
]

for alternatives, new in replacement_groups:
    matched = next((old for old in alternatives if old in text), None)
    if matched is None:
        raise SystemExit(
            "Expected current window tuple was not found; checked: "
            + " | ".join(alternatives)
        )
    text = text.replace(matched, new, 1)

path.write_text(text, encoding="utf-8")
print("Rotated validation and holdout to fresh non-overlapping windows for the cross-buy revision")
