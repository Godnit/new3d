from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''            name="rev_cont_buy_follow_sell",
            baseline_hour_rules=False,
            session_start=13,
            session_end=20,
'''
new = '''            name="rev_cont_buy_follow_sell",
            baseline_hour_rules=False,
            session_start=16,
            session_end=19,
'''
if old not in text:
    raise SystemExit("revision candidate session marker not found")
text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("Applied one simple revision: restrict specialized strategy to server hours 16-18")
