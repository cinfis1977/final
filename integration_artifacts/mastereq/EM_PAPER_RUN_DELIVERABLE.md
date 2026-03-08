# EM paper run deliverable (single-command, deterministic artifacts)

This deliverable packages the EM real-data forward harnesses into a **paper-facing reproducibility run**:

- One command runs both EM channels (Bhabha and mu+mu-)
- Deterministic outputs under `out/em_paper/`
- JSON telemetry records IO provenance (resolved paths) + covariance choice + framing
- An end-to-end test locks artifact existence + schema smoke + provenance flags

This is **reproducibility/closure evidence** for the declared proxy models.
It is **not** a claim of physical accuracy.

## One-command run

Python driver:

- `run_em_paper_run.py`

Windows wrapper:

- `run_em_paper_run.ps1`

PowerShell (repo root):

```powershell
.\.venv\Scripts\python.exe run_em_paper_run.py --shape_only --freeze_betas --beta_nonneg --require_positive
# or
.\run_em_paper_run.ps1 -ShapeOnly -FreezeBetas -BetaNonneg -RequirePositive
```

## Deterministic output tree

- `out/em_paper/bhabha_pred.csv`
- `out/em_paper/bhabha_summary.json`
- `out/em_paper/bhabha_import_pred.csv`
- `out/em_paper/bhabha_import_summary.json`
- `out/em_paper/mumu_pred.csv`
- `out/em_paper/mumu_summary.json`
- `out/em_paper/paper_run_report.md`

The `bhabha_import_*` artifacts are produced by an explicit second Bhabha sub-run
that exercises the `--baseline_csv` import branch (baseline curve read from a
separate CSV path, then normalized per inferred group).

## Packs and data artifacts

- Packs:
  - `lep_bhabha_pack.json`
  - `lep_mumu_pack.json`

- Explicit baseline-import artifact (used only to exercise the import branch; not an accuracy claim):
  - `integration_artifacts/mastereq/packs/em_paper/bhabha_baseline_import.csv`

- CSV artifacts referenced by packs:
  - `lep_bhabha_table18_clean.csv` + covariance CSVs
  - `lep_mumu_table13_clean.csv` + covariance CSVs

## Automated evidence

End-to-end lock:

- `integration_artifacts/mastereq/tests/test_e2e_em_paper_run_mode.py`

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q integration_artifacts/mastereq/tests/test_e2e_em_paper_run_mode.py
```
