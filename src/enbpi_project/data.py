"""Chronological, lag-only preparation for the upstream Solar_Atl dataset."""
import numpy as np
import pandas as pd


def lagged_split(y, train_size, lags):
    y = np.asarray(y, dtype=float)
    if y.ndim != 1 or not np.isfinite(y).all():
        raise ValueError("Target must be a finite one-dimensional series")
    if lags < 1 or train_size <= lags or train_size >= len(y):
        raise ValueError("Require 1 <= lags < train_size < series length")
    # Row t contains y[t-lags:t], excluding y[t]. Later test rows can use
    # earlier test actuals because this experiment assumes immediate feedback.
    windows = np.lib.stride_tricks.sliding_window_view(y, lags + 1)
    features = windows[:, :-1].copy()
    targets = windows[:, -1].copy()
    cut = train_size - lags
    return features[:cut], features[cut:], targets[:cut], targets[cut:]


def load_solar(path, max_rows=10000):
    frame = pd.read_csv(path, skiprows=2).iloc[:max_rows].copy()
    timestamps = pd.to_datetime(frame[["Year", "Month", "Day", "Hour", "Minute"]].rename(columns=str.lower))
    if not timestamps.is_monotonic_increasing or timestamps.duplicated().any():
        raise ValueError("Dataset is not in strict chronological order")
    if not timestamps.diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError("Solar observations must be hourly without gaps")
    y = frame["DHI"].to_numpy(dtype=float)
    if not np.isfinite(y).all():
        raise ValueError("Dataset has missing/nonfinite DHI values")
    return timestamps, y
