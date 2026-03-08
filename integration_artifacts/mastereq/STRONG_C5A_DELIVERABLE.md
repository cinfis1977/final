# STRONG C5A deliverable (real-data reproduction packs)

C5A is the next step after C4 “paper-facing IO closure”.

Goal: **run the STRONG amplitude-core + C4 IO/χ² runner on real external CSV artifacts** via `paths`, under anti-fallback call-poison, and produce reproducible CSV+JSON outputs.

This is a **reproducibility/runbook** deliverable.
It is **not** a claim of physical accuracy or a fit/tune.

## What is included in this repo snapshot

- Real-data packs (paths-based):
  - `integration_artifacts/mastereq/packs/strong_c5a/pdg_sigma_tot_pack.json`
  - `integration_artifacts/mastereq/packs/strong_c5a/pdg_rho_pack.json`

- Data artifacts (already present in repo):
  - `data/hepdata/pdg_sigma_tot_clean_for_runner.csv`
  - `data/hepdata/pdg_rho_clean_for_runner.csv`

- Optional covariance artifact (derived, diagonal; used only to exercise the cov-path branch):
  - `integration_artifacts/mastereq/packs/strong_c5a/pdg_sigma_tot_cov_diag.csv`

- Evidence test (e2e smoke):
  - `integration_artifacts/mastereq/tests/test_e2e_strong_c5a_realdata_packs_smoke.py`

## Runbook (PowerShell)

From repo root:

```powershell
$env:STRONG_C4_POISON_PDG_CALLS = "1"

# PDG sigma_tot table (cov-path branch; covariance is a derived diagonal matrix)
.\.venv\Scripts\python.exe strong_amplitude_pack_hepdata_c4.py `
  --pack integration_artifacts/mastereq/packs/strong_c5a/pdg_sigma_tot_pack.json `
  --out_csv out/strong_c5a_pdg_sigma_tot.csv `
  --out_json out/strong_c5a_pdg_sigma_tot.json

# PDG rho table (diag-uncertainty branch)
.\.venv\Scripts\python.exe strong_amplitude_pack_hepdata_c4.py `
  --pack integration_artifacts/mastereq/packs/strong_c5a/pdg_rho_pack.json `
  --out_csv out/strong_c5a_pdg_rho.csv `
  --out_json out/strong_c5a_pdg_rho.json
```

## C5A.1 paper run mode (single command)

This mode packages the above as a single deterministic “paper run” that writes
canonical artifacts under `out/strong_c5a/`:

- `sigma_tot_pred.csv`, `sigma_tot_summary.json`
- `rho_pred.csv`, `rho_summary.json`
- `paper_run_report.md`

### PowerShell wrapper (recommended on Windows)

```powershell
./run_strong_c5a_paper_run.ps1
```

### Python entrypoint (cross-platform)

```powershell
$env:STRONG_C4_POISON_PDG_CALLS = "1"
.\.venv\Scripts\python.exe run_strong_c5a_paper_run.py
```

### Evidence test

```powershell
.\.venv\Scripts\python.exe -m pytest -q integration_artifacts/mastereq/tests/test_e2e_strong_c5a1_paper_run_mode.py
```

## What to expect in outputs (locks)

- `out/*.json` contains:
  - `io.data_loaded_from_paths=true` and resolved artifact paths
  - `anti_fallback.pdg_call_poison_active=true` when run with the env var
  - `amplitude_core_used=true` and `pdg_baseline_used=false`
  - `framing.stability_not_accuracy=true`

- `chi2.total` is expected to be finite.
  It is **not** expected to be small (no tuning; toy motor).
