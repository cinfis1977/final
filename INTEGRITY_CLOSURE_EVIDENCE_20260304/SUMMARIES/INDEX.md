# Integrity/Closure Evidence Bundle (weak/strong/EM/DM/MS)

This folder is meant to be zipped and uploaded for third-party review.

Important terminology:
- **Integrity_OK / Closure_OK**: the declared pipeline runs end-to-end on declared inputs, with anti-fallback/telemetry/integrity guards producing the expected artifacts.
- **Performance_OK**: physics-fit quality (e.g., χ² thresholds, predictive accuracy). This bundle does **not** claim Performance_OK unless a sector has an explicit numeric gate.

## Quick map

### DM
- Results: `../RESULTS/dm_paper/`
- Paper report: `../RESULTS/dm_paper/paper_run_report.md`
- Key summaries:
  - `../RESULTS/dm_paper/dm_cv_thread_STIFFGATE_summary.json`
  - `../RESULTS/dm_paper/dm_cv_none_summary.json`
- Runner code: `../CODE/run_dm_paper_run.py` (+ underlying `dm_holdout_cv_thread*.py`)

### EM
- Results: `../RESULTS/em_paper/`
- Paper report: `../RESULTS/em_paper/paper_run_report.md`
- Key summaries:
  - `../RESULTS/em_paper/bhabha_summary.json`
  - `../RESULTS/em_paper/bhabha_import_summary.json`
  - `../RESULTS/em_paper/mumu_summary.json`
- Runner code: `../CODE/run_em_paper_run.py`

### STRONG
- Pack-ingestion paper run results: `../RESULTS/strong_c5a/` (report: `paper_run_report.md`)
- Scan artifacts (CSV/chi2 JSON): `../RESULTS/STRONG_SCAN/` and `../RESULTS/STRONG/`
- Runner code:
  - Pack-ingestion: `../CODE/run_strong_c5a_paper_run.py`, `../CODE/strong_amplitude_pack_hepdata_c4.py`
  - Scans: `../CODE/strong_sigma_tot_energy_scan_v2.py`, `../CODE/strong_rho_energy_scan_v3.py`

### WEAK
- Neutrino composite evidence CSV: `../RESULTS/WEAK/out_weak_t2k_oneforall.csv`
- Captured auxiliary CSVs: `../RESULTS/2026-03-03_run02/weak/`
- Runner code: `../CODE/score_nova_minos_t2k_penalty.py`, `../CODE/t2k_penalty_cli.py`, `../CODE/nova_mastereq_forward_kernel_BREATH_THREAD_v2.py`
- Profiles input: `../INPUTS/t2k_release_extract/t2k_frequentist_profiles.json`

### MS
- Strict paper-safe runs:
  - `../RESULTS/real_cyto_3arm_strict_raw_common_20260304/`
  - `../RESULTS/real_cyto_3arm_strict_raw_common_resid_20260304/`
- Legacy baseline run (context): `../RESULTS/real_cyto_3arm_legacy_20260304/`
- Dynamics integrity rollups:
  - `../RESULTS/real_cyto_3arm_strict_raw_common_20260304/DYNAMICS_INTEGRITY_SUMMARY.json`
  - `../RESULTS/real_cyto_3arm_strict_raw_common_resid_20260304/DYNAMICS_INTEGRITY_SUMMARY.json`
- Runner code: `../CODE/ms_particle_specific_dynamic_runner_v1_0_DROPIN.py`, `../CODE/run_ms_particle_specific_dynamic_3arm_v1_0.py`
- Finalizer: `../CODE/runners/particle_specific_finalize_from_runs_v1_0_DROPIN/`
- Inputs used (real points): `../INPUTS/MS/out/particle_specific_cytofull_*`

## Execution logs (command provenance)
- Consolidated logs + per-command stdout/stderr: `../RESULTS/pass_runs/`

## “Why included” notes (integrity/closure evidence)
- DM: `WHY_PASSED_DM.md`
- EM: `WHY_PASSED_EM.md`
- STRONG: `WHY_PASSED_STRONG.md`
- WEAK: `WHY_PASSED_WEAK.md`
- MS: `WHY_PASSED_MS.md`
