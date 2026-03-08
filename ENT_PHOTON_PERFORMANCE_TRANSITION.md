# Entanglement + Photon audit/bridge execution note

## Purpose

This note fixes the handoff from the completed **paper-faithful / closure** phase to any later **performance-oriented** phase.

It does **not** upgrade either sector into a stronger claim by itself.

## Phase-gate result

Audit/bridge execution status: **executed**

Reason:
- paper-faithful wrappers exist
- equivalence checks pass
- claim-boundary documentation is in place
- photon sky-fold current runner is fixed for workspace use
- remaining uncertainty is historical paper provenance only, not a current implementation blocker

## Fixed current runners

### Entanglement
- paper-faithful runner:
  - `run_entanglement_nist_run4_chsh_audit_paper_v1.py`
- NEW WORK dynamic runner:
  - `entanglement_full_dynamic_runner_v1.py`

### Photon
- paper-faithful runner:
  - `run_photon_birefringence_prereg_paper_v1.py`
- current sky-fold runner for workspace use:
  - `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`
- NEW WORK dynamic runner:
  - `photon_full_dynamic_runner_v1.py`

## Preconditions already satisfied

- deterministic bridge/equivalence coverage present under `integration_artifacts/mastereq/tests`
- entanglement paper outputs present under `out/entanglement_paper/`
- photon paper outputs present under `out/photon_paper/`
- dynamic telemetry/state-audit outputs present for both sectors
- provenance closure for current workspace use documented in `ENT_PHOTON_FINAL_AUDIT_NOTE.md`

## Executed performance outputs

### Entanglement
- executed locked dynamic run:
  - `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.summary.json`
  - `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.state_audit.json`
  - `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.telemetry.json`
  - `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.report.md`
- current locked comparison:
  - `S_obs = 2.455041357825164`
  - `S_model_abs = 1.2739057644500655`
  - `|ΔS_abs| = 1.1811355933750987`

### Photon
- executed locked dynamic run:
  - `out/photon_dynamic_full/photon_fullmodel_locked_v1.summary.json`
  - `out/photon_dynamic_full/photon_fullmodel_locked_v1.state_audit.json`
  - `out/photon_dynamic_full/photon_fullmodel_locked_v1.telemetry.json`
  - `out/photon_dynamic_full/photon_fullmodel_locked_v1.report.md`
- executed current sky-fold run:
  - `out/photon_paper/birefringence_skyfold_current_runner_v1.csv`
  - `out/photon_paper/birefringence_skyfold_current_runner_v1.json`
- current locked comparison:
  - `chi2_bridge = 3.188499320541647`
  - `chi2_model = 0.3958161449816739`
  - `delta_chi2 = 2.7926831755599735`
- current external/local sky-fold result:
  - `p_value_signed = 0.0114`
  - `p_value_abs = 0.02395`

### Validation
- post-run equivalence check:
  - `6 passed`

## What the execution phase was allowed to do

- compare dynamic outputs against bridge baselines
- summarize holdout or scorecard behavior
- record falsification-style wins or failures without retuning locked paper claims
- benchmark runtime, stability, telemetry completeness, and output reproducibility

## What the execution phase was not allowed to do

- rewrite paper-faithful benchmark values
- relabel external/local sky-fold recomputation as paper-canonical proof
- hide unfavorable dynamic results
- retro-fit parameters while still calling the run “locked” or “no-fit”

## Minimal checklist

- [x] Paper-faithful entanglement wrapper fixed
- [x] Paper-faithful photon wrapper fixed
- [x] Sky-fold current runner fixed
- [x] Equivalence gates passing
- [x] Claim-boundary note updated
- [x] Provenance closure docs updated
- [x] Performance handoff note created

## Executed outputs in this pass

### Entanglement
- compare paper CHSH audit summary against dynamic full-model summary
- keep `S_obs`, `S_model_abs`, and `|ΔS_abs|` explicit
- preserve telemetry fields as diagnostics, not fit knobs

### Photon
- compare bridge `chi2_bridge` against dynamic `chi2_model`
- report `delta_chi2` and per-source telemetry chain
- keep the paper sky-fold benchmark `≈ 0.1536` as citation only

## Final handoff statement

For the current workspace, the Entanglement + Photon audit/bridge execution has now been completed.
This is **not** a performance-pass verdict. It only means the paper-faithful and bridge/audit runs were executed, documented, and bounded correctly for the present paper pass.