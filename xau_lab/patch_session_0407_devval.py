from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, non-date-specific strategy revision based only on development and
# validation trades from the failed cost-aware run. Across those eight windows,
# server hours 04, 05 and 06 were approximately flat-to-positive, while hours
# 00-03 and 07 accounted for nearly all losses. Keep signals, trend filters,
# stops, targets, risk and execution stress unchanged; only concentrate entries
# in the recurring 04:00-06:59 EET/EEST liquidity window.
needle = "    return revised\n\n\ndef in_session"
replacement = '''    focused = [revised[0]]
    for c in revised[1:]:
        focused.append(
            replace(
                c,
                name=c.name + "_s0407",
                baseline_hour_rules=False,
                session_start=4,
                session_end=7,
                blocked_hour=24,
            )
        )
    return focused


def in_session'''

if text.count(needle) != 1:
    raise SystemExit("cost-aware candidate return marker not found exactly once")
text = text.replace(needle, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Applied one development/validation-only 04:00-07:00 server-session revision")
