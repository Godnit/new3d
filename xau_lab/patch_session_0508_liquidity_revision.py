from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision after the independent 05:00-07:59 test
# remained negative and produced only 25 trades across ten windows. Keep the
# direction, signal, trend-persistence, stop, target, risk, spread, slippage,
# costs, validation protocol, and untouched holdout unchanged. Extend only the
# trading session to 05:00-09:59 EET/EEST so the test includes the established
# European/London opening liquidity rather than only its pre-open transition.
# This is an economically motivated session change, not a date-specific fit.
old = '''                name=c.name + "_s0506",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0510",
                baseline_hour_rules=False,
                session_start=5,
                session_end=10,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one 05:00-06:00 focused-session candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one liquidity-session revision: trade 05:00-09:59 EET/EEST")
