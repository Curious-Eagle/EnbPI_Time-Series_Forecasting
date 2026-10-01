# Attribution and third-party materials

## EnbPI implementation

The scientific method and adapted numerical implementation originate from:

Chen Xu and Yao Xie. **Conformal prediction interval for dynamic time-series.** Proceedings of the 38th International Conference on Machine Learning, PMLR 139:11559-11569, 2021.

- Paper: https://proceedings.mlr.press/v139/xu21h.html
- Code: https://github.com/hamrel-cxu/EnbPI
- Pinned commit: `60cd5b7530eb954b02ae94da967111f5b5c3c01b`
- Original copyright: Copyright (c) 2021 cx971111
- License: MIT; the complete unchanged notice is retained in `references/upstream/LICENSE`.

`src/enbpi_project/model.py` adapts the original numerical procedure. Changes are documented in `docs/reproduction-notes.md`. Selected original files are retained unchanged for inspection and parity tests. The authors are not represented as endorsing this portfolio project.

## Dataset, paper, and saved author results

Source URLs and checksums are listed in `references/source-manifest.json`. The local paper is provided for study and is not relicensed as project code. The source dataset identifies NSRDB as its origin. The project downloads it through the authors' repository; raw data and the PDF are excluded from Git by default. Original result CSVs are retained with the upstream attribution.

## Local contributions

The focused experiment runner, explicit feedback interface, parity/leakage checks, result comparisons, diagnostic analyses, plots, and explanatory documents were prepared for this project with coding-assistant support. Describe the published method as a reproduction and distinguish it from the subsequent retail extension in portfolio materials.
