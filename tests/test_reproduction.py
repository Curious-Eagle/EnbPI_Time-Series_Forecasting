"""Meaningful checks: upstream parity, chronological features, causal updates."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

from enbpi_project.data import lagged_split
from enbpi_project.metrics import interval_metrics
from enbpi_project.model import EnbPI, sequential_intervals

ROOT = Path(__file__).resolve().parents[1]


def load_upstream_subset():
    """Compile inspected functions only; no optional ML imports or demo execution."""
    manifest = json.loads((ROOT / "references/source-manifest.json").read_text())
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
    namespace = {"np": np, "pd": pd}
    utils_path = ROOT / "references/upstream/utils_EnbPI.py"
    utils = ast.parse(utils_path.read_text(encoding="utf-8"))
    functions = [node for node in utils.body if isinstance(node, ast.FunctionDef)
                 and node.name in {"generate_bootstrap_samples", "strided_app", "one_dimen_transform"}]
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(utils_path), "exec"), namespace)
    source_path = ROOT / "references/upstream/PI_class_EnbPI.py"
    parsed = ast.parse(source_path.read_text(encoding="utf-8"))
    original = next(node for node in parsed.body if isinstance(node, ast.ClassDef) and node.name == "prediction_interval")
    original.body = [node for node in original.body if isinstance(node, ast.FunctionDef)
                     and node.name in {"__init__", "fit_bootstrap_models_online", "compute_PIs_Ensemble_online"}]
    exec(compile(ast.Module(body=[original], type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace


@pytest.mark.parametrize("alpha", [0.05, 0.1, 0.15000000000000002, 0.2, 0.25])
def test_matches_unchanged_upstream_methods(alpha):
    source = load_upstream_subset()
    y = np.random.RandomState(31).normal(size=180).cumsum()
    X_train, X_test, y_train, y_test = lagged_split(y, 100, 8)
    kwargs = dict(n_estimators=10, max_depth=2, criterion="squared_error", bootstrap=False, n_jobs=1)
    np.random.seed(98765)
    reference = source["prediction_interval"](RandomForestRegressor(**kwargs), X_train, X_test, y_train, y_test)
    expected = reference.compute_PIs_Ensemble_online(alpha, 30, 1, []).to_numpy()
    actual_model = EnbPI().fit(X_train, y_train)
    actual = sequential_intervals(actual_model.predict_centers(X_test, alpha), y_test, actual_model.training_residuals_, alpha)
    np.testing.assert_allclose(actual, expected, atol=1e-10, rtol=1e-12)


def test_lags_match_original_and_exclude_current_target():
    y = np.arange(100, dtype=float)
    X_train, X_test, y_train, y_test = lagged_split(y, 60, 5)
    original = load_upstream_subset()["one_dimen_transform"](y[:60], y[60:], 5)
    for actual, expected in zip((X_train, X_test, y_train, y_test), original):
        np.testing.assert_array_equal(actual, expected)
    assert X_test[0].tolist() == [55, 56, 57, 58, 59]
    changed = y.copy()
    changed[70:] = 100000
    changed_X = lagged_split(changed, 60, 5)[1]
    np.testing.assert_array_equal(changed_X[:11], X_test[:11])


def test_current_and_future_outcomes_cannot_change_issued_intervals():
    centers = np.arange(12, dtype=float)
    actuals = centers + 0.2
    initial_errors = np.linspace(0, 1, 10)
    original = sequential_intervals(centers, actuals, initial_errors, 0.1)
    altered = actuals.copy()
    altered[5:] += 1000
    changed = sequential_intervals(centers, altered, initial_errors, 0.1)
    np.testing.assert_array_equal(changed[:6], original[:6])
    assert not np.array_equal(changed[6:], original[6:])


def test_rolling_window_drops_old_errors():
    # A large historical error leaves the three-point window after step zero.
    bounds = sequential_intervals(np.zeros(4), np.zeros(4), [100, 0, 0], 0.1)
    assert bounds[0, 1] > 0
    np.testing.assert_array_equal(bounds[1:], np.zeros((3, 2)))


def test_metrics_with_known_misses_and_inclusive_boundary():
    metrics = interval_metrics([0, 2, 4], [1, 1, 1], [[0, 2], [0, 2], [0, 2]], 0.1)
    assert metrics["coverage"] == 2 / 3
    assert metrics["mean_width"] == 2
    assert metrics["interval_score"] == pytest.approx((2 + 2 + 42) / 3)


def test_rejects_reversed_bounds():
    with pytest.raises(ValueError):
        interval_metrics([1], [1], [[2, 0]], 0.1)


def test_reproducible_without_global_random_state_changes():
    y = np.arange(80, dtype=float)
    X_train, X_test, y_train, _ = lagged_split(y, 50, 5)
    np.random.seed(42)
    state = np.random.get_state()
    first = EnbPI(bootstraps=12).fit(X_train, y_train).predict_centers(X_test)
    np.testing.assert_array_equal(state[1], np.random.get_state()[1])
    assert state[2:] == np.random.get_state()[2:]
    second = EnbPI(bootstraps=12).fit(X_train, y_train).predict_centers(X_test)
    np.testing.assert_array_equal(first, second)
