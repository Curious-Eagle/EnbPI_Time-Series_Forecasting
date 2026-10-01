# Findings and the next experiment

## What has been established

The selected lag-only random-forest reproduction closely matches the authors' saved metrics across five nominal levels. At the 90% target:

| Metric | Local, ten-seed average | Authors' saved average |
| --- | --- | --- |
| Observed coverage | 90.24% | 90.25% |
| Mean interval width | 256.64 W/m² | 256.66 W/m² |

The dataset contains one year of hourly Atlanta solar irradiance. Each seed scores the same 7,008 test observations. See `../outputs/solar_reproduction/upstream_comparison.csv` for unrounded values.

## What the average hides

For nominal 90% intervals, coverage at local hour 12 averaged about 61.20% across seeds, whereas several nighttime hours had 100% coverage. Each hour has 292 evaluated observations per seed. These diagnostics concern the chosen lag-only setup and should not be equated with the paper's different multivariate or multi-step experiments.

Thus, the reproduction can match overall coverage while failing to provide uniformly useful intervals throughout the day. The experiment does not establish the cause of every miss. Changing the model or calibration policy would be a new experiment requiring a development set, not a correction to the original reproduction.

A frozen-error diagnostic obtained about 79.55% coverage at the 90% target. Its intervals were narrower, but it missed more outcomes. This illustrates why width alone is not a sufficient quality measure.

## Next milestone: retail extension

1. Verify access and usage terms for an M5 retail-sales subset.
2. Select a small set of products using training-period sales patterns only.
3. Define separate training, development, and final test periods.
4. Start with next-day sales predictions and daily feedback.
5. Compare seasonal-naive point forecasts, a simple interval baseline, and EnbPI.
6. Report coverage by product and demand regime alongside width and interval score.

Retail results, inventory-cost simulations, and a retail dashboard are not yet implemented. A potential portfolio contribution is evaluating whether overall coverage hides unreliable intervals for certain product groups, analogous to the hourly pattern observed here.

## Honest portfolio description for the completed milestone

Reproduced the univariate random-forest portion of an ICML 2021 time-series uncertainty experiment across 10 seeds and five coverage levels. Matched the authors' saved overall coverage closely, validated numerical parity and chronological prediction timing, and investigated hourly and rolling coverage failures. Adapted research code and documentation with coding-assistant support.
