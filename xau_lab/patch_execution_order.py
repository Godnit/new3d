from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old_start = '''        # Manage an existing position through every real bid/ask tick.
        tick_offset_start = 0
        if pos is not None:
'''
new_start = '''        # Manage an existing position through every real bid/ask tick.
        # Never re-enter at the first tick of a minute after learning that an
        # older position closes later inside that same minute.
        had_position_at_minute_start = pos is not None
        tick_offset_start = 0
        if had_position_at_minute_start:
'''
if old_start in text:
    text = text.replace(old_start, new_start, 1)
elif "had_position_at_minute_start = pos is not None" not in text:
    raise SystemExit("position-start patch marker not found")

old_end = '''            # If still open, cannot enter another position this minute.
            if pos is not None:
                continue

        # Entry checks only inside the evaluation interval.
'''
new_end = '''            # A position existed at this minute's first tick. Even if it
            # closed later in the minute, the first-tick entry opportunity has
            # already passed, so skip all entries for this minute.
            continue

        # Entry checks only inside the evaluation interval.
'''
if old_end in text:
    text = text.replace(old_end, new_end, 1)
elif "the first-tick entry opportunity has" not in text:
    raise SystemExit("position-end patch marker not found")

# Replace every remaining current, still-forming M1 EMA reference in position
# management. The exact count may change as the engine evolves; requiring a
# hard-coded count made the CI patch brittle without improving safety.
current_ref = "float(row.ema21)"
closed_ref = "float(bars.iloc[i - 1].ema21)"
replacements = text.count(current_ref)
if replacements:
    text = text.replace(current_ref, closed_ref)
elif closed_ref not in text:
    raise SystemExit("no EMA management reference found to validate")

path.write_text(text, encoding="utf-8")
print(f"Patched chronological execution; closed-bar EMA replacements={replacements}")
