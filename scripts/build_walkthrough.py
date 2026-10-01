"""Create a notebook that explores saved results without training models."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def markdown(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": source.splitlines(keepends=True)}


cells = [
    markdown("# EnbPI: explore the reproduction\n\nThis notebook reads saved results; it does not train models. Run `scripts/run_experiment.py --config configs/reproduction.json` first. The experiment is the lag-only random-forest portion of Figure 1 in Xu and Xie (ICML 2021).\n\nThe original experiment uses solar irradiance. Retail demand is the next application, not a result already established here."),
    code("from pathlib import Path\nimport json\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\nroot = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'configs/reproduction.json').exists())\nresults = root / 'outputs/solar_reproduction'\nassert (results / 'summary.csv').exists(), 'Run the reproduction first.'\nprint('Project:', root)"),
    markdown("## 1. Check what was run\n\nThe 20 lag features use only preceding values. The 10 seeds repeat randomized training on the same time period."),
    code("metadata = json.loads((results / 'run_metadata.json').read_text())\nfor key in ['rows', 'train_raw', 'train_effective', 'test_rows', 'test_start', 'test_end', 'upstream_commit']:\n    print(f'{key}: {metadata[key]}')"),
    markdown("## 2. Compare with the authors\n\nCoverage is the fraction of observations within the interval. Compare width as well. Reference values come from the authors' saved CSV."),
    code("comparison = pd.read_csv(results / 'upstream_comparison.csv')\ncolumns = ['target_coverage', 'coverage_mean', 'upstream_coverage', 'coverage_difference_pp', 'width_mean', 'upstream_width']\nprint(comparison[columns].round(4).to_string(index=False))"),
    code("fig, ax = plt.subplots(figsize=(12, 5))\nax.imshow(plt.imread(results / 'coverage_width.png'))\nax.axis('off')\nplt.show()"),
    markdown("## 3. Inspect one seed at a 90% target\n\nEach interval is issued before its actual value is used to update the error window. A 90% nominal target is not a guarantee for each outcome."),
    code("predictions = pd.read_csv(results / 'predictions/seed_98765_alpha_0.10.csv.gz', parse_dates=['timestamp'])\ncovered = (predictions.actual >= predictions.lower) & (predictions.actual <= predictions.upper)\nprint(f'Observed coverage: {covered.mean():.2%}')\nprint(f'Mean width: {(predictions.upper - predictions.lower).mean():.2f} W/m²')\nprint(predictions.head().to_string(index=False))"),
    code("week = predictions.iloc[:168]\nfig, ax = plt.subplots(figsize=(12, 4))\nax.fill_between(week.timestamp, week.lower, week.upper, alpha=0.25, label='90% nominal interval')\nax.plot(week.timestamp, week.actual, color='black', label='Actual')\nax.plot(week.timestamp, week.center, label='Forecast center')\nax.set(ylabel='DHI (W/m²)', title='First seven test days')\nax.legend()\nfig.autofmt_xdate()\nplt.show()"),
    markdown("## 4. Look beyond the overall average\n\nOverall 90% coverage can hide systematic misses at particular hours. This table uses the first seed; the report also aggregates all ten seeds."),
    code("hourly = predictions.assign(hour=predictions.timestamp.dt.hour, hit=covered).groupby('hour').agg(coverage=('hit', 'mean'), observations=('hit', 'size'))\nprint(hourly.round(3).to_string())\nax = hourly.coverage.plot.bar(figsize=(12, 3), color='#0f766e')\nax.axhline(0.9, color='#b45309', linestyle='--')\nax.set(ylabel='Coverage', title='Coverage by local hour: first seed', ylim=(0, 1.05))\nplt.tight_layout()\nplt.show()"),
    markdown("## 5. Your interpretation\n\nWrite your answers here before presenting this project:\n\n1. How close are the local results to the authors' results?\n2. At which hours is coverage weakest?\n3. Why is the seed standard deviation not a confidence interval for a new year?\n4. What would change when forecasting daily retail sales?\n5. Which parts reproduce the paper and which are additional diagnostics?\n\nSources: [paper](https://proceedings.mlr.press/v139/xu21h.html), [author code](https://github.com/hamrel-cxu/EnbPI). See `docs/reproduction-notes.md` for differences."),
]

notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"}}, "cells": cells}
for i, cell in enumerate(cells):
    cell["id"] = f"walkthrough-{i:02d}"
target = ROOT / "notebooks/01_explore_reproduction.ipynb"
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(notebook, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(target)
