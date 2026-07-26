from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision selected from development and validation only.
# In the latest audited run, 05:00-05:59 EET/EEST produced 13 trades, +2.69 USD
# and PF 1.29 across dev+validation, while 06:00-06:59 produced 9 trades,
# -4.67 USD and PF 0.55. Keep every signal, trend, risk, stop, target, spread,
# slippage, validation and holdout rule unchanged; remove only the second hour.
old = '''                name=c.name + "_s0507",
                baseline_hour_rules=False,
                session_start=5,
                session_end=7,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0506",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one 05:00-07:00 candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one revision: trade only 05:00-05:59 EET/EEST")
