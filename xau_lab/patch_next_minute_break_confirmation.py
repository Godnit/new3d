from pathlib import Path

# One simple, economically defensible strategy revision for this iteration:
# remove the delayed next-minute high/low-break confirmation and retain the
# already chronological, closed-bar entry implemented by the preceding engine
# patches. The completed real-tick run produced only 25 trades across ten
# independent windows and the development, validation, and holdout splits were
# all negative. Requiring an additional 0.05 ATR break after a fully closed M1
# signal added entry latency, reduced the sample, and often paid a worse spread
# and price after the move had already started. No indicator, date-specific
# rule, risk increase, or holdout-derived parameter is introduced here.
#
# The workflow keeps invoking this file so every run has an explicit audit
# record of the revision, but this patch intentionally leaves the engine
# unchanged.
path = Path("xau_lab/real_tick_lab.py")
if not path.exists():
    raise SystemExit("real_tick_lab.py is missing")

text = path.read_text(encoding="utf-8")
if 'sig_name + "_CONF"' in text or "entry_tick + 1" in text:
    raise SystemExit(
        "Delayed confirmation logic is already present before this no-op patch; "
        "the engine rebuild order must be corrected rather than silently accepted."
    )

print("Revision applied: use chronological closed-bar entry without delayed next-minute break confirmation")
