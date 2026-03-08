# Entanglement + Photon final audit note

## Executive status

This note closes the current Entanglement/Photon implementation pass under the required discipline:

- **no fitting**
- **no tuning against target outcomes**
- **paper-faithful claims kept separate from NEW WORK**
- **bridge/audit results never upgraded into unsupported derivation claims**

## Layer 1 — paper-faithful

### Entanglement

Validated artifacts:
- `run_entanglement_nist_run4_chsh_audit_paper_v1.py`
- `out/entanglement_paper/nist_run4_chsh_audit_paper_v1_summary.json`
- `out/entanglement_paper/nist_run4_chsh_audit_paper_v1_report.md`
- `integration_artifacts/mastereq/tests/test_equivalence_entanglement_runner.py`

Locked result summary:
- canonical input: `integration_artifacts/entanglement_photon_bridge/nist_run4_coincidences.csv`
- `S_abs = 2.455041357825164`
- null shuffle benchmark recorded with no fit

Claim boundary:
- This is a validated CHSH/Bell audit path.
- It does **not** claim a first-principles dynamic derivation of Bell correlations.

### Photon

Validated artifacts:
- `run_photon_birefringence_prereg_paper_v1.py`
- `out/photon_paper/photon_birefringence_prereg_paper_v1_summary.json`
- `out/photon_paper/photon_birefringence_prereg_paper_v1_report.md`
- `integration_artifacts/mastereq/tests/test_equivalence_photon_birefringence_runner.py`
- `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`
- `integration_artifacts/mastereq/tests/test_equivalence_photon_birefringence_skyfold_runner.py`

Locked result summary:
- bridge cosmology fixed at `Om=0.315`, `Ol=0.685`, `Or=0.0`
- paper reference p-values retained as canonical:
  - signed `≈ 0.3603`
  - absolute `≈ 0.3936`
  - sky-fold `≈ 0.1536`

Claim boundary:
- This is a bridge observable / falsifier layer.
- It does **not** claim a unique microscopic derivation.

## Layer 2 — NEW WORK dynamic extension

### Entanglement dynamic correlator attempt

Artifacts:
- `entanglement_full_dynamic_runner_v1.py`
- `CODE/entanglement_dynamic_full_runner_v1.py`
- `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.summary.json`
- `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.state_audit.json`
- `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.telemetry.json`
- `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.report.md`

Locked result summary:
- `S_obs = 2.455041357825164`
- `S_model_abs = 1.2739057644500655`
- `|ΔS_abs| = 1.1811355933750987`

Audit status:
- named state variables explicitly recorded
- no-fit condition preserved
- gamma-map coefficients remain locked
- telemetry distinguishes dynamic inputs from audit-only variables

### Photon dynamic modulation attempt

Artifacts:
- `photon_full_dynamic_runner_v1.py`
- `CODE/photon_dynamic_full_runner_v1.py`
- `out/photon_dynamic_full/photon_fullmodel_locked_v1.summary.json`
- `out/photon_dynamic_full/photon_fullmodel_locked_v1.state_audit.json`
- `out/photon_dynamic_full/photon_fullmodel_locked_v1.telemetry.json`
- `out/photon_dynamic_full/photon_fullmodel_locked_v1.report.md`

Locked result summary:
- baseline = `Bridge(beta_pred)`
- `chi2_bridge = 3.188499320541647`
- `chi2_model = 0.3958161449816739`
- `delta_chi2 = 2.7926831755599735`

Audit status:
- explicit chain recorded: `I(z) -> L_eff -> rho -> V_model -> beta_model`
- no-fit condition preserved
- dynamic modulation documented separately from paper-faithful bridge layer

## Sky-fold status split

There are now **two** sky-fold statuses and they must not be merged:

### A. Canonical paper benchmark
- canonical paper sky-fold p-value: `≈ 0.1536`
- remains the paper-facing benchmark

### B. External-data local recomputation
- source used: `C:/Dropbox/projects/new_master_equation_with_gauge_structure_test/out/quasar_jet_matches_v1.csv`
- local sky-fold recomputation written into:
  - `out/photon_paper/photon_birefringence_prereg_paper_v1_summary.json`
- current local result:
  - `p_value_signed = 0.01105`
  - `p_value_abs = 0.0217`

Interpretation:
- this is a valid no-fit external extension result
- it is **not automatically identical** to the paper’s canonical sky-fold chain
- sibling-repo provenance search found a reproducible **external** quasar/jet chain (`README_quasar_jet_birefringence_v1.md` + `out/quasar_jet_matches_v1.csv` in the sibling repo), but did **not** pin the paper’s exact canonical sky-fold source table / exact fold rule

## Equivalence / validation gates

Recorded in:
- `ENT_PHOTON_EQUIV_PASSLOG.txt`

Current gate status:
- entanglement equivalence: PASS
- photon birefringence equivalence: PASS
- photon sky-fold runner equivalence: PASS

## What is complete

Complete in this pass:
- anchor inventory
- paper-faithful entanglement wrapper
- paper-faithful photon wrapper
- dynamic wrapper exposure under requested stable names
- equivalence gates
- dynamic telemetry hardening
- claim-boundary documentation

## Remaining open item

There is **no remaining implementation blocker** for the current workspace path.

- current workspace provenance status: **pinned to the existing runner** `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`
- paper-historical provenance status for the benchmark `≈ 0.1536`: **not recoverable from accessible artifacts**

This is now a **historical-note item**, not an open implementation or source-chain task for the current workspace.

## Provenance search result

Completed search scope:
- current repo paper/docs/scripts
- current repo git history for photon/birefringence/quasar/skyfold filenames
- sibling repo `C:/Dropbox/projects/new_master_equation_with_gauge_structure_test`

What was found:
- a real-data quasar/jet accumulation chain in the sibling repo
- matched external table `out/quasar_jet_matches_v1.csv` with usable columns such as `qso_dec_deg` and `delta_wrap90_deg`
- the **current canonical workspace runner** for sky-fold recomputation:
  - `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`
- a new provenance diagnostic scan recorded in:
  - `integration_artifacts/entanglement_photon_bridge/diagnose_birefringence_skyfold_partitions_v1.py`
  - `out/photon_paper/photon_skyfold_provenance_diagnostic_v1.json`
  - `out/photon_paper/photon_skyfold_provenance_diagnostic_v1.md`
- older sibling paper drafts explicitly reference a **draft-only historical** sky-fold runner/output pair that was **not recovered**:
  - `run_prereg_birefringence_skyfold_v1_DROPIN_SELFCONTAINED_FIX.ps1`
  - `out/birefringence_skyfold_prereg_v1.csv`

Diagnostic result:
- on the external quasar/jet table, simple **RA hemisphere** partitions can yield null p-values numerically close to the paper benchmark
- closest local diagnostic match found so far: `p_value_abs = 0.1544` for `cos(qso_ra_deg - 164 deg) >= 0` with `metric = abs(delta_wrap90_deg)`
- this suggests the paper benchmark could plausibly correspond to a lost angular-partition rule, but this is still **not** canonical evidence

What was **not** found:
- an exact paper-canonical sky-fold source file
- an exact archived fold-rule implementation tied directly to the paper value `≈ 0.1536`
- any older committed sky-fold/quasar/photon artifact in this repo’s git history beyond the currently tracked accumulation/CMB bridge files
- the historical sibling-paper runner/output pair itself is not present in the accessible file trees or imported source inventory
- exact-name sweeps, text-reference sweeps, zip-entry sweeps, and broad path sweeps still did **not** recover the historical runner/output pair from accessible repo trees

Operational consequence:
- treat `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py` as the **current canonical workspace runner**
- keep `≈ 0.1536` as a paper benchmark only
- keep local sky-fold recomputation explicitly labeled as external/local unless a paper-historical artifact is ever recovered
- keep the PS1/CSV names as unrecovered draft references only, not as active target artifacts

## Final verdict for this implementation pass

- **Paper-faithful base:** complete
- **NEW WORK dynamic layer:** complete as exploratory falsifier surface
- **No-fit discipline:** preserved
- **Claim boundary discipline:** preserved
- **Current workspace canonical runner:** fixed and pinned
- **Audit/bridge execution status:** executed
- **Further paper-facing tests with current repo data:** not required
- **Todo for this pass:** complete
