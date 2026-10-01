# EnbPI for Time-Series Forecasting

**Atlanta solar reproduction · Prediction intervals · Retail demand roadmap**

This project studies how to attach useful uncertainty intervals to forecasts. It adapts **Ensemble Batch Prediction Intervals (EnbPI)** from Xu and Xie's ICML 2021 paper, reproduces the lag-only random-forest subset of Figure 1, and examines where overall coverage hides unreliable forecasts.

The completed experiment uses **2018 hourly solar irradiance from Atlanta**. Retail sales forecasting is the next planned application; the repository currently contains solar results only.

| Completed experiment | Result |
| --- | --- |
| Data | 8,760 hourly observations; 7,008 test observations |
| Evaluation | 10 random seeds × 5 coverage targets |
| Coverage at the 90% target | **90.24% locally**, compared with **90.25%** in the authors' saved results |
| Mean interval width at the 90% target | **256.64 W/m² locally**, compared with **256.66 W/m²** upstream |
| Validation | **11 passing tests** for upstream parity, forecast timing, metrics, and reproducibility |

![EnbPI coverage and interval width across five nominal targets, compared with the authors' saved results](outputs/solar_reproduction/coverage_width.png)

*Means across ten seeds. Error bars show variation across seeds, not uncertainty about performance in other years or locations.*

[Dataset](#dataset) · [Method](#method-and-experiment-settings) · [Results](#reproduction-results) · [Diagnostics](#what-the-diagnostics-show) · [Run the project](#run-the-project) · [Files and documentation](#files-and-documentation) · [Next steps](#retail-demand-roadmap)

## Dataset

The source file is [Solar_Atl_data.csv](data/raw/Solar_Atl_data.csv), obtained from the pinned authors' repository. Its metadata identifies **NSRDB** as the original source and gives Atlanta coordinates of **33.76, −84.39**.

| Property | Value |
| --- | --- |
| Period | January 1–December 31, 2018 |
| Frequency | Hourly, with timestamps at `:30` |
| Time convention | Dataset local standard time, UTC−05:00; stored without timezone conversion |
| Target | Diffuse horizontal irradiance (**DHI**), measured in W/m² |
| Model inputs | The previous **20 hourly DHI observations** |
| Initial training period | January 1, 00:30–March 14, 23:30 |
| Raw training observations | **1,752**: the first 20% of the series |
| Training examples after creating lags | **1,732** |
| Test period | March 15, 00:30–December 31, 23:30 |
| Test observations | **7,008**: the remaining 80% |

The file contains two metadata rows before its CSV header. Timestamp fields are `Year`, `Month`, `Day`, `Hour`, and `Minute`. DNI, dew point, surface albedo, wind speed, relative humidity, temperature, and pressure are also present, but this experiment uses only past DHI values.

Computed over the full source series:

| Data check or statistic | Value |
| --- | --- |
| DHI minimum / maximum | 0 / 500 W/m² |
| Mean / median DHI | 69.31 / 0 W/m² |
| Zero-valued DHI observations | 4,434 of 8,760 |
| Missing DHI values | 0 |
| Duplicate timestamps | 0 |
| Spacing | One hour throughout, with no gaps |

The [loader](src/enbpi_project/data.py) validates finite targets, ordered unique timestamps, and hourly spacing. It preserves the chronological split and does not interpolate observations. See the [data dictionary](docs/data-dictionary.md) for field definitions.

## Method and experiment settings

EnbPI combines bootstrap models with a moving history of prediction errors. Here, each forecast estimates DHI **one hour ahead**, and the actual observation becomes available before the next forecast.

1. Build training features from the previous 20 observations, excluding the current target.
2. Draw 30 bootstrap samples and fit one small random forest to each sample.
3. Estimate each training error using only models whose bootstrap samples omitted that example. These out-of-bag errors initialize the interval calibration window.
4. Form an alpha-dependent forecast center using the original conference implementation's order statistic of leave-one-out ensemble predictions.
5. Issue a symmetric interval around that center using a percentile of the recent absolute errors.
6. Once the actual arrives, append its error and discard the oldest error. Continue with the same fitted forests.

The calibration window contains **1,732 errors**. The forecast is issued before its outcome updates that window, preserving the information available at prediction time.

| Setting | Full reproduction |
| --- | --- |
| Configuration | [configs/reproduction.json](configs/reproduction.json) |
| Bootstrap ensembles | 30 random forests per seed |
| Forest settings | 10 trees, maximum depth 2, `squared_error`, one worker |
| Sampling | Bootstrap training rows externally; `bootstrap=False` within each forest |
| Features | 20 DHI lags; no weather covariates |
| Seeds | 98765–98774 |
| Miscoverage levels, alpha | 0.05, 0.10, 0.15, 0.20, 0.25 |
| Nominal coverage, `1 − alpha` | 95%, 90%, 85%, 80%, 75% |
| Feedback | After each hourly observation; update stride 1 |
| Refitting during testing | None; each seed's fitted ensemble is reused across alpha levels |

The implementation retains the conference code's alpha-specific centers, integer percentile convention, and unclipped bounds. Compatibility changes and numerical details are documented in [reproduction notes](docs/reproduction-notes.md).

## Reproduction results

These are the saved results from the full run completed on **September 30, 2026**, averaged across ten seeds. Each seed evaluates the same 7,008 timestamps. The reference values come from the authors' matching [lag-only result CSV](references/upstream/Results/Solar_Atl_many_alpha_new_1d.csv), filtered to the random-forest ensemble method.

| Nominal coverage | Local coverage | Authors' coverage | Difference (pp) | Local width (W/m²) | Authors' width (W/m²) |
| --- | --- | --- | --- | --- | --- |
| 75% | 75.15% | 75.15% | −0.0043 | 95.63 | 95.62 |
| 80% | 79.96% | 79.93% | +0.0257 | 125.37 | 125.47 |
| 85% | 85.15% | 85.16% | −0.0029 | 169.87 | 169.97 |
| 90% | **90.24%** | **90.25%** | −0.0128 | **256.64** | **256.66** |
| 95% | 95.11% | 95.11% | −0.0029 | 373.90 | 373.88 |

*Differences are local minus upstream, calculated before rounding; pp means percentage points. Width is the average upper bound minus lower bound.*

The maximum absolute coverage difference from the authors' saved values is **0.0257 percentage points** across these five targets. Raising the coverage target also increases interval width, from **95.63 W/m² at 75%** to **373.90 W/m² at 95%**.

The runner reports four metrics:

| Metric | Interpretation |
| --- | --- |
| Empirical coverage | Fraction of actual observations inside the bounds, including the boundaries |
| Mean interval width | Average size of the predicted range; interpret alongside coverage |
| Interval score | Width plus a penalty for missed outcomes; lower is better at the same alpha |
| MAE | Mean absolute error of the forecast center |

Unrounded values and trial variation are available in the [summary](outputs/solar_reproduction/summary.csv), [per-trial metrics](outputs/solar_reproduction/metrics_by_trial.csv), and [upstream comparison](outputs/solar_reproduction/upstream_comparison.csv). The [generated report](outputs/solar_reproduction/report.md) collects the experiment outputs.

## What the diagnostics show

### Forecasts during the first test week

![Actual DHI, forecast centers, and 90% nominal intervals during March 15–21, 2018](outputs/solar_reproduction/forecast_week.png)

The first seed (`98765`) illustrates the daily cycle and several daytime peaks outside the 90% nominal intervals. The shaded band can extend below zero because bounds remain unclipped for comparison with the original implementation.

### Coverage varies substantially by hour

![Mean coverage by local hour, showing lower coverage around midday and full coverage during several nighttime hours](outputs/solar_reproduction/hourly_coverage.png)

At the 90% target, average coverage is **61.20% at local hour 12** and **61.16% at hour 13**, while several nighttime hours reach **100%**. Every hour has **292 test observations per seed**. The overall 90.24% result therefore hides substantial differences across the day.

These are diagnostics for this particular lag-only model. They do not establish the cause of every miss or describe all experiments in the original paper. See the [hourly results](outputs/solar_reproduction/hourly_coverage.csv).

### Coverage also changes over time

![Seven-day rolling coverage for seed 98765, compared with the 90% target](outputs/solar_reproduction/rolling_coverage.png)

This chart uses a moving window of **168 hourly predictions** from the first seed. Periods below the target remain visible even when coverage over the full test period is close to 90%.

### Updating the error window matters in this run

An additional diagnostic keeps the same forecast centers but freezes the initial training-error distribution throughout testing.

| Method at 90% nominal coverage | Coverage | Mean width (W/m²) | Interval score | MAE (W/m²) |
| --- | --- | --- | --- | --- |
| EnbPI with rolling errors | **90.24%** | 256.64 | **390.61** | 38.63 |
| Frozen residual diagnostic | 79.55% | 117.34 | 449.83 | 38.63 |

The frozen intervals are narrower but miss more observations and receive a worse interval score. Both methods have the same MAE because their centers are identical. This is a local diagnostic of interval updates, separate from the reproduced Figure 1 comparison.

## Run the project

Use **Python 3.12**. The recorded environment is Windows 11 with Python 3.12.14, NumPy 2.2.6, pandas 2.2.3, SciPy 1.15.3, scikit-learn 1.6.1, and Matplotlib 3.10.3. No GPU, account, or paid API is required.

From the repository root, set up the environment and fetch the research inputs. The download step requires internet access and refreshes the pinned source files, paper PDF, and source manifest.

**Windows / PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe scripts/fetch_sources.py

# Run the 11 validation tests.
.\.venv\Scripts\python.exe -m pytest

# Smoke run: one seed at 90% nominal coverage.
.\.venv\Scripts\python.exe scripts/run_experiment.py --config configs/smoke.json

# Full selected reproduction: ten seeds and five coverage targets.
.\.venv\Scripts\python.exe scripts/run_experiment.py --config configs/reproduction.json
```

**macOS / Linux**

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/fetch_sources.py
.venv/bin/python -m pytest
.venv/bin/python scripts/run_experiment.py --config configs/smoke.json
.venv/bin/python scripts/run_experiment.py --config configs/reproduction.json
```

The lock file records the tested Windows environment; macOS and Linux have not been verified. [requirements.txt](requirements.txt) lists direct dependencies, while [requirements-lock.txt](requirements-lock.txt) records installed versions. If the environment and research inputs are already present, start with the validation or experiment commands.

After setup, experiments run offline. Both the runner and upstream parity tests verify the files listed in the source manifest, including the downloaded PDF. A fresh clone therefore needs the fetch step even though the solar CSV and selected upstream code are tracked in Git.

Results are written to `outputs/solar_smoke/` or `outputs/solar_reproduction/`. Re-running a configuration overwrites its corresponding generated files. For a separate experiment, copy a config and give it a new `name`; include `alpha=0.1` in `alphas` because the standard diagnostics require the 90% target.

The [walkthrough notebook](notebooks/01_explore_reproduction.ipynb) reads saved outputs. Open it in a Jupyter or VS Code notebook environment with this project's Python interpreter. A notebook frontend and kernel are optional and are not installed by the core requirements.

## Validation and limitations

The current test suite passes **11 checks**:

- Numerical agreement with selected unchanged upstream methods at all five alpha levels.
- Lag construction matches upstream and excludes the current target.
- Changing current or future outcomes cannot change intervals already issued.
- The rolling window removes old errors correctly.
- Metric arithmetic handles misses, inclusive boundaries, and invalid bounds.
- Repeated fits are deterministic without changing NumPy's global random state.

Run them with `python -m pytest` using the project environment. Python may emit `SyntaxWarning` messages for a legacy escape sequence in the unchanged upstream source; the tests still pass.

The results apply to one year, one location, one forecast horizon, and the selected random-forest implementation. Repeated seeds reuse the same temporal observations, so their standard deviations do not measure generalization to new years or cities. Overall coverage also does not guarantee coverage at every hour.

Modern library versions can produce small differences from the authors' historical results. Tests establish parity for the selected code path in the installed environment; they do not reproduce the entire paper or prove its theoretical assumptions for this dataset. Neural-network and ARIMA experiments, longer forecast horizons, and retail demand have not been evaluated here.

## Files and documentation

```text
configs/                  Smoke and full reproduction configurations
data/raw/                 Original Solar_Atl CSV
docs/                     Learning guide, data dictionary, findings, and plan
notebooks/                Walkthrough of saved reproduction results
outputs/
  solar_reproduction/     Full results, four PNG plots, and 50 prediction files
  solar_smoke/            One-seed results and plots
  test-results.xml        Saved test report
references/               Citation, source manifest, paper, and upstream snapshot
scripts/                  Source downloader, experiment runner, guide builders
src/enbpi_project/
  data.py                 Validated loading and chronological lag features
  model.py                Bootstrap forests and sequential interval updates
  metrics.py              Coverage, width, interval score, and MAE
tests/                    Upstream parity and forecast-timing checks
requirements.txt          Direct dependencies
requirements-lock.txt     Versions from the tested environment
THIRD_PARTY.md            Attribution and third-party notices
```

Each run provides an audit trail:

| Artifact | Contents |
| --- | --- |
| `report.md` | Generated results and diagnostic figures |
| `summary.csv` | Mean metrics and coverage/width standard deviations across seeds |
| `metrics_by_trial.csv` | Metrics by method, seed, and alpha; out-of-bag diagnostics |
| `upstream_comparison.csv` | Local and author averages with explicit differences |
| `hourly_coverage.csv` / `hourly_coverage_by_trial.csv` | Coverage by hour, aggregated and per seed |
| `predictions/seed_<seed>_alpha_<alpha>.csv.gz` | EnbPI predictions: `timestamp`, `actual`, `center`, `lower`, `upper`, `covered` |
| `config.json` | Exact settings used for the run |
| `run_metadata.json` | Package versions, source commit, code hashes, counts, dates, and timing |

For example, inspect one saved prediction file from the repository root:

```python
import pandas as pd

predictions = pd.read_csv(
    "outputs/solar_reproduction/predictions/seed_98765_alpha_0.10.csv.gz",
    parse_dates=["timestamp"],
)
print(predictions.head())
print(f"Observed coverage: {predictions['covered'].mean():.2%}")
```

The solar CSV, selected upstream sources, and saved experiment outputs are tracked. The virtual environment, caches, and downloaded paper PDF are excluded by [.gitignore](.gitignore).

| Read next | Purpose |
| --- | --- |
| [Learning guide](docs/learning-guide.md) | Build intuition for EnbPI and the evaluation metrics |
| [Reproduction notes](docs/reproduction-notes.md) | Inspect preserved behavior and compatibility changes |
| [Data dictionary](docs/data-dictionary.md) | Understand input fields and generated files |
| [Findings and next step](docs/findings-and-next-step.md) | Interpret the evidence and planned extension |
| [Experiment plan](docs/experiment-plan.md) | Review the research scope and evaluation protocol |
| [Results notebook](notebooks/01_explore_reproduction.ipynb) | Explore the saved outputs interactively |

## Retail demand roadmap

The next research question is whether useful aggregate coverage can hide unreliable intervals for particular products or sales patterns.

- [x] Reproduce the selected solar experiment across ten seeds and five coverage targets.
- [x] Compare against saved author results and validate chronological prediction timing.
- [x] Save predictions, metrics, provenance, and hourly/rolling diagnostics.
- [ ] Verify access and usage terms for a small M5 retail-sales subset.
- [ ] Select products using training-period information and define separate training, development, and final test periods.
- [ ] Evaluate next-day sales forecasts with daily feedback against seasonal-naive and simple residual-interval baselines.
- [ ] Report coverage by product and sales pattern, interval width, interval score, and point-forecast error.
- [ ] Build a retail forecast dashboard after evaluation.

Retail results, inventory-cost simulations, and a retail dashboard are not implemented. Sales can understate demand during stockouts; studying unconstrained demand would require additional inventory evidence.

## Research source and attribution

Chen Xu and Yao Xie. **Conformal prediction interval for dynamic time-series.** Proceedings of the 38th International Conference on Machine Learning, PMLR 139:11559–11569, 2021.

- [Paper and publication record](https://proceedings.mlr.press/v139/xu21h.html)
- [Authors' implementation](https://github.com/hamrel-cxu/EnbPI)
- [BibTeX citation](references/paper.bib)
- [Source URLs and SHA-256 checksums](references/source-manifest.json)

Upstream is pinned to commit **`60cd5b7530eb954b02ae94da967111f5b5c3c01b`**, the conference implementation. The original [MIT license](references/upstream/LICENSE) is retained with the selected unchanged source files; it should not be treated as a blanket license for the external dataset or paper.

The numerical core adapts the authors' work. Local contributions include the focused runner, explicit forecast/update interface, validation tests, comparisons, diagnostics, and educational documentation, prepared with coding-assistant support. See [third-party attribution](THIRD_PARTY.md) for the source notices.
