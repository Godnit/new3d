from pathlib import Path
import re

lab_path = Path("xau_lab/real_tick_lab.py")
text = lab_path.read_text(encoding="utf-8")

# Exactly one economically defensible strategy revision for this iteration:
# bearish continuation entries only, available across the full trading day,
# but accepted only when the closed M15 trend is also bearish. This combines
# the only signal family that was positive in development+validation with a
# higher-timeframe confirmation, without adding a date, weekday, or news rule.
name = "rev_global_cont_sell_m15strict_freshmay"
if f'name="{name}"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return boundary not found")
    candidate = f'''    out.append(
        replace(
            base,
            name="{name}",
            baseline_hour_rules=False,
            session_start=0,
            session_end=0,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="strict",
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
rule = f'c.name.startswith("{name}")'
if rule not in text:
    if anchor not in text:
        raise SystemExit("signal anchor not found")
    replacement = f'''    if {rule}:
        buy_trigger = False
        sell_trigger = cont_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(anchor, replacement, 1)

# Predeclare this one revision before opening a fresh holdout. Selection is
# based only on development and 2024 validation; the May 2022/2024 holdout is
# used solely for the final acceptance gate.
choose_start = text.find("def choose_candidate(")
main_start = text.find("\ndef main()", choose_start)
if choose_start < 0 or main_start < 0:
    raise SystemExit("choose_candidate boundaries not found")
new_choose = f'''def choose_candidate(all_rows: pd.DataFrame) -> tuple[str, dict[str, pd.DataFrame], bool, str]:
    dev = aggregate(all_rows, "dev")
    val = aggregate(all_rows, "validation")
    hold = aggregate(all_rows, "holdout")
    selected = "{name}"

    dev_row = dev[dev["candidate"] == selected]
    val_row = val[val["candidate"] == selected]
    hold_row = hold[hold["candidate"] == selected]
    if dev_row.empty or val_row.empty or hold_row.empty:
        fallback = "v560_baseline_cl55"
        selected = fallback if fallback in set(dev["candidate"]) else str(dev.iloc[0]["candidate"])
        return selected, {{"dev": dev, "validation": val, "holdout": hold, "top": dev, "shortlist": val}}, False, "Predeclared continuation candidate was not produced; diagnostic fallback only."

    d = dev_row.iloc[0]
    v = val_row.iloc[0]
    h = hold_row.iloc[0]
    pre_holdout_ok = bool(
        d.net_profit > 0
        and d.profit_factor >= 1.20
        and d.trades >= 12
        and d.positive_window_ratio >= 0.50
        and v.net_profit > 0
        and v.profit_factor >= 1.10
        and v.trades >= 4
        and v.positive_window_ratio >= 0.50
    )

    selected_rows = all_rows[all_rows["candidate"] == selected]
    gp = selected_rows.gross_profit.sum()
    gl = selected_rows.gross_loss.sum()
    combined_pf = gp / abs(gl) if gl < 0 else (999.0 if gp > 0 else 0.0)
    combined_trades = int(selected_rows.trades.sum())
    combined_wins = int(selected_rows.wins.sum())
    combined_wr = combined_wins / combined_trades * 100.0 if combined_trades else 0.0

    success = bool(
        pre_holdout_ok
        and h.net_profit > 0
        and h.profit_factor >= 1.10
        and h.trades >= 4
        and h.positive_window_ratio >= 0.50
        and combined_pf >= 1.20
        and combined_trades >= 24
        and combined_wr >= 45.0
        and max(float(d.max_drawdown_pct), float(v.max_drawdown_pct), float(h.max_drawdown_pct)) < 10.0
    )
    reason = (
        "Predeclared global continuation-sell candidate passed development and validation before the fresh May holdout was inspected."
        if pre_holdout_ok
        else "The single continuation-sell revision failed its development/validation gate before holdout acceptance."
    )
    return selected, {{"dev": dev, "validation": val, "holdout": hold, "top": dev_row, "shortlist": val_row}}, success, reason
'''
text = text[:choose_start] + new_choose + text[main_start:]
lab_path.write_text(text, encoding="utf-8")

# Fresh holdout months not used by the prior selection cycles. Development and
# validation remain unchanged, while each holdout spans most of May.
runner_path = Path("xau_lab/hf_window_runner.py")
runner = runner_path.read_text(encoding="utf-8")
windows = '''WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-01", "2021-07-01"),
    ("dev_2021_oct", "dev", "2021-10-01", "2021-11-01"),
    ("dev_2022_mar", "dev", "2022-03-01", "2022-04-01"),
    ("dev_2022_sep", "dev", "2022-09-01", "2022-10-01"),
    ("dev_2023_mar", "dev", "2023-03-01", "2023-04-01"),
    ("dev_2023_oct", "dev", "2023-10-01", "2023-11-01"),
    ("val_2024_mar", "validation", "2024-03-01", "2024-04-01"),
    ("val_2024_oct", "validation", "2024-10-01", "2024-11-01"),
    ("hold_2022_may_blind", "holdout", "2022-05-01", "2022-05-28"),
    ("hold_2024_may_blind", "holdout", "2024-05-01", "2024-05-28"),
]'''
runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not install fresh May holdout protocol")
runner_path.write_text(runner, encoding="utf-8")

aggregate_path = Path("xau_lab/aggregate_results.py")
aggregate = aggregate_path.read_text(encoding="utf-8")
aggregate = re.sub(
    r"The candidate is considered acceptable only when .*? holdout gate passes\.",
    "The candidate is considered acceptable only when the newly untouched May 2022/2024 holdout gate passes.",
    aggregate,
)
aggregate_path.write_text(aggregate, encoding="utf-8")
print("Added one global continuation-sell M15-strict revision with fresh May holdouts")
