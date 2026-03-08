# Why MS is included (prereg gate + dynamics-integrity audit)

MS has an explicit prereg verdict gate (Layer A) plus an explicit dynamics-integrity audit layer (Layer B).

This is **Integrity_OK/Closure_OK** evidence: the prereg gate is evaluated on a paper-safe observable (`raw_ppm`), and dynamics outputs are recorded as audit artifacts. It is not a blanket claim of physics-fit quality.

## Evidence artifacts (paper-safe strict runs)
Two strict runs are included (both paper-safe: prereg observable is locked to `raw_ppm`):
- `../RESULTS/real_cyto_3arm_strict_raw_common_20260304/`
- `../RESULTS/real_cyto_3arm_strict_raw_common_resid_20260304/`

### Layer A: prereg gate PASS (locked)
Within each run, for each ablation (`internal_only`, `full`) the finalizer writes:
- `*/final/prereg_lock_and_final_verdict_goodppm3.json` with `final_verdict == "PASS"`
- `*/final/FINAL_VERDICT_REPORT_goodppm3.md` human-readable report

### Layer B: dynamics integrity (audit-only)
Each strict run includes top-level rollups:
- `DYNAMICS_INTEGRITY_SUMMARY.json`
- `DYNAMICS_INTEGRITY_SUMMARY.md`

These summarize per arm that:
- audit + telemetry files exist for every arm (`with_audit == 6`, `with_telemetry == 6`)
- `stateful_steps_total > 0` in `internal_only`/`full` (dynamics actually ran)
- the prereg verdict remains PASS (observable not altered)

## Runner + command provenance
- Strict runner: `../CODE/ms_particle_specific_dynamic_runner_v1_0_DROPIN.py`
- 3-arm driver: `../CODE/run_ms_particle_specific_dynamic_3arm_v1_0.py`
- Finalizer: `../CODE/runners/particle_specific_finalize_from_runs_v1_0_DROPIN/`
- Aggregator: `../CODE/ms_dynamics_integrity_aggregate_v1_DROPIN.py`

## Inputs used
- Real points CSVs are bundled under `../INPUTS/MS/` (copied from `out/particle_specific_cytofull_*`).

## Context baseline
- A legacy baseline run is included under `../RESULTS/real_cyto_3arm_legacy_20260304/`.
