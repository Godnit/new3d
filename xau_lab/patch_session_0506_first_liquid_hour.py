from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision based only on development and validation.
# In the latest cost-aware real-tick run, the 05:00-05:59 EET/EEST hour was the
# only server hour that was positive in both development and validation. Later
# hours were consistently negative after real spread and adverse slippage. Keep
# signals, trend filters, stops, targets, risk, costs, validation windows and
# untouched holdouts unchanged; restrict only the trading session.
old = '''                name=c.name + "_s0509",
                baseline_hour_rules=False,
                session_start=5,
                session_end=9,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0506",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one 05:00-09:00 candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one session revision: trade only 05:00-05:59 EET/EEST")
