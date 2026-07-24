from pathlib import Path

path = Path("xau_lab/hf_window_runner.py")
text = path.read_text(encoding="utf-8")
old = '("hold_2021_feb", "holdout", "2021-02-01", "2021-02-20"),'
new = '("hold_2021_may", "holdout", "2021-05-24", "2021-06-05"),'
if old not in text:
    raise SystemExit("Expected unavailable holdout tuple was not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Replaced unavailable February 2021 holdout with earliest available non-overlapping May 2021 window")
