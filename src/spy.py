"""SPY data snapshot and preprocessing (methodology §11).

The snapshot is downloaded once, saved with an access timestamp and SHA-256,
and every analysis reads the saved file only. Not executed in Phase 1.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def download_snapshot(out_dir, start="1993-01-29", end="2026-10-01", ticker="SPY"):
    """Download split- and dividend-adjusted closes (yfinance, auto_adjust=True)
    and write <ticker>.csv plus a metadata JSON with timestamp and SHA-256."""
    import yfinance as yf

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    close = df["Close"].squeeze("columns").rename("close").dropna()
    path = out / f"{ticker}.csv"
    close.to_csv(path, index_label="date")
    meta = {
        "ticker": ticker,
        "source": "Yahoo Finance via yfinance, auto_adjust=True",
        "yfinance_version": yf.__version__,
        "start": start,
        "end_exclusive": end,
        "accessed_utc": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(len(close)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    (out / f"{ticker}.meta.json").write_text(json.dumps(meta, indent=2))
    return path


def load_snapshot(path):
    """Read a saved snapshot and verify its SHA-256 against the metadata file."""
    path = Path(path)
    meta = json.loads(path.with_suffix(".meta.json").read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError(f"{path} does not match its recorded SHA-256")
    return pd.read_csv(path, index_col="date", parse_dates=True)["close"]


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
