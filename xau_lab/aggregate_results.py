from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

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

    selected, tables, success, reason = lab.choose_candidate(metrics_df)
    candidates = {c.name: c for c in lab.candidates()}
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

    gp = selected_rows.gross_profit.sum()
    gl = selected_rows.gross_loss.sum()
    combined_pf = gp / abs(gl) if gl < 0 else (999.0 if gp > 0 else 0.0)
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
