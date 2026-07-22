from pathlib import Path
import re

# One strategy revision for this iteration:
# keep the existing closed-bar setup, but enter only after the next minute's
# real bid/ask stream breaks the signal candle by 0.05 ATR. This is a simple
# continuation confirmation, not a new indicator or date-specific rule.
engine_path = Path("xau_lab/real_tick_lab.py")
engine = engine_path.read_text(encoding="utf-8")

# This patch may run after an earlier research patch has already installed the
# same chronological confirmation logic. Treat that state as success instead
# of aborting the whole matrix. Only install the block when it is absent.
already_confirmed = 'sig_name + "_CONF"' in engine
if not already_confirmed:
    start_matches = list(re.finditer(
        r"(?m)^        spread = float\(minute_asks\[0\] - minute_bids\[0\]\)\s*$",
        engine,
    ))
    if len(start_matches) != 1:
        raise SystemExit(
            f"confirmation entry start found {len(start_matches)} times and no existing _CONF entry was detected"
        )
    start = start_matches[0].start()

    end_match = re.search(
        r"(?m)^        for k in range\(1, count\):\s*$",
        engine[start:],
    )
    if end_match is None:
        raise SystemExit("confirmation entry end loop not found")
    end = start + end_match.end()

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
        # Manage only ticks after the actual confirmation fill.
        for k in range(entry_tick + 1, count):'''

    engine = engine[:start] + replacement + engine[end:]
    if engine.count('sig_name + "_CONF"') != 1:
        raise SystemExit("confirmation patch integrity check failed")
    engine_path.write_text(engine, encoding="utf-8")
    print("Installed next-minute real-tick break confirmation")
else:
    print("Next-minute real-tick break confirmation already present; skipped duplicate installation")

# Rotate the untouched holdout after the prior result was observed. August and
# December 2025 were not used by the preceding selection run. Keep this update
# idempotent so rebuilds remain reproducible.
runner_path = Path("xau_lab/hf_window_runner.py")
runner = runner_path.read_text(encoding="utf-8")
windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2025_aug", "holdout", "2025-08-04", "2025-08-23"),
    ("hold_2025_dec", "holdout", "2025-12-01", "2025-12-20"),
]'''
runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not rotate to fresh Aug/Dec 2025 holdout")
runner_path.write_text(runner, encoding="utf-8")
print("Applied fresh Aug/Dec 2025 holdout protocol")
