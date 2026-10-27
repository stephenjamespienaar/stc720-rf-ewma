"""SPY data snapshot, integrity checks and preprocessing (methodology §11).

The snapshot is downloaded once, saved with an access timestamp and SHA-256,
and every analysis reads the saved file only. Yahoo back-adjusts its history
for distributions, so a later download can differ: the frozen file is the record.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def write_snapshot(df, out_dir, meta, ticker="SPY"):
    """Write the raw downloaded frame (all adjusted columns) to <ticker>.csv and a
    metadata JSON with its SHA-256. Refuses to overwrite an existing snapshot."""
    out = Path(out_dir)
    path = out / f"{ticker}.csv"
    if path.exists() or path.with_suffix(".meta.json").exists():
        raise FileExistsError(f"refusing to overwrite the frozen snapshot {path}")
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index_label="date")
    meta = {**meta, "ticker": ticker, "n_rows": int(len(df)), "columns": list(map(str, df.columns)),
            "first_date": str(df.index[0].date()) if len(df) else None,
            "last_date": str(df.index[-1].date()) if len(df) else None,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))
    return path


def download_snapshot(out_dir, start="1993-01-29", end="2026-10-01", ticker="SPY"):
    """Download split- and dividend-adjusted daily bars once (S1: explicit
    auto_adjust=True, multi_level_index=False, repair=False; keepna=True so that
    missing rows surface in the integrity check instead of being dropped) and freeze
    them with write_snapshot. Needs the student's explicit authorization."""
    import yfinance as yf

    kw = dict(start=start, end=end, auto_adjust=True, multi_level_index=False, repair=False, keepna=True,
              ignore_tz=True, actions=False, progress=False, threads=False)
    df = yf.download(ticker, **kw)
    meta = {"source": "Yahoo Finance via yfinance", "yfinance_version": yf.__version__,
            "pandas_version": pd.__version__, "download_args": {k: v for k, v in kw.items()},
            "end_exclusive": end, "accessed_utc": datetime.now(timezone.utc).isoformat(),
            "note": "adjusted history is back-adjusted by Yahoo and can change between downloads"}
    return write_snapshot(df, out_dir, meta, ticker)


def load_snapshot(path):
    """Read a saved snapshot's adjusted close and verify its SHA-256 against the metadata file."""
    path = Path(path)
    meta = json.loads(path.with_suffix(".meta.json").read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError(f"{path} does not match its recorded SHA-256")
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    return df["Close" if "Close" in df else "close"]


def integrity(close, first, last_max, rows=(8480, 8490)):
    """S1 checks on the adjusted close. Hard errors (chronology or values) stop the
    analysis; the row count and long calendar gaps are diagnostics only: nothing
    is inserted, filled or deleted."""
    idx, err = close.index, []
    if len(close) == 0:
        return {"errors": ["no data"]}
    if not idx.is_unique:
        err.append(f"duplicate dates: {sorted(set(map(str, idx[idx.duplicated()].date)))[:10]}")
    if not idx.is_monotonic_increasing:
        err.append("dates not increasing")
    if getattr(idx, "tz", None) is not None:
        return {"errors": ["timezone-aware dates"]}
    v = close.to_numpy(float)
    bad = ~np.isfinite(v) | (v <= 0)
    if bad.any():
        err.append(f"non-finite or non-positive prices on {[str(d.date()) for d in idx[bad][:10]]}")
    if idx[0] != pd.Timestamp(first):
        err.append(f"first date {idx[0].date()} != {first}")
    if idx[-1] > pd.Timestamp(last_max):
        err.append(f"last date {idx[-1].date()} after {last_max}")
    gaps = np.diff(idx.values).astype("timedelta64[D]").astype(int) if idx.is_monotonic_increasing else np.array([])
    long = [(str(idx[i].date()), str(idx[i + 1].date()), int(g)) for i, g in enumerate(gaps) if g > 4]
    return {"errors": err, "n_rows": int(len(close)), "first": str(idx[0].date()), "last": str(idx[-1].date()),
            "expected_rows": list(rows), "rows_in_expected_range": bool(rows[0] <= len(close) <= rows[1]),
            "calendar_gaps_over_4_days": long}


def log_returns(close):
    """Percent log returns r_t = 100 ln(P_t / P_{t-1}) (eq. 1)."""
    return (100.0 * np.log(close).diff()).dropna()


def split(r, train_end, monitor_start):
    """Chronological split: training (<= train_end) and monitoring
    (>= monitor_start). Both are demeaned by the training mean only."""
    train = r[r.index <= pd.Timestamp(train_end)]
    monitor = r[r.index >= pd.Timestamp(monitor_start)]
    if not train.index.max() < monitor.index.min():
        raise ValueError("training and monitoring windows overlap")
    mu = train.mean()
    return train - mu, monitor - mu, float(mu)
