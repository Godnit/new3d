from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''    profiles = [
        # name, stop, rr, be, trail_start, trail_atr, fail_m, max_mfe, current_r
        ("hit", 1.15, 1.10, 0.55, 0.90, 0.65, 3, 0.25, -0.05),
        ("bal", 1.25, 1.35, 0.80, 1.20, 0.80, 4, 0.30, -0.10),
    ]
'''
new = '''    profiles = [
        # name, stop, rr, be, trail_start, trail_atr, fail_m, max_mfe, current_r
        ("hit", 1.15, 1.10, 0.55, 0.90, 0.65, 3, 0.25, -0.05),
        ("bal", 1.25, 1.35, 0.80, 1.20, 0.80, 4, 0.30, -0.10),
        # One economically motivated revision for noisy XAUUSD M1 execution:
        # a wider volatility stop, smaller 1R target, later break-even/trailing,
        # and slower fail-fast exit. Position sizing still targets the same
        # account risk, so this changes noise tolerance rather than risk budget.
        ("wide", 1.80, 1.00, 0.90, 1.15, 1.00, 6, 0.40, -0.15),
    ]
'''
if old not in text:
    raise SystemExit("profiles block not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Added one wide-noise execution profile")
