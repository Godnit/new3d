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

# One simple, date-agnostic revision for the new iteration. The final 05:00-only
# candidate produced just 16 development+validation trades. Earlier development-
# only hour attribution found recurring server hours 04 and 05 profitable in
# aggregate, while 06 and 07 were negative. Restore 04:00-05:59 to increase the
# independent sample without changing direction, signals, trend filters, stops,
# targets, risk, execution costs, validation windows, or untouched holdouts.
old_session = '''                name=c.name + "_s0506",
                baseline_hour_rules=False,
                session_start=5,
                session_end=6,
                blocked_hour=24,
'''
new_session = '''                name=c.name + "_s0406_sparsefix",
                baseline_hour_rules=False,
                session_start=4,
                session_end=6,
                blocked_hour=24,
'''
if text.count(old_session) != 1:
    raise SystemExit(
        f"Expected exactly one final 05:00-only candidate block, found {text.count(old_session)}"
    )
text = text.replace(old_session, new_session, 1)

path.write_text(text, encoding="utf-8")
print("Applied frozen EMA9 reclaim tolerance and one new 04:00-05:59 session revision")
