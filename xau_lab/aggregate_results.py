from __future__ import annotations

import json
import math
import os
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

import real_tick_lab as lab


def table_line(table: pd.DataFrame, selected: str, split: str) -> str:
    row = table[table.candidate == selected]
    if row.empty:
        return f"| {split} | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING |"
    r = row.iloc[0]
    return (
        f"| {split} | {int(r.windows)} | {int(r.trades)} | {r.net_profit:.2f} | "
        f"{r.profit_factor:.2f} | {r.win_rate:.2f}% | {r.max_drawdown_pct:.2f}% | "
        f"{int(r.positive_windows)}/{int(r.windows)} |"
    )


def aggregate(rows: pd.DataFrame, split: str) -> pd.DataFrame:
    data = rows[rows["split"] == split].copy()
    agg = data.groupby("candidate", as_index=False).agg(
        net_profit=("net_profit", "sum"),
        gross_profit=("gross_profit", "sum"),
        gross_loss=("gross_loss", "sum"),
        trades=("trades", "sum"),
        wins=("wins", "sum"),
        losses=("losses", "sum"),
        max_drawdown_pct=("max_drawdown_pct", "max"),
        positive_windows=("positive", "sum"),
        windows=("window", "count"),
    )
    denom = agg["gross_loss"].abs()
    agg["profit_factor"] = np.where(
        denom > 0,
        agg["gross_profit"] / denom,
        np.where(agg["gross_profit"] > 0, 999.0, 0.0),
    )
    agg["win_rate"] = np.where(
        agg["trades"] > 0,
        agg["wins"] / agg["trades"] * 100.0,
        0.0,
    )
    agg["positive_window_ratio"] = np.where(
        agg["windows"] > 0,
        agg["positive_windows"] / agg["windows"],
        0.0,
    )
    agg["expected_payoff"] = np.where(
        agg["trades"] > 0,
        agg["net_profit"] / agg["trades"],
        0.0,
    )
    return agg


def development_score(row: pd.Series) -> float:
    if row.trades < 30:
        return -1e9 + float(row.trades)
    pf = min(float(row.profit_factor), 3.0)
    return (
        float(row.net_profit)
        * max(0.1, pf)
        * (0.5 + float(row.positive_window_ratio))
        * (0.5 + min(float(row.win_rate), 70.0) / 70.0)
        * math.sqrt(max(float(row.trades), 1.0) / 50.0)
        / (1.0 + float(row.max_drawdown_pct))
    )


def choose_candidate(all_rows: pd.DataFrame):
    dev = aggregate(all_rows, "dev")
    validation = aggregate(all_rows, "validation")
    holdout = aggregate(all_rows, "holdout")
    dev["dev_score"] = dev.apply(development_score, axis=1)
    top = dev.sort_values("dev_score", ascending=False).head(8)
    shortlist = validation[validation["candidate"].isin(top["candidate"])].copy()
    shortlist["validation_score"] = shortlist.apply(development_score, axis=1)
    eligible = shortlist[
        (shortlist["net_profit"] > 0)
        & (shortlist["profit_factor"] >= 1.15)
        & (shortlist["trades"] >= 10)
        & (shortlist["positive_window_ratio"] >= 0.5)
    ]
    if eligible.empty:
        selected = str(top.iloc[0]["candidate"])
        reason = (
            "No development-top-eight candidate passed the separate validation gate; "
            "selected the development leader for diagnosis only."
        )
    else:
        selected = str(eligible.sort_values("validation_score", ascending=False).iloc[0]["candidate"])
        reason = "Selected from the development top eight using the separate 2024 validation gate."

    hold_row = holdout[holdout["candidate"] == selected].iloc[0]
    combined = all_rows[all_rows["candidate"] == selected]
    gross_profit = combined["gross_profit"].sum()
    gross_loss = combined["gross_loss"].sum()
    combined_pf = gross_profit / abs(gross_loss) if gross_loss < 0 else (999.0 if gross_profit > 0 else 0.0)
    combined_trades = int(combined["trades"].sum())
    combined_wins = int(combined["wins"].sum())
    combined_wr = combined_wins / combined_trades * 100.0 if combined_trades else 0.0
    selected_dev = dev[dev["candidate"] == selected].iloc[0]
    success = bool(
        hold_row.net_profit > 0
        and hold_row.profit_factor >= 1.15
        and hold_row.positive_window_ratio >= 0.5
        and hold_row.trades >= 10
        and combined_pf >= 1.25
        and combined_trades >= 70
        and combined_wr >= 50.0
        and max(float(selected_dev.max_drawdown_pct), float(hold_row.max_drawdown_pct)) < 10.0
    )
    return selected, {"dev": dev, "validation": validation, "holdout": holdout, "top": top, "shortlist": shortlist}, success, reason


def main() -> int:
    collected = Path(os.environ.get("COLLECTED_DIR", "collected"))
    results = Path(os.environ.get("RESULTS_DIR", "results"))
    results.mkdir(parents=True, exist_ok=True)

    metric_files = sorted(collected.rglob("window_metrics_*.csv"))
    trade_files = sorted(collected.rglob("window_trades_*.csv"))
    complete_files = sorted(collected.rglob("window_*_complete.txt"))
    if len(metric_files) != len(lab.WINDOWS):
        raise RuntimeError(
            f"Expected {len(lab.WINDOWS)} completed metric files, found {len(metric_files)}. "
            f"Completion markers: {len(complete_files)}"
        )

    metrics_df = pd.concat([pd.read_csv(p) for p in metric_files], ignore_index=True)
    nonempty_trades = []
    for path in trade_files:
        try:
            frame = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue
        if not frame.empty:
            nonempty_trades.append(frame)
    trades_df = pd.concat(nonempty_trades, ignore_index=True) if nonempty_trades else pd.DataFrame()

    metrics_df.to_csv(results / "window_metrics.csv", index=False)
    trades_df.to_csv(results / "all_trades.csv", index=False)

    selected, tables, success, reason = choose_candidate(metrics_df)
    candidates = {candidate.name: candidate for candidate in lab.candidates()}
    selected_candidate = candidates[selected]
    for name, table in tables.items():
        table.to_csv(results / f"aggregate_{name}.csv", index=False)

    selected_rows = metrics_df[metrics_df.candidate == selected].copy()
    selected_trades = trades_df[trades_df.candidate == selected].copy() if not trades_df.empty else pd.DataFrame()
    selected_rows.to_csv(results / "selected_window_metrics.csv", index=False)
    selected_trades.to_csv(results / "selected_trades.csv", index=False)
    (results / "selected_candidate.json").write_text(
        json.dumps(
            {"success": bool(success), "reason": reason, "candidate": asdict(selected_candidate)},
            indent=2,
        ),
        encoding="utf-8",
    )

    gross_profit = selected_rows.gross_profit.sum()
    gross_loss = selected_rows.gross_loss.sum()
    combined_pf = gross_profit / abs(gross_loss) if gross_loss < 0 else (999.0 if gross_profit > 0 else 0.0)
    combined_trades = int(selected_rows.trades.sum())
    combined_wins = int(selected_rows.wins.sum())
    combined_wr = combined_wins / combined_trades * 100.0 if combined_trades else 0.0
    combined_net = selected_rows.net_profit.sum()
    max_dd = selected_rows.max_drawdown_pct.max()

    report = f"""# XAUUSD M1 Real-Tick Validation Lab

## Decision

- Selected candidate: `{selected}`
- Gate result: **{'PASSED' if success else 'NOT PASSED'}**
- Selection logic: {reason}
- Data: partitioned XAUUSD real bid/ask tick parquet mirror, sourced from Dukascopy through Tickstory.
- Time handling: UTC ticks converted to EET/EEST (`Europe/Helsinki`) for server-hour logic.
- Execution stress: observed spread plus {selected_candidate.slippage_price:.2f} adverse price slippage per entry/market exit.
- No Headway 2026 test date was used for candidate selection.

## Split Results

| Split | Windows | Trades | Net USD | Profit Factor | Win Rate | Max DD | Positive windows |
|---|---:|---:|---:|---:|---:|---:|---:|
{table_line(tables['dev'], selected, 'dev')}
{table_line(tables['validation'], selected, 'validation')}
{table_line(tables['holdout'], selected, 'holdout')}

## Combined Independent Windows

- Trades: {combined_trades}
- Net profit across independently reset $500 windows: {combined_net:.2f} USD
- Profit factor: {combined_pf:.2f}
- Win rate: {combined_wr:.2f}%
- Worst single-window drawdown: {max_dd:.2f}%

## Guardrails

This is an independent research backtest, not a promise of profit. The parquet mirror, Dukascopy and Headway quotes, symbol specifications, latency, commission, swaps, stop execution, and trading sessions can differ. The candidate is considered acceptable only when the untouched 2025 holdout gate passes. If the gate is not passed, the current robot remains the safer reference and no successful claim is made.
"""
    (results / "REPORT.md").write_text(report, encoding="utf-8")
    print(report, flush=True)
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
