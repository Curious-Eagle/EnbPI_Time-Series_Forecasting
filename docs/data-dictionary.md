# Data and generated-file dictionary

## Source dataset

`data/raw/Solar_Atl_data.csv` is downloaded unchanged from the pinned author repository. The file identifies NSRDB as its source and Atlanta coordinates as 33.76, -84.39. It contains two metadata rows followed by the CSV header.

| Fields | Use |
| --- | --- |
| Year, Month, Day, Hour, Minute | Observation timestamp in the dataset's local standard time. |
| DHI | Diffuse horizontal irradiance, W/m²; the prediction target. |
| DNI and weather fields | Present in the original file but unused by this lag-only experiment. |

The loader verifies finite targets, unique ordered timestamps, and one-hour spacing. It does not silently interpolate or drop rows. The 10,000-row cap does not truncate this 8,760-row file.

The local timestamp is deliberately stored without a timezone conversion. Do not interpret it as UTC or apply daylight-saving changes without checking the source metadata.

## Prediction files

Each `outputs/<run>/predictions/seed_<seed>_alpha_<alpha>.csv.gz` contains:

| Column | Meaning |
| --- | --- |
| timestamp | Time of the target measurement. |
| actual | Observed DHI. Used for scoring and updates only after its interval is issued. |
| center | Conference EnbPI's alpha-dependent forecast center. |
| lower, upper | Prediction bounds in W/m². |
| covered | Whether lower <= actual <= upper. |

Pandas can read these compressed CSV files directly with `pd.read_csv(path)`.

## Results

- `metrics_by_trial.csv`: per-method, per-seed, per-alpha coverage, width, interval score, MAE, test count, and empty out-of-bag count.
- `summary.csv`: mean and standard deviation across seeds. A one-seed run has undefined standard deviations, saved as blank fields.
- `upstream_comparison.csv`: local means, authors' saved means, and differences. Coverage differences use percentage points; widths use W/m².
- `hourly_coverage_by_trial.csv`: 90%-nominal coverage at each hour for every seed.
- `hourly_coverage.csv`: hourly mean coverage, seed standard deviation, and observations per seed. Repeated seeds evaluate the same observations.
- `config.json`: exact experiment inputs.
- `run_metadata.json`: source commit, package versions, input counts, date range, execution timestamps, and local code hashes.

## Distribution

Raw data and the downloaded paper stay local by default through `.gitignore`. Code attribution is covered in `THIRD_PARTY.md`; the upstream code license is not assumed to grant blanket rights to all external data or the paper. Share the source URLs and download script with the repository.
