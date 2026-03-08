# Why DM is included (integrity/closure + declared gate)

This bundle treats “PASS” as **pipeline closure + declared gate satisfied**, not a physical-accuracy claim.

## Evidence artifacts
- Paper report: `../RESULTS/dm_paper/paper_run_report.md`
- Thread+STIFFGATE summary: `../RESULTS/dm_paper/dm_cv_thread_STIFFGATE_summary.json`
- Env disabled summary: `../RESULTS/dm_paper/dm_cv_none_summary.json`

## What passed (declared criteria)
- The Codex/driver gate is: PASS iff **all folds have** $\Delta\chi^2_{test} > 0$.
- In `dm_cv_thread_STIFFGATE_summary.json`:
  - `telemetry.all_folds_delta_test_positive == true`
  - `telemetry.delta_chi2_test.min > 0` (evidence that every fold improved vs baseline)
  - `io.data_loaded_from_paths == true` (no hidden fallback inputs)
  - `telemetry.thread_calibration_used == true` (explicit calibration branch executed)
- In `dm_cv_none_summary.json`:
  - Same foldwise $\Delta\chi^2_{test} > 0$ structure for `env_model=none` (the scan-free “env disabled” control branch completes deterministically)

## Runner + command provenance
- Runner entrypoint: `../CODE/run_dm_paper_run.py`
- Underlying runners: `../CODE/dm_holdout_cv_thread_STIFFGATE.py`, `../CODE/dm_holdout_cv_thread.py`
- Canonical command forms are in: `../COMMANDS/CODEX_FINAL_RUN_COMMANDS.md` and `../COMMANDS/CODEX_FINAL_RUN_COMMANDS_v3.txt`
