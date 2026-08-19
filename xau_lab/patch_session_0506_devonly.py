from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision based only on the development
# split from the immediately preceding run: server hour 04 produced -1.46 USD
# across 14 development trades, while server hour 05 produced +1.54 USD across
# six development trades. Keep the signal, trend-persistence, stop, target,
# risk, spread and slippage assumptions unchanged; only avoid the thinner first
# hour and trade 05:00-05:59 EET/EEST. Validation and holdout are not used to
# define this change, and the holdout remains untouched for the new run.
old = '''                name=c.name + "_s0406",
                baseline_hour_rules=False,
                session_start=4,
                session_end=6,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0506",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one 04:00-06:00 focused-session candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one development-only revision: trade server hour 05:00-05:59")
