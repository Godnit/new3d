from pathlib import Path
import re

lab_path = Path("xau_lab/real_tick_lab.py")
text = lab_path.read_text(encoding="utf-8")

# One simple economically defensible strategy revision for this iteration:
# keep only bearish continuation/follow-through entries, trade across all hours,
# and retain the existing M5 trend, spread, ATR, execution-stress and risk rules.
# No month, weekday, news or holdout-specific trading rule is introduced.
if 'name="rev_focused_sell_resumption_decblind"' not in text:
    boundary = text.find("\ndef in_session")
    if boundary < 0:
        raise SystemExit("in_session boundary not found")
    return_pos = text.rfind("    return out", 0, boundary)
    if return_pos < 0:
        raise SystemExit("candidate return boundary not found")
    candidate = '''    out.append(
        replace(
            base,
            name="rev_focused_sell_resumption_decblind",
            baseline_hour_rules=False,
            session_start=0,
            session_end=0,
            blocked_hour=24,
            signal_mode="all",
            m15_mode="off",
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
if 'c.name.startswith("rev_focused_sell_resumption_decblind")' not in text:
    if anchor not in text:
        raise SystemExit("signal anchor not found")
    replacement = '''    if c.name.startswith("rev_focused_sell_resumption_decblind"):
        buy_trigger = False
        sell_trigger = cont_sell or follow_sell

    # Exact baseline keeps its report-driven special hour rules.
    hour = bars.index[i].tz_convert(SERVER_TZ).hour
'''
    text = text.replace(anchor, replacement, 1)

# Freeze candidate selection before touching the fresh holdout. This protocol
# evaluates exactly the single revision above against development and validation;
# holdout metrics are used only for the final gate.
choose_start = text.find("def choose_candidate(")
main_start = text.find("\ndef main()", choose_start)
if choose_start < 0 or main_start < 0:
    raise SystemExit("choose_candidate boundaries not found")
new_choose = '''def choose_candidate(all_rows: pd.DataFrame) -> tuple[str, dict[str, pd.DataFrame], bool, str]:
    dev = aggregate(all_rows, "dev")
    val = aggregate(all_rows, "validation")
    hold = aggregate(all_rows, "holdout")
    selected = "rev_focused_sell_resumption_decblind_cl55"

    dev_row = dev[dev["candidate"] == selected]
    val_row = val[val["candidate"] == selected]
    hold_row = hold[hold["candidate"] == selected]
    if dev_row.empty or val_row.empty or hold_row.empty:
        fallback = "v560_baseline_cl55"
        selected = fallback if fallback in set(dev["candidate"]) else str(dev.iloc[0]["candidate"])
        return selected, {"dev": dev, "validation": val, "holdout": hold, "top": dev, "shortlist": val}, False, "Focused revision was not produced; diagnostic fallback only."

    d = dev_row.iloc[0]
    v = val_row.iloc[0]
    h = hold_row.iloc[0]
    pre_holdout_ok = bool(
        d.net_profit > 0
        and d.profit_factor >= 1.25
        and d.trades >= 20
        and d.positive_window_ratio >= 0.50
        and v.net_profit > 0
        and v.profit_factor >= 1.15
        and v.trades >= 6
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
        and h.profit_factor >= 1.15
        and h.trades >= 8
        and h.positive_window_ratio >= 0.50
        and combined_pf >= 1.25
        and combined_trades >= 40
        and combined_wr >= 45.0
        and max(float(d.max_drawdown_pct), float(v.max_drawdown_pct), float(h.max_drawdown_pct)) < 10.0
    )
    reason = (
        "Single predeclared global sell continuation/follow revision; development and validation gates were checked before the fresh December holdout."
        if pre_holdout_ok
        else "The single focused revision failed the development/validation gate before holdout acceptance."
    )
    return selected, {"dev": dev, "validation": val, "holdout": hold, "top": dev_row, "shortlist": val_row}, success, reason
'''
text = text[:choose_start] + new_choose + text[main_start:]
lab_path.write_text(text, encoding="utf-8")

# Expand each independent sample to roughly four weeks for a meaningful trade
# count. The December 2022/2024 holdouts were not used in prior candidate
# selection and are sealed here before this revision is run.
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
    ("hold_2022_dec_blind", "holdout", "2022-12-01", "2022-12-23"),
    ("hold_2024_dec_blind", "holdout", "2024-12-01", "2024-12-23"),
]'''
runner, count = re.subn(
    r"WINDOWS\s*=\s*\[.*?\]\n\n\ndef iter_months",
    windows + "\n\n\ndef iter_months",
    runner,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("could not install fresh December holdout protocol")
runner_path.write_text(runner, encoding="utf-8")

aggregate_path = Path("xau_lab/aggregate_results.py")
aggregate = aggregate_path.read_text(encoding="utf-8")
aggregate = re.sub(
    r"The candidate is considered acceptable only when .*? holdout gate passes\.",
    "The candidate is considered acceptable only when the newly untouched December 2022/2024 holdout gate passes.",
    aggregate,
)
aggregate_path.write_text(aggregate, encoding="utf-8")
print("Installed one focused global sell-resumption revision with fresh December holdouts")
