from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

marker = "    return out\n\n\ndef in_session"
insert = '''    # One simple, economically defensible revision after the prior run was
    # too sparse (11 development trades, 2 validation trades): remove the
    # narrow clock-window dependency and let the existing trend, candle,
    # adaptive-spread, and risk filters decide across the liquid trading day.
    # Midnight server hour remains blocked to avoid rollover conditions.
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
    return out


def in_session'''

if marker not in text:
    raise SystemExit("candidate-list marker not found for global liquid-session revision")
text = text.replace(marker, insert, 1)
path.write_text(text, encoding="utf-8")
print("Applied one revision: global liquid-day cross/follow candidate with rollover blocked")
