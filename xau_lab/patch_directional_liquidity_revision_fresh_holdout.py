from pathlib import Path
import re

# One simple strategy revision based only on development + validation trades:
# during the early European liquidity build-up, allow long crosses in server
# hours 04-05 and short crosses in hour 06. This removes the direction/hour
# combinations that were negative in both non-holdout splits while retaining
# 36 of 62 observed dev+validation trades. Signals, trend filters, stops,
# targets, risk, spread and adverse-slippage assumptions remain unchanged.
engine_path = Path("xau_lab/real_tick_lab.py")
text = engine_path.read_text(encoding="utf-8")
pattern = r"def direction_allowed\(direction: int, hour: int, c: Candidate\) -> bool:\n.*?\n\ndef floor_volume"
replacement = '''def direction_allowed(direction: int, hour: int, c: Candidate) -> bool:
    if c.baseline_hour_rules:
        if hour == 3:
            return True
        if hour in (5, 7):
            return direction < 0
        if hour == 6:
            return direction > 0
        return False

    # Directional liquidity hand-off rule: long pullback resumptions during
    # hours 04-05, then short resumptions in hour 06. All existing closed-bar
    # trend, body, distance and execution-cost checks still apply.
    if direction > 0:
        return hour in (4, 5)
    return hour == 6


def floor_volume'''
text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f"Expected one direction_allowed function, replaced {count}")

# Rename the active research candidate so results cannot be confused with the
# prior symmetric 04-06 attempt.
text = text.replace('name=c.name + "_early0406"', 'name=c.name + "_dirL45S6"')
engine_path.write_text(text, encoding="utf-8")

# Protocol-only holdout rotation. The February/May 2026 gates are now observed
# and retired. Use two previously sealed, non-overlapping pre-2025 windows.
# No date appears in trading logic.
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
    ("hold_2021_may_blind", "holdout", "2021-05-24", "2021-06-05"),
    ("hold_2022_dec_blind", "holdout", "2022-12-05", "2022-12-24"),
]'''
runner, count = re.subn(r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months", windows + "\n\n\ndef iter_months", runner, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not install fresh May-2021/December-2022 holdout protocol")
runner_path.write_text(runner, encoding="utf-8")

print("Applied one revision: buy hours 04-05, sell hour 06; rotated to fresh blind holdout")
