# DM-C2: Holdout/CV + leakage locks (real SPARC pack)

Goal
- Provide a WEAK/STRONG/EM-grade *evidence surface* for DM-C2 on real SPARC points:
  - deterministic artifacts under `out/`
  - explicit IO/provenance telemetry in JSON
  - galaxy-holdout k-fold CV (no point-level leakage)
  - train-only calibration of a single knob (`A_dm`) with test-set evaluation
  - diagonal error model via `sigma_v` (from SPARC `e_v_kms`)

This is **stability/closure, not accuracy**.

## What was added
- CV runner: `dm_holdout_cv_dynamics_c2.py`
  - Inputs: `dm_c2_pack_v1` JSON pack
  - Splits: deterministic galaxy-holdout k-fold by galaxy name + seed
  - Calibration: grid-search `A_dm` on TRAIN only; evaluate on TEST
  - Outputs: fold-level CSV + JSON summary including fold membership and leakage guards

- Paper-run driver: `run_dm_c2_cv_paper_run.py` (+ `run_dm_c2_cv_paper_run.ps1`)
  - Builds the SPARC-derived pack
  - Runs CV under `DM_POISON_PROXY_CALLS=1`
  - Writes stable artifacts under `out/dm_c2_cv_paper/`

- E2E lock: `integration_artifacts/mastereq/tests/test_e2e_dm_c2_holdout_cv_paper_run_mode.py`
  - Asserts determinism of folds and strict train/test disjointness
  - Asserts telemetry/framing fields and artifact presence

## Run commands
Build + run CV paper mode (Python):
- `C:/Dropbox/projects/new_master_equation_with_gauga_structure_test_git/.venv/Scripts/python.exe run_dm_c2_cv_paper_run.py --out_dir out\\dm_c2_cv_paper`

PowerShell wrapper:
- `powershell -File run_dm_c2_cv_paper_run.ps1`

Run the e2e lock:
- `C:/Dropbox/projects/new_master_equation_with_gauga_structure_test_git/.venv/Scripts/python.exe -m pytest -q integration_artifacts/mastereq/tests/test_e2e_dm_c2_holdout_cv_paper_run_mode.py`
