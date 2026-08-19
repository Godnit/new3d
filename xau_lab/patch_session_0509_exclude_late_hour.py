from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision after the 05:00-09:59 EET/EEST run.
# Across development and validation, the final 09:00-09:59 hour generated
# 31 trades with about -18.12 USD net, while the earlier 05:00-08:59 hours
# were materially less negative and included the only consistently positive
# hour. Keep direction, signals, trend filters, stops, targets, risk, costs,
# validation protocol, and untouched holdouts unchanged. Remove only the late
# hour to avoid the transition into a noisier post-open regime.
old = '''                name=c.name + "_s0510",
                baseline_hour_rules=False,
                session_start=5,
                session_end=10,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0509",
                baseline_hour_rules=False,
                session_start=5,
                session_end=9,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one 05:00-10:00 liquidity-session candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one session revision: trade 05:00-08:59 EET/EEST")
