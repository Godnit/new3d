from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, non-date-specific revision based on the development split only.
# In the latest cost-aware run, development trades opened during recurring
# server hours 04 and 05 were profitable in aggregate, while hours 06 and 07
# were negative. Keep every signal, trend, stop, target, risk and execution-cost
# assumption unchanged; only narrow the entry window to 04:00-05:59 EET/EEST.
# Validation and holdout windows are not used to define this revision.
needle = "    return revised\n\n\ndef in_session"
replacement = '''    focused = [revised[0]]
    for c in revised[1:]:
        focused.append(
            replace(
                c,
                name=c.name + "_s0406",
                baseline_hour_rules=False,
                session_start=4,
                session_end=6,
                blocked_hour=24,
            )
        )
    return focused


def in_session'''

if text.count(needle) != 1:
    raise SystemExit("cost-aware candidate return marker not found exactly once")
text = text.replace(needle, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Applied one development-only 04:00-06:00 server-session revision")
