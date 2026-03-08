# DM paper run deliverable (IO/closure)

Goal: provide a single-command, deterministic DM run that writes a small set of reproducible artifacts under `out/`, with explicit provenance telemetry.

This is a **paper-facing ergonomics** deliverable (IO closure + schema stability), **not** an accuracy/fit claim.

## One-command run

From repo root:

```powershell
python .\run_dm_paper_run.py
```

Windows wrapper:

```powershell
.\run_dm_paper_run.ps1
```

## What it runs

`run_dm_paper_run.py` runs two deterministic sub-runs on repo-hosted SPARC points:

1) Thread + STIFFGATE (explicit calibration branch) via `dm_holdout_cv_thread_STIFFGATE.py`
2) `env_model=none` branch via `dm_holdout_cv_thread.py`

Both runs are **scan-free** by default (fixed `A` and `alpha`), matching the Codex canonical command pattern.

## Artifacts

Default output directory: `out/dm_paper/`

- `dm_cv_thread_STIFFGATE_fixed.csv`
- `dm_cv_thread_STIFFGATE_summary.json`
- `dm_cv_none_fixed.csv`
- `dm_cv_none_summary.json`
- `paper_run_report.md`

## Evidence test

This deliverable is exercised and locked by:

```powershell
python -m pytest -q integration_artifacts\mastereq\tests\test_e2e_dm_paper_run_mode.py
```

The e2e test asserts:
- deterministic artifact creation
- JSON provenance telemetry (`data_loaded_from_paths`, resolved `points_csv`)
- explicit branch coverage (STIFFGATE calibration used; `env_model=none` run)
- framing lock (`stability_not_accuracy: true`)
