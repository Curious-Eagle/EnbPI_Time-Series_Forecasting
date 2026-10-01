"""Metrics for inclusive prediction intervals."""
import numpy as np


def interval_metrics(actual, center, bounds, alpha):
    actual, center, bounds = map(lambda x: np.asarray(x, dtype=float), (actual, center, bounds))
    if actual.ndim != 1 or len(actual) == 0 or center.shape != actual.shape or bounds.shape != (len(actual), 2):
        raise ValueError("Expected aligned actuals, centers, and two-column bounds")
    if not 0 < alpha < 1 or not all(np.isfinite(a).all() for a in (actual, center, bounds)):
        raise ValueError("Inputs must be finite and alpha must be in (0, 1)")
    lower, upper = bounds.T
    if np.any(lower > upper):
        raise ValueError("Lower bounds cannot exceed upper bounds")
    widths = upper - lower
    score = widths + 2 / alpha * (np.maximum(lower - actual, 0) + np.maximum(actual - upper, 0))
    return {"coverage": float(np.mean((actual >= lower) & (actual <= upper))),
            "mean_width": float(widths.mean()), "interval_score": float(score.mean()),
            "mae": float(np.mean(np.abs(actual - center))), "n_test": len(actual)}
