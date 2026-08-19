from pathlib import Path
import re

engine = Path("xau_lab/real_tick_lab.py")
text = engine.read_text(encoding="utf-8")

appendix = r'''

# Final clean protocol for this iteration: compare the frozen v5.60 reference
# against one economically defensible revision only. The revision is sell-side
# continuation after a pullback, restricted by a strict M15 bearish trend.
# No calendar-date or individual-window rule is introduced.
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

if "_PROTOCOL_WANTED" in text:
    raise SystemExit("clean protocol already present")
engine.write_text(text + appendix, encoding="utf-8")

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
print("Applied clean two-candidate monthly protocol with fresh 2020 holdout")
