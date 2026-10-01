# Initial experiment plan

**Progress:** Phase A is complete for the chosen lag-only random-forest subset: 10 seeds, five coverage levels, saved comparisons, and 11 passing checks. See `../outputs/solar_reproduction/report.md`. Phase B remains the next milestone; no retail results are claimed.

## A. Reproduction target

Use the ICML 2021 conference version and the upstream main branch, rather than mixing in the later journal implementation.

Start with the random-forest portion of the authors' Figure 1 experiment on Solar_Atl, using the lag-only formulation. This is a partial reproduction, not a reproduction of every figure or model.

The inspected upstream tests_paper.py specifies:

- Solar_Atl_data.csv with DHI as the response.
- Data size capped at 10,000; initial training fraction 20%.
- Lag depth 20; update stride 1; bootstrap count 30.
- Random forest: 10 trees, maximum depth 2, bootstrap disabled within each forest.
- Miscoverage levels 0.05 through 0.25 in increments of 0.05.
- Ten trials with seeds starting at 98765.

Source: https://raw.githubusercontent.com/hamrel-cxu/EnbPI/main/tests_paper.py

Completed preparation: data loader, transformations, and interval implementation inspected; upstream commit pinned; protocol checked against the conference PDF; prediction timing tested. The legacy forest criterion was renamed to `squared_error`. See `reproduction-notes.md` for the complete compatibility record.

Completed runs: a one-seed 90% smoke check and the selected multi-seed experiment. Comparisons use the matching upstream CSV; no values were inferred from figure pixels.

## B. Retail extension

Proposed dataset: a small M5 sales subset, subject to verifying access and terms. Define product selection using training-period information only. Include contrasting sales patterns without choosing products based on test performance.

Start with next-day forecasts updated after each day's actual sales arrive. This is different from forecasting an entire week before observing any of its outcomes. Add longer horizons only after defining an appropriate feedback schedule.

Use sales as the observed target. Sales may understate demand during stockouts; do not claim to estimate unconstrained demand without inventory evidence.

Use chronological training, development, and final test periods. Tune settings on development data only. Shift all sales-based features into the past; use future covariates only when known at the forecast origin.

Compare:

1. Seasonal-naive point predictions.
2. A selected tree model with a simple historical-residual interval baseline.
3. The same tree-model family with EnbPI intervals.

Keep forecast origin, target dates, and information availability consistent. Document differences in ensemble training between methods.

## C. Evaluation and artifacts

- Empirical coverage: fraction of actuals inside the intervals.
- Mean interval width, reported alongside coverage.
- Interval score: penalizes both excessive width and missed outcomes.
- MAE for point predictions.
- Coverage by product and over rolling time windows; report sample counts.

Save configuration, package versions, data provenance, seeds, per-date predictions, interval bounds, actuals, summary metrics, and plots. Report uncertainty across repeated seeds for the reproduction. Do not infer time-series sampling uncertainty from independent-row assumptions.

Completion requires runnable instructions, a reproduction comparison, a documented retail extension, and an honest limitations section. Results that disagree with the paper are findings to investigate, not values to adjust until they match.
