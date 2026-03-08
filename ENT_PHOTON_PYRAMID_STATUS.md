# Entanglement + Photon pyramid status

## Base layer — paper-faithful

### Entanglement

Status: **validated evidence path**

Artifacts:
- `run_entanglement_nist_run4_chsh_audit_paper_v1.py`
- `out/entanglement_paper/nist_run4_chsh_audit_paper_v1_summary.json`
- `out/entanglement_paper/nist_run4_chsh_audit_paper_v1_report.md`
- `integration_artifacts/mastereq/tests/test_equivalence_entanglement_runner.py`

Current statement:
- Locked event processing + CHSH audit runs on the canonical NIST run4 coincidence CSV.
- This is a benchmark / bridge audit layer.
- It does **not** yet derive Bell correlations from full dynamics.

### Photon

Status: **validated bridge observable layer**

Artifacts:
- `run_photon_birefringence_prereg_paper_v1.py`
- `out/photon_paper/photon_birefringence_prereg_paper_v1_summary.json`
- `out/photon_paper/photon_birefringence_prereg_paper_v1_report.md`
- `integration_artifacts/mastereq/tests/test_equivalence_photon_birefringence_runner.py`

Current statement:
- Locked birefringence bridge formulas are reproduced with fixed FRW kernel.
- Paper reference p-values remain null-compatible.
- A standalone sky-fold prereg runner now exists for local recomputation when a sky-coordinate source table is supplied.
- A provenance search across this repo plus the sibling repo found only an **external** quasar/jet sky-coordinate chain, not the exact paper-canonical sky-fold source chain for `≈ 0.1536`.
- A dedicated provenance diagnostic now exists and shows that an external **RA hemisphere** partition on the quasar/jet table can reproduce a numerically close p-value (`≈ 0.1544`), but this remains non-canonical.
- This is a bridge/scaffolding layer, not a unique microphysical derivation claim.

## Middle / top layer — NEW WORK dynamic extension

### Entanglement dynamic correlator attempt

Status: **implemented as NEW WORK**

Artifacts:
- `entanglement_full_dynamic_runner_v1.py`
- `CODE/entanglement_dynamic_full_runner_v1.py`
- `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.summary.json`
- `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.state_audit.json`
- `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.telemetry.json`
- `out/entanglement_dynamic_full/nist_run4_fullmodel_locked_v1.report.md`

Locked run summary:
- `S_obs = 2.455041357825164`
- `S_model_abs = 1.2739057644500655`
- `|ΔS_abs| = 1.1811355933750987`

Interpretation:
- This is an exploratory falsifier surface.
- No fit or retune was used in the locked run.
- Result is recorded whether favorable or unfavorable.
- Named state-variable telemetry now records `alignment_lag`, `window_jitter`, `mismatch_load`, `coherence_floor`, and `rate_n` separately from the locked gamma map.

### Photon dynamic modulation attempt

Status: **implemented as NEW WORK**

Artifacts:
- `photon_full_dynamic_runner_v1.py`
- `CODE/photon_dynamic_full_runner_v1.py`
- `out/photon_dynamic_full/photon_fullmodel_locked_v1.summary.json`
- `out/photon_dynamic_full/photon_fullmodel_locked_v1.state_audit.json`
- `out/photon_dynamic_full/photon_fullmodel_locked_v1.telemetry.json`
- `out/photon_dynamic_full/photon_fullmodel_locked_v1.report.md`

Locked run summary:
- baseline = `Bridge(beta_pred)`
- `chi2_bridge = 3.188499320541647`
- `chi2_model = 0.3958161449816739`
- `delta_chi2 = 2.7926831755599735`

Interpretation:
- This is an exploratory extension layered on top of the paper bridge kernel.
- No fit or retune was used in the locked run.
- The dataset used here is the small repo-hosted template and should not be overclaimed as a final sector verdict.
- Per-source telemetry now records the explicit chain `I(z) -> L_eff -> rho -> V_model -> beta_model`.

## Gate summary

- Anchor inventory: complete
- Paper-faithful wrappers: complete
- Equivalence gates: PASS
- Dynamic wrappers under requested stable names: complete
- Claim boundary separation: preserved
- Final audit closure note: `ENT_PHOTON_FINAL_AUDIT_NOTE.md`
- Current photon sky-fold runner fixed: `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`
- Audit/bridge execution note: `ENT_PHOTON_PERFORMANCE_TRANSITION.md`

## Final wording discipline

- **Entanglement:** locked CHSH audit passes Bell benchmark; model-generated correlator is NEW WORK.
- **Photon:** bridge observable prereg layer is reproduced; dynamic modulation is exploratory NEW WORK.

## Transition state

- Current workspace closure: **complete**
- Audit/bridge execution status: **executed**
- Historical paper-artifact provenance for photon sky-fold: unresolved but non-blocking for current workspace use
- Additional paper-facing tests with new data: **not available in current snapshot**
- Recommended sector status for current paper pass: **closed**
