"""Run the selected conference experiment and save traceable results locally."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from enbpi_project.data import lagged_split, load_solar
from enbpi_project.metrics import interval_metrics
from enbpi_project.model import EnbPI, sequential_intervals


def verify_sources():
    manifest = json.loads((ROOT / "references/source-manifest.json").read_text())
    for source in manifest["files"]:
        path = ROOT / source["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Research source changed: {path}; restore before reproduction")
    return manifest


def markdown_table(frame, formats=None):
    formats = formats or {}
    lines = ["| " + " | ".join(frame.columns) + " |",
             "| " + " | ".join("---" for _ in frame.columns) + " |"]
    for _, row in frame.iterrows():
        cells = [formats.get(col, lambda v: f"{v:.4f}" if isinstance(v, float) else str(v))(row[col]) for col in frame.columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def create_outputs(output, metrics, examples, config, metadata):
    metrics.to_csv(output / "metrics_by_trial.csv", index=False)
    summary = metrics.groupby(["method", "alpha"], as_index=False).agg(
        coverage_mean=("coverage", "mean"), coverage_std=("coverage", "std"),
        width_mean=("mean_width", "mean"), width_std=("mean_width", "std"),
        interval_score_mean=("interval_score", "mean"), mae_mean=("mae", "mean"),
        trials=("seed", "count"),
    )
    summary["target_coverage"] = 1 - summary.alpha
    summary.to_csv(output / "summary.csv", index=False)
    original = pd.read_csv(ROOT / "references/upstream/Results/Solar_Atl_many_alpha_new_1d.csv")
    original = original[(original.muh_fun == "RandomForestRegressor") & (original.method == "Ensemble")].copy()
    original["alpha_key"] = original.alpha.round(8)
    reference = original.groupby("alpha_key", as_index=False).agg(
        upstream_coverage=("coverage", "mean"), upstream_width=("width", "mean"),
        upstream_trials=("itrial", "nunique"))
    local = summary[summary.method == "EnbPI"].copy()
    local["alpha_key"] = local.alpha.round(8)
    comparison = local.merge(reference, on="alpha_key", validate="one_to_one")
    if len(comparison) != len(local):
        raise ValueError("Missing corresponding upstream reference rows")
    comparison["coverage_difference_pp"] = 100 * (comparison.coverage_mean - comparison.upstream_coverage)
    comparison["width_difference"] = comparison.width_mean - comparison.upstream_width
    comparison.to_csv(output / "upstream_comparison.csv", index=False)

    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    comp = comparison.sort_values("target_coverage")
    axes[0].plot(comp.target_coverage, comp.target_coverage, "--", color="#64748b", label="Target")
    for ax, field, ref, error, ylabel in [
        (axes[0], "coverage_mean", "upstream_coverage", "coverage_std", "Observed coverage"),
        (axes[1], "width_mean", "upstream_width", "width_std", "Mean interval width (W/m²)")]:
        ax.errorbar(comp.target_coverage, comp[field], yerr=comp[error].fillna(0),
                    fmt="o-", color="#0f766e", capsize=4, label="Local run (mean ± seed SD)")
        ax.plot(comp.target_coverage, comp[ref], "s--", color="#b45309", label="Authors' saved results")
        ax.set(xlabel="Nominal coverage", ylabel=ylabel)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=9)
    fig.suptitle("EnbPI reproduction | Atlanta solar, lag-only random forest", fontsize=14)
    fig.savefig(output / "coverage_width.png", dpi=170)
    plt.close(fig)

    example = examples["example"]
    subset = example.iloc[:24 * 7]
    fig, ax = plt.subplots(figsize=(12, 4.8), layout="constrained")
    dates = pd.to_datetime(subset.timestamp)
    ax.fill_between(dates, subset.lower, subset.upper, color="#99f6e4", alpha=0.75, label="90% nominal interval")
    ax.plot(dates, subset.actual, color="#0f172a", linewidth=1.4, label="Actual DHI")
    ax.plot(dates, subset.center, color="#0f766e", linewidth=1, label="EnbPI center")
    ax.set(title="First seven test days | one-hour-ahead forecasts", ylabel="Solar irradiance (W/m²)", xlabel="2018 local standard time")
    ax.legend(loc="upper left", ncols=3, fontsize=9)
    ax.grid(alpha=0.2)
    fig.savefig(output / "forecast_week.png", dpi=170)
    plt.close(fig)

    rolling = example.covered.rolling(24 * 7, min_periods=24 * 7).mean()
    fig, ax = plt.subplots(figsize=(12, 3.7), layout="constrained")
    ax.plot(pd.to_datetime(example.timestamp), rolling, color="#0f766e", linewidth=1)
    ax.axhline(0.9, color="#b45309", linestyle="--", label="90% target")
    ax.set(title="Rolling seven-day coverage | first seed", ylabel="Observed coverage", xlabel="2018 local standard time", ylim=(0, 1.03))
    ax.legend()
    ax.grid(alpha=0.2)
    fig.savefig(output / "rolling_coverage.png", dpi=170)
    plt.close(fig)

    hourly = pd.concat(examples["hourly"], ignore_index=True)
    hourly.to_csv(output / "hourly_coverage_by_trial.csv", index=False)
    hourly_summary = hourly.groupby("hour", as_index=False).agg(
        coverage_mean=("coverage", "mean"), coverage_std=("coverage", "std"), n_per_seed=("n", "first"))
    hourly_summary.to_csv(output / "hourly_coverage.csv", index=False)
    fig, ax = plt.subplots(figsize=(12, 3.7), layout="constrained")
    ax.bar(hourly_summary.hour, hourly_summary.coverage_mean, color="#0f766e")
    ax.axhline(0.9, color="#b45309", linestyle="--", label="90% target")
    ax.set(title="Coverage by hour | 90% nominal intervals, mean across seeds", xlabel="Hour (local standard time)", ylabel="Observed coverage", ylim=(0, 1.07), xticks=range(0, 24, 2))
    ax.legend()
    fig.savefig(output / "hourly_coverage.png", dpi=170)
    plt.close(fig)

    focus = comp[np.isclose(comp.alpha, 0.1)].iloc[0]
    frozen = summary[(summary.method == "Frozen residual diagnostic") & np.isclose(summary.alpha, 0.1)].iloc[0]
    display = comp[["target_coverage", "coverage_mean", "upstream_coverage", "coverage_difference_pp", "width_mean", "upstream_width"]].copy()
    display.columns = ["Target", "Local coverage", "Upstream coverage", "Difference (pp)", "Local width", "Upstream width"]
    status = "Smoke check: one seed only" if len(config["seeds"]) == 1 else "Selected reproduction: ten seeds, five nominal levels"
    report = f"""# EnbPI solar reproduction results

**{status}.** This is the lag-only random-forest subset of Figure 1, not a reproduction of the entire paper.

## Main result

At 90% nominal coverage, local intervals covered **{focus.coverage_mean:.2%}** of test outcomes on average, versus **{focus.upstream_coverage:.2%}** in the authors' saved CSV. Mean interval width was **{focus.width_mean:.2f} W/m²** versus **{focus.upstream_width:.2f} W/m²** upstream. These are computed results, not values read from a plotted line.

{markdown_table(display)}

![Coverage and width](coverage_width.png)

## What was run

- {metadata['rows']} hourly observations; {metadata['train_raw']} raw training observations, {metadata['train_effective']} effective lagged training examples, and {metadata['test_rows']} test observations.
- Test period: {metadata['test_start']} through {metadata['test_end']} (dataset local standard time).
- {config['lags']} past targets per forecast; {config['bootstraps']} bootstrap forests, {config['trees']} trees each, maximum depth {config['max_depth']}.
- {len(config['seeds'])} seeds; {len(config['alphas'])} nominal levels; one-hour feedback; no refitting during the test period.
- Sources pinned to commit `{metadata['upstream_commit']}` and verified by SHA-256 before the run.

See `config.json`, `run_metadata.json`, `metrics_by_trial.csv`, and `upstream_comparison.csv` for the complete audit trail. Each seed/alpha pair has a compressed CSV in `predictions/` with timestamps, actuals, centers, bounds, and coverage indicators.

## Interpretation

Observed overall coverage is not a guarantee of equally good coverage at every hour. The hourly plot is a diagnostic, and seed variation is not a confidence interval for coverage on new years or cities.

![Coverage by hour](hourly_coverage.png)

A frozen-residual diagnostic uses the same centers but never updates the initial error distribution. At the 90% target its observed coverage was {frozen.coverage_mean:.2%}, with mean width {frozen.width_mean:.2f} W/m². This is an additional experiment, not a method reproduced from Figure 1.

![First forecast week](forecast_week.png)

![Rolling coverage](rolling_coverage.png)

## Differences and limitations

- Modern Python, NumPy, and scikit-learn replace the original software environment. Numerical/seed results can differ from the authors' historical saved CSV.
- The local algorithm is tested against selected unchanged upstream methods in the same current environment; that verifies code parity, not historical bitwise reproducibility.
- The forest loss name changes from `mse` to `squared_error`; fitting uses one worker. Alpha-specific centers and the original percentile convention are retained.
- Forests are fitted once per seed and reused across alpha values because the upstream wrapper resets the same seed before each alpha run. No outcome-dependent tuning is performed.
- Intervals remain unbounded and may include negative irradiance. Bounds are not clipped in this reproduction.
- The same test period is evaluated under each seed. Repeated seeds do not add independent temporal observations.
- Retail demand, longer forecast horizons, inventory decisions, and the original neural-network/ARIMA experiments have not been evaluated.

## Attribution

Xu and Xie (ICML 2021), [Conformal prediction interval for dynamic time-series](https://proceedings.mlr.press/v139/xu21h.html). Upstream implementation: [hamrel-cxu/EnbPI](https://github.com/hamrel-cxu/EnbPI). Local scope and compatibility notes are in `../../docs/reproduction-notes.md`.
"""
    (output / "report.md").write_text(report, encoding="utf-8")
    print(display.to_string(index=False), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/smoke.json")
    args = parser.parse_args()
    config = json.loads((ROOT / args.config).read_text())
    if 0.1 not in config["alphas"]:
        raise ValueError("Include alpha=0.1 for the standard diagnostic plots")
    source_manifest = verify_sources()
    output = ROOT / "outputs" / config["name"]
    output.resolve().relative_to((ROOT / "outputs").resolve())
    output.mkdir(parents=True, exist_ok=True)
    (output / "predictions").mkdir(exist_ok=True)
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    timestamps, y = load_solar(ROOT / "data/raw/Solar_Atl_data.csv", config["max_rows"])
    train_size = int(config["train_fraction"] * len(y))
    X_train, X_test, y_train, y_test = lagged_split(y, train_size, config["lags"])
    test_times = timestamps.iloc[train_size:].reset_index(drop=True)
    started = time.perf_counter()
    metadata = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(),
                "packages": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scipy", "scikit-learn", "matplotlib")},
                "upstream_commit": source_manifest["commit"], "rows": len(y),
                "train_raw": train_size, "train_effective": len(y_train), "test_rows": len(y_test),
                "test_start": str(test_times.iloc[0]), "test_end": str(test_times.iloc[-1]),
                "source_checksums_verified": True,
                "local_code_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted((ROOT / "src").rglob("*.py")) + [Path(__file__)]}}
    rows, examples = [], {"hourly": []}
    for seed in config["seeds"]:
        model = EnbPI(config["bootstraps"], config["trees"], config["max_depth"], seed).fit(X_train, y_train)
        for alpha in config["alphas"]:
            centers = model.predict_centers(X_test, alpha)
            bounds = sequential_intervals(centers, y_test, model.training_residuals_, alpha)
            values = interval_metrics(y_test, centers, bounds, alpha)
            row = {"method": "EnbPI", "seed": seed, "alpha": alpha, "empty_oob_rows": model.empty_oob_count_, **values}
            rows.append(row)
            radius = np.percentile(model.training_residuals_, int(100 * (1 - alpha)), method="linear")
            frozen = np.column_stack((centers - radius, centers + radius))
            rows.append({"method": "Frozen residual diagnostic", "seed": seed, "alpha": alpha,
                         "empty_oob_rows": model.empty_oob_count_, **interval_metrics(y_test, centers, frozen, alpha)})
            frame = pd.DataFrame({"timestamp": test_times, "actual": y_test, "center": centers,
                                  "lower": bounds[:, 0], "upper": bounds[:, 1],
                                  "covered": (y_test >= bounds[:, 0]) & (y_test <= bounds[:, 1])})
            frame.to_csv(output / "predictions" / f"seed_{seed}_alpha_{alpha:.2f}.csv.gz", index=False,
                         compression={"method": "gzip", "mtime": 0})
            if np.isclose(alpha, 0.1):
                if "example" not in examples:
                    examples["example"] = frame
                hourly = frame.assign(hour=test_times.dt.hour).groupby("hour", as_index=False).agg(
                    coverage=("covered", "mean"), n=("covered", "size"))
                hourly["seed"] = seed
                examples["hourly"].append(hourly)
            print(f"seed={seed} target={1-alpha:.0%} coverage={values['coverage']:.4f} width={values['mean_width']:.2f}", flush=True)
    metadata["elapsed_seconds"] = time.perf_counter() - started
    metadata["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    create_outputs(output, pd.DataFrame(rows), examples, config, metadata)
    print(f"Saved results to {output}", flush=True)


if __name__ == "__main__":
    main()
