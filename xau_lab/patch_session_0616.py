from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '    sessions = [(7, 15), (8, 18), (9, 19)]\n'
new = '''    # Single post-failure revision: add one broader European-to-early-US
    # liquidity window. This addresses the validation sample being too sparse
    # (only one to three trades for the development leaders) without changing
    # signal, stop, target, or holdout dates. The 2025 holdout remains sealed.
    sessions = [(6, 16), (7, 15), (8, 18), (9, 19)]
'''

if old not in text:
    raise SystemExit("liquid session candidate list not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Added one broader 06:00-16:00 server-time liquidity candidate")
