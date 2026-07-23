from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One strategy revision based only on development + 2024 validation from run 113:
# sell-side continuation/follow resumption was the only family positive in both
# splits, but the 0.55 close-location requirement left too few validation trades.
# Relax only that candle-close threshold to 0.45. Keep direction, signals,
# trend, spread, risk, cooldown, stops and execution stress unchanged.
if 'name="rev_global_sell_cont_follow_cl45"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return not found")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_global_sell_cont_follow_cl45",
            baseline_hour_rules=False,
            session_start=0,
            session_end=0,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="off",
            stop_atr=1.15,
            rr=1.10,
            be_trigger=0.55,
            be_lock_atr=0.05,
            trail_start=0.90,
            trail_atr=0.65,
            fail_fast_minutes=3,
            fail_fast_max_mfe_r=0.25,
            fail_fast_current_r=-0.05,
            close_extreme_fraction=0.45,
            max_spread_price=1.20,
            max_spread_atr=0.65,
        )
    )
'''
    text = text[:return_pos] + candidate + text[return_pos:]

anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'if c.name == "rev_global_sell_cont_follow_cl45":' not in text:
    if anchor not in text:
        raise SystemExit("signal anchor not found")
    insert = '''    if c.name == "rev_global_sell_cont_follow_cl45":
        buy_trigger = False
        sell_trigger = cont_sell or follow_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(anchor, insert, 1)

# The Feb/Mar 2025 holdout was opened in run 113 and is no longer untouched.
# Rotate only the holdout to two previously unused May 2025 weeks; development
# and 2024 validation remain frozen.
windows_match = re.search(r"WINDOWS\s*=\s*\[(.*?)\n\]", text, flags=re.S)
if not windows_match:
    raise SystemExit("WINDOWS list not found")
block = windows_match.group(0)
lines = block.splitlines()
kept = [line for line in lines if '"holdout"' not in line]
if kept[-1].strip() == "]":
    kept = kept[:-1]
kept.extend([
    '    ("hold_2025_may_a", "holdout", "2025-05-05", "2025-05-10"),',
    '    ("hold_2025_may_b", "holdout", "2025-05-19", "2025-05-24"),',
    ']'
])
text = text[:windows_match.start()] + "\n".join(kept) + text[windows_match.end():]

# Update report wording so the audit trail identifies the new blind holdout.
text = text.replace(
    "newly untouched February/March 2025 holdout",
    "newly untouched May 2025 holdout",
)

path.write_text(text, encoding="utf-8")
print("Added one close-location revision (0.55 -> 0.45) and rotated blind holdout to May 2025")
