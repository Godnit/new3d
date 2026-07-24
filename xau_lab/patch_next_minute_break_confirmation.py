from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible strategy revision for this iteration:
# keep the closed-bar signal logic unchanged, but require the next minute's
# real bid/ask stream to confirm continuation by breaking the signal candle's
# high/low by 0.05 ATR before entering. This avoids buying/selling the first
# quote of a minute after a signal that immediately fails, without introducing
# a new indicator, date rule, or holdout-specific parameter.
#
# The entry-freshness patch may already have normalized the first quote into
# first_ask/first_bid. Match either form so this patch remains idempotent and
# does not fail merely because a preceding execution-quality patch changed one
# assignment line.
pattern = re.compile(
    r'''        spread = (?:float\(minute_asks\[0\] - minute_bids\[0\]\)|first_ask - first_bid)\n'''
    r'''        if spread > c\.max_spread_price or \(atr > 0 and spread / atr > c\.max_spread_atr\):\n'''
    r'''            continue\n'''
    r'''        entry = .*?\n'''
    r'''        stop_distance = .*?\n'''
    r'''        sl = .*?\n'''
    r'''        rr = c\.rr\n'''
    r'''        if c\.baseline_hour_rules:\n'''
    r'''            rr = .*?\n'''
    r'''        tp = .*?\n'''
    r'''        vol = risk_volume\(balance, entry, sl, c\)\n'''
    r'''        if vol <= 0:\n'''
    r'''            continue\n'''
    r'''        pos = Position\(direction, sig_name, t, entry, sl, tp, vol, stop_distance, entry, rr\)\n'''
    r'''        last_entry = t\n'''
    r'''        trades_today \+= 1\n'''
    r'''        # Manage after the entry tick, using the remaining real ticks of that minute\.\n'''
    r'''        for k in range\(1, count\):''',
    re.S,
)

replacement = '''        signal_bar = bars.iloc[i - 1]
        confirmation_buffer = atr * 0.05
        trigger_price = (
            float(signal_bar.high) + confirmation_buffer
            if direction > 0
            else float(signal_bar.low) - confirmation_buffer
        )
        entry_tick = None
        for probe in range(count):
            if direction > 0 and float(minute_asks[probe]) >= trigger_price:
                entry_tick = probe
                break
            if direction < 0 and float(minute_bids[probe]) <= trigger_price:
                entry_tick = probe
                break
        if entry_tick is None:
            continue

        spread = float(minute_asks[entry_tick] - minute_bids[entry_tick])
        if spread > c.max_spread_price or (atr > 0 and spread / atr > c.max_spread_atr):
            continue
        entry_time = pd.Timestamp(minute_times[entry_tick], tz="UTC")
        entry = (
            float(minute_asks[entry_tick] + c.slippage_price)
            if direction > 0
            else float(minute_bids[entry_tick] - c.slippage_price)
        )
        stop_distance = max(atr * c.stop_atr, spread * 3.0, 0.03)
        sl = entry - stop_distance if direction > 0 else entry + stop_distance
        rr = c.rr
        if c.baseline_hour_rules:
            rr = {3: 1.80, 5: 1.15, 6: 1.10, 7: 1.00}.get(hour, 1.20)
        tp = entry + stop_distance * rr if direction > 0 else entry - stop_distance * rr
        vol = risk_volume(balance, entry, sl, c)
        if vol <= 0:
            continue
        pos = Position(direction, sig_name + "_CONF", entry_time, entry, sl, tp, vol, stop_distance, entry, rr)
        last_entry = entry_time
        trades_today += 1
        # Manage only ticks that occur after the actual confirmation entry.
        for k in range(entry_tick + 1, count):'''

text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    if 'sig_name + "_CONF"' in text and "entry_tick + 1" in text:
        print("Next-minute break confirmation already applied")
    else:
        raise SystemExit(f"expected one entry block for confirmation patch, found {count}")
else:
    path.write_text(text, encoding="utf-8")
    print("Applied next-minute high/low break confirmation entry")
