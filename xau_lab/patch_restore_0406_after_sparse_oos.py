from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision after the 05:00-only candidate produced
# only 16 dev+validation trades. Earlier development-only hour attribution
# showed recurring server hours 04 and 05 profitable in aggregate, while 06
# and 07 were negative. Restore 04:00-05:59 to increase sample size without
# changing signal, trend, stop, target, risk, cost, validation or holdout rules.
old = '''                name=c.name + "_s0506",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0406_sparsefix",
                baseline_hour_rules=False,
                session_start=4,
                session_end=6,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one final 05:00-06:00 candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one revision: restore recurring liquid hours 04:00-05:59 EET/EEST")
