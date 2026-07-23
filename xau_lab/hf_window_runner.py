from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from huggingface_hub import HfApi, hf_hub_download

import real_tick_lab as lab

REPO_ID = "CarlosSilva1/xauusd-ticks"

# Development and validation windows remain unchanged. The prior 2025 holdout
# months have now been observed and are retired. Two previously unused date
# windows become the fresh selection-blind holdout for this single revision.
WINDOWS = [
    ("dev_2021_jun", "dev", "2021-06-07", "2021-06-26"),
    ("dev_2021_oct", "dev", "2021-10-04", "2021-10-23"),
    ("dev_2022_mar", "dev", "2022-03-07", "2022-03-26"),
    ("dev_2022_sep", "dev", "2022-09-05", "2022-09-24"),
    ("dev_2023_mar", "dev", "2023-03-06", "2023-03-25"),
    ("dev_2023_oct", "dev", "2023-10-02", "2023-10-21"),
    ("val_2024_mar", "validation", "2024-03-04", "2024-03-23"),
    ("val_2024_oct", "validation", "2024-10-07", "2024-10-26"),
    ("hold_2021_feb", "holdout", "2021-02-01", "2021-02-20"),
    ("hold_2022_dec", "holdout", "2022-12-01", "2022-12-20"),
]


def iter_months(start: pd.Timestamp, end: pd.Timestamp):
    current = pd.Timestamp(start.year, start.month, 1, tz="UTC")
    finish = pd.Timestamp(end.year, end.month, 1, tz="UTC")
    while current <= finish:
        yield current.year, current.month
        current = current + pd.offsets.MonthBegin(1)


def build_window_hf(name: str, split: str, eval_start_s: str, eval_end_s: str) -> lab.WindowData:
    eval_start = pd.Timestamp(eval_start_s, tz="UTC")
    eval_end = pd.Timestamp(eval_end_s, tz="UTC")
    load_start = eval_start - pd.Timedelta(days=2)
    load_end = eval_end + pd.Timedelta(hours=2)

    files = HfApi().list_repo_files(REPO_ID, repo_type="dataset")
    frames: list[pd.DataFrame] = []
    for year, month in iter_months(load_start, load_end):
        prefix = f"year={year}/month={month:02d}/"
        matches = [f for f in files if f.startswith(prefix) and f.endswith(".parquet")]
        if not matches:
            raise RuntimeError(f"No parquet file found for {prefix}")
        for filename in matches:
            path = hf_hub_download(REPO_ID, filename=filename, repo_type="dataset")
            frame = pd.read_parquet(path, columns=["timestamp", "bid_price", "ask_price"])
            frames.append(frame)
            print(f"Loaded {filename}: {len(frame):,} ticks", flush=True)

    ticks = pd.concat(frames, ignore_index=True)
    ticks["timestamp"] = pd.to_datetime(ticks["timestamp"], utc=True)
    ticks = ticks[(ticks.timestamp >= load_start) & (ticks.timestamp < load_end)]
    ticks = ticks.dropna(subset=["timestamp", "bid_price", "ask_price"])
    ticks = ticks[(ticks.ask_price >= ticks.bid_price) & (ticks.bid_price > 100)]
    ticks = ticks.sort_values("timestamp").drop_duplicates(
        subset=["timestamp", "bid_price", "ask_price"], keep="last"
    )
    if ticks.empty:
        raise RuntimeError(f"No filtered real ticks for {name}")

    times = ticks.timestamp.to_numpy(dtype="datetime64[ms]")
    bids = ticks.bid_price.to_numpy(dtype=np.float64)
    asks = ticks.ask_price.to_numpy(dtype=np.float64)

    minute_ids = times.astype("datetime64[m]").astype(np.int64)
    unique_min, starts, counts = np.unique(minute_ids, return_index=True, return_counts=True)
    ends = starts + counts - 1
    opens = bids[starts]
    closes = bids[ends]
    highs = np.maximum.reduceat(bids, starts)
    lows = np.minimum.reduceat(bids, starts)
    first_ask = asks[starts]
    first_bid = bids[starts]

    idx = pd.to_datetime(unique_min, unit="m", utc=True)
    bars = pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "first_ask": first_ask,
            "first_bid": first_bid,
            "spread_first": first_ask - first_bid,
            "tick_start": starts,
            "tick_count": counts,
        },
        index=idx,
    )
    bars["ema9"] = lab.ema(bars["close"], 9)
    bars["ema21"] = lab.ema(bars["close"], 21)
    bars["atr14"] = lab.atr_wilder(bars, 14)

    m5 = lab.make_ohlc(bars[["open", "high", "low", "close"]], "5min")
    m5["ema20"] = lab.ema(m5["close"], 20)
    m5["ema50"] = lab.ema(m5["close"], 50)
    m5.index = m5.index + pd.Timedelta(minutes=5)

    m15 = lab.make_ohlc(bars[["open", "high", "low", "close"]], "15min")
    m15["ema20"] = lab.ema(m15["close"], 20)
    m15["ema50"] = lab.ema(m15["close"], 50)
    m15.index = m15.index + pd.Timedelta(minutes=15)

    m5a = m5[["close", "ema20", "ema50"]].reindex(bars.index, method="ffill")
    m15a = m15[["close", "ema20", "ema50"]].reindex(bars.index, method="ffill")
    bars[["m5_close", "m5_ema20", "m5_ema50"]] = m5a.to_numpy()
    bars[["m15_close", "m15_ema20", "m15_ema50"]] = m15a.to_numpy()
    bars["server_time"] = bars.index.tz_convert(lab.SERVER_TZ)

    print(
        f"Built {name}: ticks={len(ticks):,}, M1 bars={len(bars):,}, "
        f"range={bars.index.min()}..{bars.index.max()}",
        flush=True,
    )
    return lab.WindowData(
        name=name,
        split=split,
        eval_start=eval_start,
        eval_end=eval_end,
        times=times,
        asks=asks,
        bids=bids,
        minute_starts=starts,
        minute_counts=counts,
        bars=bars,
    )


def main() -> int:
    index = int(os.environ["WINDOW_INDEX"])
    out_dir = Path(os.environ.get("WINDOW_RESULTS_DIR", "window_results"))
    out_dir.mkdir(parents=True, exist_ok=True)
    name, split, start_s, end_s = WINDOWS[index]
    data = build_window_hf(name, split, start_s, end_s)

    metric_rows: list[dict] = []
    trade_rows: list[dict] = []
    candidates = lab.candidates()
    for pos, candidate in enumerate(candidates, 1):
        metrics, trades = lab.run_candidate(data, candidate)
        metric_rows.append(asdict(metrics))
        for trade in trades:
            row = asdict(trade)
            row.update(candidate=candidate.name, window=name, split=split)
            row["open_time"] = trade.open_time.isoformat()
            row["close_time"] = trade.close_time.isoformat()
            trade_rows.append(row)
        if pos % 10 == 0 or pos == len(candidates):
            print(f"Evaluated {pos}/{len(candidates)}", flush=True)

    pd.DataFrame(metric_rows).to_csv(out_dir / f"window_metrics_{index:02d}.csv", index=False)
    pd.DataFrame(trade_rows).to_csv(out_dir / f"window_trades_{index:02d}.csv", index=False)
    (out_dir / f"window_{index:02d}_complete.txt").write_text(
        f"{name}\n{split}\n{start_s}\n{end_s}\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
