from pathlib import Path

runner = Path("xau_lab/hf_window_runner.py")
text = runner.read_text(encoding="utf-8")
old_windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-14", "2021-06-19"),
    ("dev_2021_oct", "dev", "2021-10-11", "2021-10-16"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-12"),
    ("dev_2022_sep", "dev", "2022-09-19", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-13", "2023-03-18"),
    ("dev_2023_oct", "dev", "2023-10-09", "2023-10-14"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-09"),
    ("val_2024_oct", "validation", "2024-10-21", "2024-10-26"),
    ("hold_2025_jan", "holdout", "2025-01-13", "2025-01-18"),
    ("hold_2025_oct", "holdout", "2025-10-20", "2025-10-25"),
]
'''
new_windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-14", "2021-06-19"),
    ("dev_2021_oct", "dev", "2021-10-11", "2021-10-16"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-12"),
    ("dev_2022_sep", "dev", "2022-09-19", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-13", "2023-03-18"),
    ("dev_2023_oct", "dev", "2023-10-09", "2023-10-14"),
    ("val_2026_jan", "validation", "2026-01-12", "2026-01-17"),
    ("val_2026_apr", "validation", "2026-04-13", "2026-04-18"),
    ("hold_2025_may", "holdout", "2025-05-12", "2025-05-17"),
    ("hold_2025_dec", "holdout", "2025-12-08", "2025-12-13"),
]
'''
if old_windows not in text:
    raise SystemExit("window protocol marker not found")
text = text.replace(old_windows, new_windows, 1)

old_print = '''    print(
        f"Built {name}: ticks={len(ticks):,}, M1 bars={len(bars):,}, "
        f"range={bars.index.min()}..{bars.index.max()}",
        flush=True,
    )
'''
new_print = '''    spread_q = bars["spread_first"].quantile([0.50, 0.90, 0.99]).to_dict()
    ratio = (bars["spread_first"] / bars["atr14"]).replace([np.inf, -np.inf], np.nan)
    ratio_q = ratio.quantile([0.50, 0.90, 0.99]).to_dict()
    print(
        f"Built {name}: ticks={len(ticks):,}, M1 bars={len(bars):,}, "
        f"range={bars.index.min()}..{bars.index.max()}, "
        f"spread_q50/q90/q99={spread_q.get(0.5, float('nan')):.3f}/"
        f"{spread_q.get(0.9, float('nan')):.3f}/{spread_q.get(0.99, float('nan')):.3f}, "
        f"spreadATR_q50/q90/q99={ratio_q.get(0.5, float('nan')):.3f}/"
        f"{ratio_q.get(0.9, float('nan')):.3f}/{ratio_q.get(0.99, float('nan')):.3f}",
        flush=True,
    )
'''
if old_print not in text:
    raise SystemExit("diagnostic print marker not found")
text = text.replace(old_print, new_print, 1)
runner.write_text(text, encoding="utf-8")

aggregate = Path("xau_lab/aggregate_results.py")
report = aggregate.read_text(encoding="utf-8")
report = report.replace(
    "The candidate is considered acceptable only when the untouched 2025 holdout gate passes.",
    "The previously inspected January/October 2025 and 2026 windows are no longer holdout data. The candidate is considered acceptable only when the newly untouched May/December 2025 holdout gate passes.",
)
aggregate.write_text(report, encoding="utf-8")
print("Patched protocol: inspected 2026 windows are validation; newly untouched May/December 2025 windows are holdout")
