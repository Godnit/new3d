from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision based only on development and validation.
# In the latest audited run, server hour 04:00-04:59 produced 37 dev+validation
# trades with -11.34 USD net and a materially sub-1 profit factor, while
# 05:00-05:59 produced 16 trades with +4.56 USD net. The first hour is also the
# thinner pre-London segment. Keep signals, direction, trend filters, risk,
# stops, targets, spread/slippage stress, windows and untouched holdout fixed;
# remove only the weak opening hour.
old = '''                name=c.name + "_s0406_sparsefix",
                baseline_hour_rules=False,
                session_start=4,
                session_end=6,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0506_openhour_removed",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit(
        f"Expected exactly one final 04:00-05:59 candidate block, found {text.count(old)}"
    )

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one revision: remove weak 04:00 server hour; retain 05:00-05:59")
