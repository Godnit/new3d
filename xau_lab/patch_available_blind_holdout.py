from pathlib import Path
import re

# Protocol repair only; no strategy parameter, signal, execution or risk logic
# is changed here. The June 2022 and June 2024 periods have now been observed
# in run 132 and are retired from holdout use. Seal two previously unused,
# non-overlapping August periods before the new close-location revision runs.
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
    ("hold_2022_aug_blind", "holdout", "2022-08-08", "2022-08-27"),
    ("hold_2024_aug_blind", "holdout", "2024-08-05", "2024-08-24"),
]'''

runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not install fresh August blind holdout protocol")
runner_path.write_text(runner, encoding="utf-8")
print("Installed fresh untouched holdouts: August 2022 and August 2024")

# Run exactly one new strategy revision after all legacy patches. It changes
# only candle close-location tolerance for the already identified strict M15
# sell-resumption family; the newly sealed holdout periods are never consulted
# by this patch.
revision = Path("xau_lab/patch_strict_sell_resumption_close65_fresh_aug_holdout.py")
namespace = {"__name__": "__main__", "__file__": str(revision)}
exec(compile(revision.read_text(encoding="utf-8"), str(revision), "exec"), namespace)
