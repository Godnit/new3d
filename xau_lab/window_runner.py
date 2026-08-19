from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

import pandas as pd

import real_tick_lab as lab


def main() -> int:
    index = int(os.environ["WINDOW_INDEX"])
    if index < 0 or index >= len(lab.WINDOWS):
        raise SystemExit(f"WINDOW_INDEX out of range: {index}")

    out_dir = Path(os.environ.get("WINDOW_RESULTS_DIR", "window_results"))
    out_dir.mkdir(parents=True, exist_ok=True)
    name, split, start_s, end_s = lab.WINDOWS[index]
    data = lab.build_window(name, split, start_s, end_s)

    metrics_rows: list[dict] = []
    trade_rows: list[dict] = []
    candidates = lab.candidates()
    print(f"Window {index} {name}: evaluating {len(candidates)} candidates", flush=True)
    for pos, candidate in enumerate(candidates, 1):
        metrics, trades = lab.run_candidate(data, candidate)
        metrics_rows.append(asdict(metrics))
        for trade in trades:
            row = asdict(trade)
            row.update(candidate=candidate.name, window=name, split=split)
            row["open_time"] = trade.open_time.isoformat()
            row["close_time"] = trade.close_time.isoformat()
            trade_rows.append(row)
        if pos % 10 == 0 or pos == len(candidates):
            print(f"  evaluated {pos}/{len(candidates)}", flush=True)

    metrics_df = pd.DataFrame(metrics_rows)
    trades_df = pd.DataFrame(trade_rows)
    metrics_path = out_dir / f"window_metrics_{index:02d}.csv"
    trades_path = out_dir / f"window_trades_{index:02d}.csv"
    metrics_df.to_csv(metrics_path, index=False)
    trades_df.to_csv(trades_path, index=False)
    (out_dir / f"window_{index:02d}_complete.txt").write_text(
        f"{name}\n{split}\n{start_s}\n{end_s}\nmetrics={len(metrics_df)}\ntrades={len(trades_df)}\n",
        encoding="utf-8",
    )
    print(f"Saved {metrics_path} and {trades_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
