from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible strategy revision for this iteration:
# keep the closed-bar signal logic unchanged, but require the next minute's
# real bid/ask stream to confirm continuation by breaking the signal candle's
# high/low by 0.05 ATR before entering. This avoids entering the first quote
# after a signal that immediately fails. It adds no indicator, date rule, or
# holdout-specific parameter.
#
# This patch deliberately uses stable start/end anchors instead of one large
# regular expression. Earlier execution-quality patches legitimately changed
# the formatting of the entry block, which made the old regex brittle.
if 'sig_name + "_CONF"' in text and "entry_tick + 1" in text:
    print("Next-minute break confirmation already applied")
    raise SystemExit(0)

start_marker = "        spread = first_ask - first_bid\n"
if start_marker not in text:
    # Compatibility with a clean engine when entry freshness is not present.
    start_marker = "        spread = float(minute_asks[0] - minute_bids[0])\n"

end_marker = "        for k in range(1, count):"
start_count = text.count(start_marker)
end_count = text.count(end_marker)
if start_count != 1 or end_count != 1:
    raise SystemExit(
        f"expected one confirmation entry block; start={start_count}, end={end_count}"
    )

start = text.index(start_marker)
end = text.index(end_marker, start) + len(end_marker)

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

text = text[:start] + replacement + text[end:]
path.write_text(text, encoding="utf-8")
print("Applied robust next-minute high/low break confirmation entry")
