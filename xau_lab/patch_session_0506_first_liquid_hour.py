from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, date-agnostic revision based only on development and validation.
# The one-hour 05:00-05:59 EET/EEST session produced too few observations to
# support a robust conclusion (only 13 dev+validation trades in the latest run).
# Keep signals, trend filters, stops, targets, risk, costs, validation windows
# and holdouts unchanged; widen only to the adjacent second liquid hour so the
# same London-open mechanism is sampled more often without adding indicators.
old = '''                name=c.name + "_s0509",
                baseline_hour_rules=False,
                session_start=5,
                session_end=9,
                blocked_hour=24,
'''
new = '''                name=c.name + "_s0507",
                baseline_hour_rules=False,
                session_start=5,
                session_end=7,
                blocked_hour=24,
'''

if text.count(old) != 1:
    raise SystemExit("expected one 05:00-09:00 candidate block")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Applied one session revision: trade 05:00-06:59 EET/EEST")
