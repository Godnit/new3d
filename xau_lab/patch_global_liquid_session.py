from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

candidate = '''    # One simple, economically defensible revision after the prior run was
    # too sparse: remove the narrow clock-window dependency and let the
    # existing trend, candle, spread, and risk filters decide across the
    # liquid trading day. Midnight server hour remains blocked for rollover.
    out.append(
        replace(
            base,
            name="rev_global_liquid_cross_follow",
            baseline_hour_rules=False,
            session_start=1,
            session_end=23,
            blocked_hour=0,
            signal_mode="cross_follow",
            m15_mode="veto",
            stop_atr=1.25,
            rr=1.35,
            be_trigger=0.80,
            be_lock_atr=0.05,
            trail_start=1.20,
            trail_atr=0.80,
            fail_fast_minutes=4,
            fail_fast_max_mfe_r=0.30,
            fail_fast_current_r=-0.10,
        )
    )
'''

if 'name="rev_global_liquid_cross_follow"' in text:
    print("Global liquid-session candidate already present")
else:
    pattern = r"(?ms)^(?P<indent>    )return out\s*\n(?=\s*def in_session\b)"
    match = re.search(pattern, text)
    if not match:
        raise SystemExit("could not locate final candidate return before in_session")
    replacement = candidate + "    return out\n"
    text = text[:match.start()] + replacement + text[match.end():]
    path.write_text(text, encoding="utf-8")
    print("Applied global liquid-day cross/follow candidate with rollover blocked")
