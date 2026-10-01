# Reproduction decisions and compatibility notes

## Scope and provenance

Target: Figure 1, univariate random-forest component of Xu and Xie, ICML 2021. The original data are solar irradiance, not retail demand. The retail application is a subsequent extension.

Upstream commit: `60cd5b7530eb954b02ae94da967111f5b5c3c01b`, from the `main` conference branch. `references/source-manifest.json` records URLs, retrieval time, and SHA-256 hashes. `references/upstream/` preserves selected source files unchanged, including the MIT license and the authors' saved results.

The PDF's Section 5.1 describes 10 trials, 20% initial training, 30 bootstrap models, and immediate feedback. We inspected Algorithm 1 and Figure 1 visually. The Python script supplies the concrete lag depth and random-forest parameters. Reference metrics come from the matching upstream CSV, not digitized plot values.

## Exact details preserved

- Original ordering of all 8,760 hourly records; DHI target; first 1,752 raw observations for training.
- Lag depth 20 gives 1,732 effective training samples and 7,008 test samples. Previous test observations become available before subsequent forecasts.
- All bootstrap indices are drawn before fitting the first forest, using the legacy NumPy RandomState sequence.
- Each training residual uses predictions from bootstrap models that omitted that observation. No out-of-bag models means a zero prediction, matching upstream; the runner reports how often this occurs.
- For test inputs, compute a mean prediction for each leave-one-out model group, then select the order statistic at zero-based index `int((1-alpha)*n)`. The interval center therefore depends on alpha.
- Symmetric intervals use a moving window of `n` absolute residuals and NumPy's linear percentile calculation, with the upstream `int(100*(1-alpha))` percentile.
- Forecast first, observe the actual afterward, then update the error window. Negative bounds remain unchanged for comparability.

## Deliberate implementation changes

| Change | Reason and effect |
| --- | --- |
| `criterion='mse'` becomes `'squared_error'` | Current scikit-learn name for the same loss. |
| Single forest worker | Predictable resource use; no model parameter change. |
| Explicit shared RandomState | Matches the upstream random stream without modifying application-wide NumPy state. |
| Separate fitted forest objects | Upstream stores repeated references to a reused estimator but immediately saves predictions. We preserve those numerical predictions and retain distinct models for later prediction. |
| Chunked leave-one-out aggregation | Bounds temporary matrix size; tiny floating-point summation differences are possible. |
| Fit once per seed, reuse across alpha | Upstream resets its seed inside each run, so its bootstrap ensemble is the same across alpha values for this forest. |
| Explicit interval-then-observe interface | Makes the feedback order visible and testable; matches stride-one upstream windows. |
| Omit Keras, statsmodels, and anomaly detection imports | They are unrelated to this selected forest experiment. Unchanged upstream files remain available for inspection. |

## Validation design

Tests extract only the inspected bootstrap helper, lag transform, stride helper, and three EnbPI class methods from the pinned upstream files. This avoids running notebook-like experiment code or importing unrelated libraries. Their bodies are not modified.

For each of the five alpha levels, the adapted implementation must match those upstream methods in the same installed environment on a deterministic test series. Other checks perturb future targets, verify lag timing, verify moving-window eviction, and check interval-score arithmetic against known outcomes.

Passing those tests establishes parity for the tested path. It does not establish identical outputs across historical library versions, validate all upstream algorithms, or prove theoretical assumptions for the dataset. Saved author metrics are an external comparison; discrepancies must remain visible.

## Additional diagnostic

The frozen-residual comparison keeps the same alpha-specific forecast centers and the original training-error distribution throughout testing. It measures the effect of updating interval widths. It is not claimed as an original Figure 1 baseline or a tuned state-of-the-art competitor.

## Retail extension boundary

The chosen first experiment uses immediate hourly feedback. A retail version should initially use immediate daily feedback and next-day forecasts. Week-ahead inventory forecasts require a different information schedule. Sales are also not necessarily unconstrained demand: inventory shortages can hide lost demand.

The first extension should compare a seasonal-naive point forecast, a simple residual-interval baseline, and EnbPI on a preselected retail subset. Development and final-test periods must be separate. Aggregate coverage should be checked alongside product-specific and rolling coverage, interval widths, and interval scores.
