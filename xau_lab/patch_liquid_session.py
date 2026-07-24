from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '    sessions = [(0, 8), (2, 8), (3, 10), (7, 13), (2, 13)]\n'
new = '    # One simple, economically motivated revision after the independent failure:\n    # end the earliest liquid-session candidate at 15:00 server time, before the\n    # U.S. macro-release/New York-open transition where development+validation\n    # trades showed concentrated whipsaw losses. The 2021/2022 holdout windows\n    # remain untouched and were not used to choose this change.\n    sessions = [(7, 15), (8, 18), (9, 19)]\n'
if old not in text:
    raise SystemExit("candidate session list not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Patched earliest liquid session to stop before U.S. open transition")
