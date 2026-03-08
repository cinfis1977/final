# Copilot inventory — Entanglement + Photon

## Scope split

- **Paper-faithful layer:** bridge / audit / equivalence artifacts already present in repo.
- **NEW WORK layer:** dynamic full-model runners already present in `CODE/` and will be exposed via stable wrapper names.

## Canonical anchors

### Entanglement

- **Equivalence test:** `integration_artifacts/mastereq/tests/test_equivalence_entanglement_runner.py`
  - Declared-math check for CHSH audit and microphysics wiring.
- **Bridge sector math:** `integration_artifacts/mastereq/entanglement_sector.py`
  - Deterministic sector hook for dephasing / visibility scaffolding.
- **Canonical evidence path (CSV):** `integration_artifacts/entanglement_photon_bridge/nist_run4_coincidences.csv`
- **HDF5 export helper:** `integration_artifacts/entanglement_photon_bridge/nist_hdf5_inspect_and_export_coinc_bridgeE0_v1_2_1_DROPIN.py`
- **Canonical audit runner:** `integration_artifacts/entanglement_photon_bridge/audit_nist_coinc_csv_bridgeE0_v1_DROPIN.py`
- **Paper claim boundary:** `paper/paper_final.md` §4.10 / claim-boundary notes near entanglement section.

### Photon

- **Equivalence test:** `integration_artifacts/mastereq/tests/test_equivalence_photon_birefringence_runner.py`
  - Declared-math check for locked CMB and accumulation prereg formulas plus microphysics wiring.
- **Bridge sector math:** `integration_artifacts/mastereq/photon_sector.py`
  - Locked FRW integral and birefringence helper formulas.
- **CMB prereg runner:** `integration_artifacts/entanglement_photon_bridge/prereg_cmb_birefringence_v1_DROPIN.py`
- **Accumulation prereg runner:** `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_accumulation_v1_DROPIN.py`
- **Sky-fold prereg runner:** `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`
- **Holdout template:** `integration_artifacts/entanglement_photon_bridge/birefringence_holdouts_v1_TEMPLATE.csv`
- **Current locked outputs:**
  - `integration_artifacts/out/entanglement_photon/cmb_birefringence_prereg_v1.csv`
  - `integration_artifacts/out/entanglement_photon/birefringence_accumulation_prereg_v1.csv`
- **Paper claim boundary:** `paper/paper_final.md` §4.11.

## EQUIVALENCE_CHECKS mapping

`integration_artifacts/EQUIVALENCE_CHECKS.md` records:

- entanglement/photon bridge equivalence tests,
- canonical bridge runner map,
- explicit non-claims that dissipative channels and microphysics templates are not yet physical-truth claims.

## Existing NEW WORK dynamic runners

- `CODE/entanglement_dynamic_full_runner_v1.py`
  - Existing dynamic entanglement runner with GKSL-based model-side `E_ab` / `S` prediction.
- `CODE/photon_dynamic_full_runner_v1.py`
  - Existing dynamic photon runner with `beta_model(z)=beta_bridge(z)*V_model(z)` construction.

## Gaps found in snapshot

- No root-level canonical wrappers with the requested names existed yet.
- A dedicated photon sky-fold runner has now been added, but the repo snapshot still lacks a larger canonical sky-coordinate source table to reproduce the paper sky-fold value locally by default.

## Section mapping

- **Entanglement / Bell benchmark:** paper §4.10
- **Photon birefringence bridge / prereg falsifier:** paper §4.11

## Status at inventory time

- Canonical paper-faithful anchors: **found**
- Equivalence tests: **present**
- Dynamic runners: **present but not yet exposed under requested stable names**
- Photon sky-fold code path: **present** as `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`

## Current handoff status

- stable wrappers: **present**
- current workspace sky-fold runner: **fixed**
- performance transition note: `ENT_PHOTON_PERFORMANCE_TRANSITION.md`
