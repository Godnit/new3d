from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

# Previous revision retained: remove the extra M15 EMA20 slope gate while
# keeping the M15 trend veto, M5 trend filter, local EMA alignment, closed-bar
# EMA9 cross, spread filter, and all risk controls.
for line in (
    "        and m15_slope_up\n",
    "        and m15_slope_down\n",
):
    if text.count(line) != 1:
        raise SystemExit(f"Expected exactly one slope condition: {line.strip()}")
    text = text.replace(line, "", 1)

# Single new economically defensible revision for this iteration: disable the
# discretionary fail-fast exit. In run 231, every FAIL_FAST exit in development
# was negative (231 exits, -258.48 USD across the candidate grid), so this rule
# only crystallized losses. Broker-side SL/TP, break-even, trailing stop,
# cooldown, consecutive-loss pause and daily-loss protection remain active.
marker = "    return out\n\n\ndef in_session"
replacement = '''    out = [
        replace(
            candidate,
            name=candidate.name + "_nofail",
            fail_fast_minutes=100000,
            fail_fast_max_mfe_r=-999.0,
            fail_fast_current_r=-999.0,
        )
        for candidate in out
    ]
    return out


def in_session'''
if text.count(marker) != 1:
    raise SystemExit("Expected exactly one candidate return marker")
text = text.replace(marker, replacement, 1)

path.write_text(text, encoding="utf-8")
print("Removed M15 slope gate and disabled consistently losing fail-fast exit")
