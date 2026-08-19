from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '    sessions = [(0, 8), (2, 8), (3, 10), (7, 13), (2, 13)]\n'
new = '    sessions = [(12, 18), (13, 20), (14, 21)]\n'
if old not in text:
    raise SystemExit("session candidate marker not found")
text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("Applied one strategy revision: move candidate sessions to the liquid London/New York overlap and early US session")
