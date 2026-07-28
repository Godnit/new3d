from pathlib import Path

# One simple, economically defensible strategy revision for this iteration:
# require a 1.50R profit target for every candidate instead of permitting the
# selected 1.00R profile. The completed independent run had a 41.94% hit rate
# and roughly symmetric average wins/losses, so a 1:1 payoff cannot overcome
# spread and adverse slippage. This changes no dates, sessions, indicators,
# entry frequency, risk percentage, or holdout periods.
path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

needle = "    return out\n\n\ndef in_session"
replacement = (
    "    out = [replace(c, name=c.name + '_rr150', rr=1.50) for c in out]\n"
    "    return out\n\n\ndef in_session"
)

if needle not in text:
    raise SystemExit("candidate return marker not found; refusing an ambiguous patch")
if "'_rr150'" in text or '"_rr150"' in text:
    raise SystemExit("asymmetric payoff revision is already present")

text = text.replace(needle, replacement, 1)
path.write_text(text, encoding="utf-8")
print("Revision applied: use a uniform 1.50R target while preserving entries and risk")
