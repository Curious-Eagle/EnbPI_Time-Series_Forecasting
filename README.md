# Retail Demand Forecasting with EnbPI

A research-reproduction portfolio project: first verify the ICML 2021 EnbPI method on the authors' solar dataset, then investigate retail sales uncertainty.

**Status:** The lag-only random-forest subset of Figure 1 has been run at five coverage targets across ten seeds. At a 90% target, mean coverage was **90.24%**, compared with **90.25%** in the authors' saved results. All **11 validation checks passed**. The retail extension is planned and has not been evaluated.

## Start here

- [Complete beginner guide with formulas and worked examples](docs/Understanding_the_EnbPI_Project.docx)
- [Computed reproduction report](outputs/solar_reproduction/report.md)
- [Beginner learning guide](docs/learning-guide.md)
- [Results walkthrough notebook](notebooks/01_explore_reproduction.ipynb)
- [Implementation decisions and limitations](docs/reproduction-notes.md)
- [Data and output dictionary](docs/data-dictionary.md)
- [Experiment plan](docs/experiment-plan.md)

![Coverage and width comparison](outputs/solar_reproduction/coverage_width.png)

## Run on this computer

The isolated environment is already in `.venv`. From this project directory in PowerShell:

```powershell
# Validate against selected original methods and check prediction timing.
.\.venv\Scripts\python.exe -m pytest --junitxml=outputs/test-results.xml

# One seed, 90% nominal coverage.
.\.venv\Scripts\python.exe scripts/run_experiment.py --config configs/smoke.json

# Ten seeds, five nominal coverage levels (75% through 95%).
.\.venv\Scripts\python.exe scripts/run_experiment.py --config configs/reproduction.json
```

No account, GPU, or paid API is needed for this solar experiment. After dependencies and research files are downloaded, runs work offline. Re-running a named configuration replaces that run's generated outputs.

## Set up on another computer

Use Python 3.12. On Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe scripts/fetch_sources.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts/run_experiment.py --config configs/reproduction.json
```

On macOS/Linux use `python3.12 -m venv .venv` and `.venv/bin/python` for the remaining commands. The saved lock file records the tested Windows environment; other platforms have not been verified. `requirements.txt` lists direct dependencies and `requirements-lock.txt` records installed versions.

The optional notebook reads generated results. Open it in an existing Jupyter or VS Code notebook environment using this project's Python interpreter. A notebook frontend/kernel is not installed by the core requirements and is not needed for the experiments.

## Folder map

```text
configs/           Smoke and full selected-experiment settings
data/raw/          Original solar data, retained locally
docs/              Plan, learning guide, data dictionary, compatibility notes
notebooks/         Guided exploration of saved results
outputs/           Reports, PNG charts, metrics, predictions, test report
references/        Paper PDF, citation, source manifest, unchanged author files
scripts/           Source download, experiment runner, notebook generator
src/enbpi_project/ Adapted model, chronological data preparation, metrics
tests/             Original-code parity and future-data leakage checks
.venv/             Isolated Python environment
```

All project artifacts are contained in this folder. Environment files, caches, raw data, and the paper PDF are excluded from Git by default; the download script restores research inputs. See [third-party attribution](THIRD_PARTY.md).

## Research question

Can sequential prediction intervals achieve useful observed coverage without becoming unnecessarily wide, and how does performance differ across retail sales patterns?

## Research foundation

- [Paper: Conformal prediction interval for dynamic time-series](https://proceedings.mlr.press/v139/xu21h.html)
- [Paper PDF](https://proceedings.mlr.press/v139/xu21h/xu21h.pdf)
- [Authors' code](https://github.com/hamrel-cxu/EnbPI)

EnbPI combines bootstrap predictions with prediction-error information to construct sequential intervals. Its theoretical coverage is approximate under specified assumptions; a nominal 90% interval is not a promise for every product or date.

## Milestones

1. Completed: explain the algorithm and reproduce a restricted original experiment.
2. Completed: record differences from the original results and compatibility changes.
3. Apply the method to a small, preselected retail dataset subset.
4. Compare coverage, interval width, and point-forecast accuracy.
5. Publish a reproducible repository and a concise report with a forecast dashboard.

The original-data experiment and retail extension will be reported separately. See [the experiment plan](docs/experiment-plan.md) for the initial scope.

## Attribution

Xu, Chen, and Yao Xie. 2021. Conformal prediction interval for dynamic time-series. Proceedings of the 38th International Conference on Machine Learning, PMLR 139:11559–11569.

Pinned upstream commit: `60cd5b7530eb954b02ae94da967111f5b5c3c01b`. The complete [original MIT notice](references/upstream/LICENSE) is retained alongside unchanged source files.

The numerical core adapts the authors' implementation. Local contributions include a focused runner, explicit forecast/update separation, validation tests, result comparisons, diagnostics, and educational documentation. Coding-assistant support was used; understanding and explaining the work remains part of preparing this portfolio project.
