from pathlib import Path

path = Path("xau_lab/real_tick_lab.py")
text = path.read_text(encoding="utf-8")

old = '''    return out


def in_session'''
new = '''    # Single economically defensible revision for this iteration:
    # disable the discretionary fail-fast exit. In the completed development
    # sample every FAIL_FAST exit was negative, so it only crystallized losses.
    # Regular broker-side SL, TP, break-even, trailing stop, cooldown, daily
    # loss limit and consecutive-loss protections remain unchanged.
    out = [
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

if old not in text:
    raise SystemExit("candidate return marker not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Disabled fail-fast exits for the next independent validation iteration")
