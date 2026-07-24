from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '    sessions = [(0, 8), (2, 8), (3, 10), (7, 13), (2, 13)]\n'
new = '    # Single economically motivated revision after the first independent failure:\n    # move candidate search from thin early-server hours to the liquid London/New York\n    # trading day. No date-specific rule and no holdout-derived parameter is used.\n    sessions = [(7, 16), (8, 18), (9, 19)]\n'
if old not in text:
    raise SystemExit("candidate session list not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Patched candidate search to liquid London/New York server sessions")
