from pathlib import Path

# Prior frozen revision: tolerate a shallow bullish EMA9 reclaim.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = "    cross_buy = b2.close <= b2.ema9 and b1.low <= b1.ema9 and b1.close > b1.ema9\n"
new = (
    "    cross_buy = (\n"
    "        b2.close <= b2.ema9 + atr * 0.08\n"
    "        and b1.low <= b1.ema9\n"
    "        and b1.close > b1.ema9\n"
    "    )\n"
)

if text.count(old) != 1:
    raise SystemExit(
        f"Expected exactly one canonical cross_buy expression, found {text.count(old)}"
    )
text = text.replace(old, new, 1)

# Frozen predecessor restored 04:00-05:59 to address sample sparsity.
old_session = '''                name=c.name + "_s0506",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''
restored_session = '''                name=c.name + "_s0406_sparsefix",
                baseline_hour_rules=False,
                session_start=4,
                session_end=6,
                blocked_hour=24,
'''
if text.count(old_session) != 1:
    raise SystemExit(
        f"Expected exactly one final 05:00-only candidate block, found {text.count(old_session)}"
    )
text = text.replace(old_session, restored_session, 1)

# One new, date-agnostic revision based only on development and validation.
# In the latest audited run, server hour 04:00-04:59 produced 37
# dev+validation trades with -11.34 USD net, while 05:00-05:59 produced 16
# trades with +4.56 USD net. The earlier hour is also the thinner pre-London
# segment. Keep direction, signal, trend, risk, stop, target, execution-cost,
# validation-window and untouched-holdout rules unchanged; remove only hour 04.
weak_open = '''                name=c.name + "_s0406_sparsefix",
                baseline_hour_rules=False,
                session_start=4,
                session_end=6,
                blocked_hour=24,
'''
confirmed_liquidity = '''                name=c.name + "_s0506_openhour_removed",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''
if text.count(weak_open) != 1:
    raise SystemExit(
        f"Expected exactly one restored 04:00-05:59 block, found {text.count(weak_open)}"
    )
text = text.replace(weak_open, confirmed_liquidity, 1)

path.write_text(text, encoding="utf-8")
print("Applied frozen EMA9 reclaim tolerance and one new revision: remove weak server hour 04")
