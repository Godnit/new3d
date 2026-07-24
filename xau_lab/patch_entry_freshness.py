from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''        direction, sig_name, atr = signal_at(bars, i, c)
        if direction == 0 or not direction_allowed(direction, hour, c):
            continue
        spread = float(minute_asks[0] - minute_bids[0])
'''
new = '''        direction, sig_name, atr = signal_at(bars, i, c)
        if direction == 0 or not direction_allowed(direction, hour, c):
            continue

        # One simple execution-quality revision: confirm that the signal is
        # still fresh at the actual first tradable tick of the next minute.
        # This prevents a closed-bar crossover from being executed after an
        # immediate gap/reversal has already invalidated it.
        signal_bar = bars.iloc[i - 1]
        first_ask = float(minute_asks[0])
        first_bid = float(minute_bids[0])
        freshness_buffer = atr * 0.15
        if direction > 0:
            if first_bid <= float(signal_bar.ema9) or first_bid < float(signal_bar.close) - freshness_buffer:
                continue
        else:
            if first_ask >= float(signal_bar.ema9) or first_ask > float(signal_bar.close) + freshness_buffer:
                continue

        spread = first_ask - first_bid
'''
if old not in text:
    raise SystemExit("entry freshness patch marker not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Patched next-minute entry freshness confirmation")
