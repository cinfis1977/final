# Entanglement + Photon paper-faithful reproduction report

## Scope boundary

This report records the **paper-faithful** layer only.
It covers validated bridge/audit execution and declared-math equivalence.
It does **not** upgrade entanglement or photon to a full first-principles derivation claim.

## Entanglement paper runner

- runner: `run_entanglement_nist_run4_chsh_audit_paper_v1.py`
- input: `integration_artifacts/entanglement_photon_bridge/nist_run4_coincidences.csv`
- outputs:
  - `out/entanglement_paper/nist_run4_chsh_audit_paper_v1_summary.json`
  - `out/entanglement_paper/nist_run4_chsh_audit_paper_v1_report.md`

### Observables

- `S_signed = 2.455041357825164`
- `S_abs = 2.455041357825164`
- `null_pvalue_S_abs = 0.0` using 20000 locked null shuffles

### Setting-pair correlators

- `E00 = 0.9992063492063492`
- `E01 = 0.998250079541839`
- `E10 = 0.9972075705864102`
- `E11 = 0.539622641509434`

### Claim boundary

- Validated Bell benchmark / audit path.
- No fit or retuning performed.
- No full dynamic Bell-derivation claim.

## Photon paper runner

- runner: `run_photon_birefringence_prereg_paper_v1.py`
- input template: `integration_artifacts/entanglement_photon_bridge/birefringence_holdouts_v1_TEMPLATE.csv`
- outputs:
  - `out/photon_paper/photon_birefringence_prereg_paper_v1_summary.json`
  - `out/photon_paper/photon_birefringence_prereg_paper_v1_report.md`

### Locked formula checks

- CMB locked check `z_score = -1.072813174987442`
- accumulation locked check `z_score = -0.48924007368267536`
- locked cosmology:
  - `Om = 0.315`
  - `Ol = 0.685`
  - `Or = 0.0`

### Canonical paper reference p-values

- signed p-value `≈ 0.3603`
- absolute-metric p-value `≈ 0.3936`
- sky-fold p-value `≈ 0.1536`

### Transparency note

The current snapshot now contains a standalone sky-fold runner:

- `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`

However, the repo still does not expose a larger canonical sky-coordinate source table for default local reproduction of the paper sky-fold value. The wrapper therefore keeps the paper sky-fold value as the canonical benchmark and only performs a local recomputation when an explicit `--skyfold_csv` source table is supplied.

Additional provenance note:

- a follow-up search across this repo and the sibling repo `C:/Dropbox/projects/new_master_equation_with_gauge_structure_test` located an external quasar/jet matched table suitable for local sky-fold recomputation
- that search did **not** recover an exact paper-canonical sky-fold source file or an archived fold-rule implementation directly tied to the paper benchmark `≈ 0.1536`
- a dedicated external diagnostic scan is now recorded in `out/photon_paper/photon_skyfold_provenance_diagnostic_v1.md`; its closest match is an **RA hemisphere** split with `p_value_abs = 0.1544`, numerically close to the paper benchmark but still not canonical evidence
- therefore the paper sky-fold value remains a benchmark citation, while local recomputations remain explicitly labeled as external/local extensions

Current workspace fixation note:

- for current workspace use, the fixed sky-fold runner is `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`
- performance-phase handoff is recorded in `ENT_PHOTON_PERFORMANCE_TRANSITION.md`

## Equivalence gates

See `ENT_PHOTON_EQUIV_PASSLOG.txt`.

- entanglement equivalence: PASS
- photon equivalence: PASS

## Acceptance summary

- canonical anchor inventory: complete
- paper-faithful entanglement wrapper: complete
- paper-faithful photon wrapper: complete
- equivalence gates: PASS
- claim boundary preserved: yes
- performance transition prepared: yes
