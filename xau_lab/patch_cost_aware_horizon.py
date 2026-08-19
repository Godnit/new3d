from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One economically motivated revision after the prior family failed across
# development and validation: transaction costs consume most of an M1 ATR on
# this independent feed. Keep the entry logic unchanged, but require a better
# spread/volatility regime and give trades a wider, slower horizon. The frozen
# v5.60 baseline remains untouched; only research candidates are transformed.
needle = "    return out\n\n\ndef in_session"
replacement = '''    revised = [out[0]]
    for c in out[1:]:
        revised.append(
            replace(
                c,
                name=c.name + "_costaware",
                stop_atr=max(c.stop_atr, 2.50),
                rr=1.00,
                be_trigger=0.70,
                be_lock_atr=0.05,
                trail_start=1.00,
                trail_atr=1.10,
                max_spread_price=999.0,
                max_spread_atr=0.65,
                fail_fast_minutes=100000,
                fail_fast_max_mfe_r=-999.0,
                fail_fast_current_r=-999.0,
            )
        )
    return revised


def in_session'''
if text.count(needle) != 1:
    raise SystemExit("candidate return marker not found exactly once")
text = text.replace(needle, replacement, 1)

old_stop = "stop_dist = max(atr * c.stop_atr, spread * 3.0, 0.03)"
new_stop = "stop_dist = max(atr * c.stop_atr, spread * 5.0, 0.03)"
if text.count(old_stop) != 1:
    raise SystemExit("stop-distance marker not found exactly once")
text = text.replace(old_stop, new_stop, 1)

path.write_text(text, encoding="utf-8")
print("Applied one cost-aware wider-horizon revision to research candidates")
