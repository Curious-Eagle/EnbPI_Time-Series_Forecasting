"""Auditable random-forest subset of the ICML 2021 EnbPI implementation.

Adapted from hamrel-cxu/EnbPI, commit 60cd5b7530eb954b02ae94da967111f5b5c3c01b.
Copyright (c) 2021 cx971111; MIT license: references/upstream/LICENSE.
This module intentionally follows the conference code, not the journal variant.
"""
from collections import deque

import numpy as np
from sklearn.ensemble import RandomForestRegressor


class EnbPI:
    """Bootstrap forests with leave-one-out aggregation and legacy centers.

    The same RandomState supplies bootstrap indices and tree seeds, matching
    the upstream global NumPy random stream without changing global state.
    """

    def __init__(self, bootstraps=30, trees=10, max_depth=2, seed=98765):
        if bootstraps < 1 or trees < 1:
            raise ValueError("bootstraps and trees must be positive")
        self.bootstraps = bootstraps
        self.trees = trees
        self.max_depth = max_depth
        self.seed = seed

    def fit(self, X, y):
        X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
        if X.ndim != 2 or y.ndim != 1 or len(X) != len(y) or len(y) < 2:
            raise ValueError("Expected aligned 2-D features and 1-D targets")
        if not np.isfinite(X).all() or not np.isfinite(y).all():
            raise ValueError("Training data must be finite")
        n = len(y)
        rng = np.random.RandomState(self.seed)
        samples = np.array([rng.choice(n, n) for _ in range(self.bootstraps)])
        included = np.zeros((self.bootstraps, n), dtype=bool)
        train_predictions = np.empty((self.bootstraps, n))
        self.models_ = []
        for b, indices in enumerate(samples):
            forest = RandomForestRegressor(
                n_estimators=self.trees, max_depth=self.max_depth,
                bootstrap=False, criterion="squared_error", max_features=1.0,
                n_jobs=1, random_state=rng,
            )
            forest.fit(X[indices], y[indices])
            self.models_.append(forest)
            train_predictions[b] = forest.predict(X)
            included[b, indices] = True

        counts = (~included).sum(axis=0)
        self.empty_oob_count_ = int((counts == 0).sum())
        # Upstream predicts zero when no bootstrap omitted a training row.
        self.oob_weights_ = (~included).T / np.maximum(counts[:, None], 1)
        fitted = np.sum(self.oob_weights_ * train_predictions.T, axis=1)
        self.training_residuals_ = np.abs(y - fitted)
        self.n_features_ = X.shape[1]
        return self

    def predict_centers(self, X, alpha=0.1, chunk_size=256):
        """Predict without receiving any future targets.

        Preserve the upstream order statistic at zero-based floor((1-alpha)*n),
        rather than substituting a mean or a interpolated quantile.
        """
        if not hasattr(self, "models_"):
            raise ValueError("Fit the model before prediction")
        if not 0 < alpha < 1:
            raise ValueError("alpha must be strictly between zero and one")
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[1] != self.n_features_ or not np.isfinite(X).all():
            raise ValueError("Prediction features must be finite and match training")
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        index = int((1 - alpha) * len(self.training_residuals_))
        centers = np.empty(len(X))
        for start in range(0, len(X), chunk_size):
            chunk = X[start:start + chunk_size]
            predictions = np.array([model.predict(chunk) for model in self.models_])
            loo_predictions = self.oob_weights_ @ predictions
            centers[start:start + len(chunk)] = np.partition(loo_predictions, index, axis=0)[index]
        return centers


class RollingIntervals:
    """A fixed-length error window; issue interval before observing its target."""

    def __init__(self, training_residuals, alpha=0.1):
        residuals = np.asarray(training_residuals, dtype=float)
        if residuals.ndim != 1 or len(residuals) == 0 or not np.isfinite(residuals).all() or np.any(residuals < 0):
            raise ValueError("Residuals must be a finite nonnegative vector")
        if not 0 < alpha < 1:
            raise ValueError("alpha must be strictly between zero and one")
        self.errors = deque(residuals, maxlen=len(residuals))
        # Preserve upstream integer percentile, including its rounding behavior.
        self.percentile = int(100 * (1 - alpha))

    def interval(self, center):
        if not np.isfinite(center):
            raise ValueError("Center must be finite")
        radius = float(np.percentile(self.errors, self.percentile, method="linear"))
        return center - radius, center + radius

    def observe(self, actual, center):
        if not np.isfinite(actual) or not np.isfinite(center):
            raise ValueError("Observation and center must be finite")
        self.errors.append(abs(actual - center))


def sequential_intervals(centers, actuals, training_residuals, alpha):
    centers, actuals = np.asarray(centers), np.asarray(actuals)
    if centers.ndim != 1 or actuals.shape != centers.shape:
        raise ValueError("Centers and actuals must be aligned vectors")
    calibrator = RollingIntervals(training_residuals, alpha)
    bounds = np.empty((len(centers), 2))
    for i, (center, actual) in enumerate(zip(centers, actuals)):
        bounds[i] = calibrator.interval(center)
        calibrator.observe(actual, center)
    return bounds
