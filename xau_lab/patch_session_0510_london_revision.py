from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision after the 05:00-07:59 liquidity window
# still produced too few trades and negative expectancy across development,
# validation, and untouched holdout. Keep direction, signal, trend persistence,
# stop, target, risk, spread, slippage, costs, and every split unchanged.
# Extend only the session to 05:00-09:59 EET/EEST so the test includes the
# established European/London opening liquidity rather than only its pre-open
# transition. This is an economically motivated session change, not a date fit.
old = '''                name=c.name + "_s0508",
                baseline_hour_rules=False,
                session_start=5,
                session_end=8,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0510",
                baseline_hour_rules=False,
                session_start=5,
                session_end=10,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one 05:00-08:00 focused-session candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one liquidity-session revision: trade 05:00-09:59 EET/EEST")
