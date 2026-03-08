# Why EM is included (integrity/closure evidence)

This is **IO/closure + schema-stability** evidence: the runners ingest the declared packs/covariances, execute deterministically, and emit integrity telemetry (not a physics-fit claim).

## Evidence artifacts
- Paper report: `../RESULTS/em_paper/paper_run_report.md`
- Summaries:
  - `../RESULTS/em_paper/bhabha_summary.json`
  - `../RESULTS/em_paper/bhabha_import_summary.json`
  - `../RESULTS/em_paper/mumu_summary.json`

## What’s evidenced (concrete checks)
In the summary JSONs, the following are the key integrity/closure indicators:
- `io.data_loaded_from_paths == true` (pack/cov/data paths actually resolved)
- `integrity.no_nan_inf == true` (numerically finite pipeline)
- `integrity.require_positive_ok == true` (if positivity guard is enabled, it holds; otherwise this remains true by construction)
- `framing.stability_not_accuracy == true` (explicitly frames as closure/stability)

Additionally, the Bhabha run exercises both branches:
- normal pack baseline path (`bhabha_summary.json`)
- explicit baseline import path (`bhabha_import_summary.json` with `telemetry.baseline_import_used == true`)

## Runner + command provenance
- Runner entrypoint: `../CODE/run_em_paper_run.py`
- Underlying runners:
  - `../CODE/em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py`
  - `../CODE/em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py`
- Inputs copied under `../INPUTS/` include the HEPData-derived CSVs/covariances and the baseline-import CSV.
