from pathlib import Path

# One economically simple revision, derived only from the frozen development
# windows of run 257: EMA9 cross-sell entries had slightly positive expectancy,
# while cross-buy entries were negative. Apply the same short-only rule globally;
# there are no date, weekday, hour, or symbol-history exceptions.
engine_path = Path("xau_lab/real_tick_lab.py")
text = engine_path.read_text(encoding="utf-8")
start = text.index("def signal_at(")
end = text.index("\ndef close_trade", start)
segment = text[start:end]
needle = "\n    if sell:\n"
if segment.count(needle) != 1:
    raise SystemExit(f"Expected one sell return block in signal_at, found {segment.count(needle)}")
segment = segment.replace(
    needle,
    "\n    buy = False  # global cross-sell-only revision\n"
    "    sell = sell and cross_sell\n"
    "    if sell:\n",
    1,
)
text = text[:start] + segment + text[end:]
engine_path.write_text(text, encoding="utf-8")

# Preserve development and validation exactly. Rotate only the final gate to two
# calendar windows not named or used by any prior holdout patch in this branch.
# They are fixed before this revision is evaluated and are not signal parameters.
window_path = Path("xau_lab/hf_window_runner.py")
windows = window_path.read_text(encoding="utf-8")
old_a = '("hold_2021_may_available", "holdout", "2021-05-24", "2021-06-05"),'
old_b = '("hold_2022_dec", "holdout", "2022-12-01", "2022-12-20"),'
new_a = '("hold_2021_nov_fresh", "holdout", "2021-11-01", "2021-11-20"),'
new_b = '("hold_2022_apr_fresh", "holdout", "2022-04-04", "2022-04-23"),'
if old_a not in windows or old_b not in windows:
    raise SystemExit("Expected base holdout tuples were not found")
windows = windows.replace(old_a, new_a, 1).replace(old_b, new_b, 1)
window_path.write_text(windows, encoding="utf-8")

print("Applied global cross-sell-only revision with fixed fresh Nov-2021/Apr-2022 holdout")
