# Understand the project before presenting it

## The question

A forecast is a best estimate of a future value. A prediction interval adds a range intended to contain future observations at a stated frequency. A useful interval must balance coverage and width: an extremely wide interval is easy to cover but may be unhelpful for decisions.

Our first experiment predicts solar irradiance one hour ahead from the previous 20 measurements. It verifies a published method on its original application. Retail demand comes afterward.

## The method in five steps

1. Draw 30 bootstrap samples from the training examples. A bootstrap sample selects rows with replacement, so some rows appear multiple times and others are absent.
2. Fit one small random forest to each sample.
3. For each training example, average predictions only from models whose bootstrap samples omitted that example. Compute its absolute prediction error.
4. Predict the next observation and construct an interval using the recent error distribution. The exact conference implementation uses a quantile of leave-one-out predictions as the center; it is not just the average of every forest.
5. After the actual observation arrives, calculate its error, remove the oldest error, and insert the new one. Repeat without refitting the forests.

This out-of-bag procedure avoids needing a separate held-out calibration set for the reproduction. It is not the same as giving the model access to future outcomes.

## Vocabulary

| Term | Meaning in this project |
| --- | --- |
| Alpha | Desired miss rate; alpha 0.1 corresponds to 90% nominal coverage. |
| Empirical coverage | Fraction of evaluated outcomes inside the predicted bounds. |
| Mean width | Average upper bound minus lower bound. |
| Interval score | Width plus a penalty for outcomes outside the bounds; lower is better for a fixed alpha. |
| MAE | Average absolute difference between the forecast center and actual outcome. |
| Residual | Difference between an observed and predicted value; calibration here uses its absolute value. |
| Lag | A past measurement used as a feature. |
| Seed | A number controlling randomized sampling so a run can be repeated. |
| Marginal coverage | Coverage averaged over the evaluated distribution. |
| Conditional coverage | Coverage within a subgroup or at a particular input; it does not automatically follow from marginal coverage. |

## How to read the results

Start with `outputs/solar_reproduction/report.md`. Compare local and upstream coverage first, then examine the width needed to obtain it. Look at coverage by hour: a satisfactory overall percentage can hide systematic misses at particular times.

The shaded forecast chart shows prediction intervals for future observations, not confidence intervals around an estimated mean. The 10 seeds describe sensitivity to bootstrap randomness on the same series. They are not 10 independent years of data.

## What you should be able to explain in an interview

- Why random train/test splitting would make a forecasting evaluation unrealistic.
- Why a model can have good point accuracy but unreliable uncertainty intervals.
- Why increasing coverage usually increases width.
- How the implementation prevents the current target from influencing its own interval.
- What was taken from the paper, what was adapted, and what is your additional analysis.
- What the experiment does not show, particularly performance on future years and retail data.

## Suggested reading order

Read the paper's abstract and introduction, then Algorithm 1, Section 5.1, and Figure 1. Run the smoke experiment and inspect its charts. Read `src/enbpi_project/model.py` alongside `docs/reproduction-notes.md`. Return to the theoretical assumptions after you can explain the empirical pipeline.

Paper: https://proceedings.mlr.press/v139/xu21h.html

Original implementation: https://github.com/hamrel-cxu/EnbPI
