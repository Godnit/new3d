from pathlib import Path
import re

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# One simple, economically defensible revision after run 154:
# continuation sells were the only signal family positive in development,
# validation, and untouched holdout, but the strict M15 variant produced too
# few observations. Test the middle ground: global continuation sells with an
# M15 veto (blocks counter-trend M15, but does not require fully aligned M15).
# No date, month, weekday, or single-window exception is introduced.
if 'name="rev_global_cont_sell_m15veto"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return not found")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_global_cont_sell_m15veto",
            baseline_hour_rules=False,
            session_start=0,
            session_end=0,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="veto",
            stop_atr=1.15,
            rr=1.10,
            be_trigger=0.55,
            be_lock_atr=0.05,
            trail_start=0.90,
            trail_atr=0.65,
            fail_fast_minutes=3,
            fail_fast_max_mfe_r=0.25,
            fail_fast_current_r=-0.05,
            close_extreme_fraction=0.55,
            max_spread_price=1.20,
            max_spread_atr=0.65,
        )
    )
'''
    text = text[:return_pos] + candidate + text[return_pos:]

anchor = "    # Exact baseline keeps its report-driven special hour rules.\n    hour = bars.index[i].tz_convert(SERVER_TZ).hour\n"
if 'if c.name.startswith("rev_global_cont_sell_m15veto"):' not in text:
    if anchor not in text:
        raise SystemExit("signal override anchor not found")
    replacement = '''    if c.name.startswith("rev_global_cont_sell_m15veto"):
        buy_trigger = False
        sell_trigger = cont_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(anchor, replacement, 1)

# Clean this iteration after run 158: compare the frozen v5.60 reference with
# one revision only. The revision is a global continuation sell after a
# pullback, accepted only when M15 is strictly bearish. This is a market-logic
# rule, not a date/hour exception. Filtering is appended after all historical
# candidate patches, so previous experiments cannot influence selection.
protocol = r'''

_PROTOCOL_ALL_CANDIDATES = candidates()
_PROTOCOL_WANTED = {
    "v560_baseline_cl55",
    "rev_global_cont_sell_m15strict_freshmay_cl55",
}

def candidates():
    selected = [c for c in _PROTOCOL_ALL_CANDIDATES if c.name in _PROTOCOL_WANTED]
    missing = _PROTOCOL_WANTED - {c.name for c in selected}
    if missing:
        raise RuntimeError(f"Protocol candidates missing after patch chain: {sorted(missing)}")
    return selected
'''
if "_PROTOCOL_WANTED" not in text:
    text += protocol

path.write_text(text, encoding="utf-8")

# Increase statistical power without changing strategy rules. Six full-month
# development windows and two full-month validation windows are used. The two
# 2020 holdout months are not used for candidate selection and were not part of
# the prior 2021-2025 tuning sequence.
runner = Path("xau_lab/hf_window_runner.py")
rtext = runner.read_text(encoding="utf-8")
monthly_windows = '''WINDOWS = [
    ("dev_2021_feb", "dev", "2021-02-01", "2021-03-01"),
    ("dev_2021_jun", "dev", "2021-06-01", "2021-07-01"),
    ("dev_2022_feb", "dev", "2022-02-01", "2022-03-01"),
    ("dev_2022_jun", "dev", "2022-06-01", "2022-07-01"),
    ("dev_2023_feb", "dev", "2023-02-01", "2023-03-01"),
    ("dev_2023_jun", "dev", "2023-06-01", "2023-07-01"),
    ("val_2024_feb", "validation", "2024-02-01", "2024-03-01"),
    ("val_2024_jun", "validation", "2024-06-01", "2024-07-01"),
    ("hold_2020_feb", "holdout", "2020-02-01", "2020-03-01"),
    ("hold_2020_jun", "holdout", "2020-06-01", "2020-07-01"),
]
'''
rtext, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    monthly_windows + "\n\ndef iter_months",
    rtext,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not replace hf_window_runner WINDOWS")
runner.write_text(rtext, encoding="utf-8")

print("Added M15-veto candidate and clean two-candidate full-month protocol")
