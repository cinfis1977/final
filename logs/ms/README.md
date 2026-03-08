# MS paper-safe strict evidence logs

Each run is a folder named by `run_id` under this directory.

## What’s in a run folder

- `RUN_INDEX.txt`: quick human index (run_id, drift mode, prereg observable, ablations, artifact copy paths)
- `cmd_01_run_driver/`
  - `command.txt`
  - `terminal_output_and_exit_code.txt`
- `cmd_02_aggregate/`
  - `command.txt`
  - `terminal_output_and_exit_code.txt`
- `artifacts/out_MS/`: a short-path copy of `out/MS/<run_id>/...` suitable for zipping/upload
  - `DYNAMICS_INTEGRITY_SUMMARY.{json,md}`
  - `internal_only/` and/or `full/` (depending on ablations), including `final/FINAL_VERDICT_REPORT_goodppm3.md`

## How these were produced

Script entrypoint:

- `run_ms_papersafe_strict_evidence_with_logs_v1.py`

Default behavior runs two drift telemetry modes in separate `run_id`s:

- `telemetry_only_commonbaseline`
- `telemetry_commonbaseline_plus_residual`

Prereg is locked to `raw_ppm` (paper-safe); dynamics are audit-only artifacts.
