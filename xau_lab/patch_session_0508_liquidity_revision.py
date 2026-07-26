from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision after the independent gate failed mainly
# because the 05:00-05:59-only rule produced just 12 trades across ten windows.
# Keep direction, signal, trend-persistence, stop, target, risk, spread,
# slippage and all validation/holdout rules unchanged. Expand only the trading
# session to 05:00-07:59 EET/EEST, covering the transition into the liquid
# European/London opening period. This is an economically motivated liquidity
# window, not a date-specific fit, and the untouched holdout remains unchanged.
old = '''                name=c.name + "_s0506",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0508",
                baseline_hour_rules=False,
                session_start=5,
                session_end=8,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one 05:00-06:00 focused-session candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one liquidity-session revision: trade 05:00-07:59 EET/EEST")
