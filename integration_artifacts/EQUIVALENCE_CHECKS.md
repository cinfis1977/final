# GKSL ↔ runner equivalence checks (current status)

This folder contains an **exact GKSL (Lindblad) reference** implementation under `integration_artifacts/mastereq/`.
The repo also contains sector-specific forward runners (WEAK/EM/STRONG/DM/…)
that often implement *approximations* (phase-shift kernels, baseline×modulation, etc).

This document records equivalence checks that explicitly relate a runner’s math to a GKSL evolution.

## What is checked today

Snapshot (this branch/session):
- Full suite: `python -m pytest -q integration_artifacts/mastereq/tests` → passes in this snapshot (see terminal/CI output).
- New bridge tests included:
   - `integration_artifacts/mastereq/tests/test_equivalence_entanglement_runner.py`
   - `integration_artifacts/mastereq/tests/test_equivalence_photon_birefringence_runner.py`

### Validation status (evidence)

What we can currently claim, backed by deterministic tests in this repo:

- Golden-output regeneration is tracked by the verdict golden harness reports:
   - `integration_artifacts/out/verdict_golden/RUN_SUMMARY.md`
   - `integration_artifacts/out/verdict_golden/RUN_SUMMARY.json`
   - Harness doc: `integration_artifacts/GOLDEN_HARNESS.md`

- **WEAK runner ↔ GKSL equivalence (unitary / phase-map):**
   - Mathematical convention mapping: `integration_artifacts/mastereq/tests/test_equivalence_weak_runner.py`
   - Golden-output per-bin phase-map equivalence: `integration_artifacts/mastereq/tests/test_equivalence_weak_golden_outputs.py`
   - End-to-end runner regeneration (runner+pack → CSV → golden): `integration_artifacts/mastereq/tests/test_e2e_weak_runner_regenerates_golden.py`
   - End-to-end GKSL-dynamics runner matches the same golden outputs (numerical tolerance):
     `integration_artifacts/mastereq/tests/test_e2e_weak_gksl_runner_matches_golden.py`
     (runner: `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py`)

- **WEAK 3-flavor dynamics integrity (not a golden/pipeline test):**
    - Positivity (ρ ⪰ 0), trace/Hermiticity, unitary purity limit, and vacuum CPT/T symmetry checks:
       `integration_artifacts/mastereq/tests/test_weak_3flavor_dynamics_integrity.py`

- **WEAK 3-flavor runner-level dynamics telemetry (e2e, not golden):**
    - Runs the runner in `--flavors 3` mode and asserts per-bin density-matrix integrity from CSV telemetry
       (trace≈1, ρ ⪰ 0 via min eigenvalue, Hermiticity error, and Pe+Pmu+Ptau≈1):
       `integration_artifacts/mastereq/tests/test_e2e_weak_runner_3flavor_telemetry.py`

- **WEAK internal rate-kernel closure step (e2e, not golden):**
    - Computes `pred_sm/pred_geo` from explicit internal rate ingredients (flux×σ×eff×smearing×exposure)
       driven by state-derived probabilities, without using pack `N_sig_sm` and without signal reweighting:
       `integration_artifacts/mastereq/tests/test_e2e_weak_runner_internal_rate_kernel.py`

- **WEAK dynamics-to-rate deformation coupling (e2e, not golden):**
      - Asserts that deforming the *state-derived* probability deforms internally computed reconstructed rates as expected:
         - P(E)=0 → rate collapse
         - P(E)=1 → no-oscillation rate
         - energy-dependent P(E) → spectral distortion (analytic 2-flavor vacuum check)
         `integration_artifacts/mastereq/tests/test_e2e_weak_runner_dynamics_to_rate_deformation.py`

- **WEAK tabular (experiment-shaped) rate inputs (e2e, not golden):**
      - Adds tabular/histogram flux/σ/eff models to the internal rate kernel and checks:
         - tabular-constant reproduces the old const-model predictions
         - shaped tabular flux deforms the reconstructed spectrum as expected
         `integration_artifacts/mastereq/tests/test_e2e_weak_runner_rate_kernel_tabular_models.py`

- **WEAK tabular validation + multi-tabular product lock (unit + e2e, not golden):**
      - Validates tabular inputs are physical and debuggable:
         - rejects negative or non-finite y values
         - optional strict coverage check that true-energy bins are fully covered by tabular support
         `integration_artifacts/mastereq/tests/test_weak_rate_kernel_tabular_validation.py`
      - E2E lock that flux×σ×eff tabular inputs bind multiplicatively (P(E)=1, identity smearing):
         `integration_artifacts/mastereq/tests/test_e2e_weak_runner_rate_kernel_tabular_product_lock.py`

   Note: `rate_kernel.tabular_coverage` defaults to `ignore` for backward compatibility; for paper-facing runs prefer `warn` or `strict`
   to prevent silent rate suppression when tabular inputs do not cover the true-energy bins.

- **WEAK smearing physics constraints (unit + e2e, not golden):**
    - Validates migration matrix is nonnegative and column-stochastic (Σ_rec S(rec,true)=1):
       `integration_artifacts/mastereq/tests/test_weak_rate_kernel_smearing_physical.py`
    - E2E check that a nontrivial physical smearing matrix deforms the reconstructed spectrum as expected:
       `integration_artifacts/mastereq/tests/test_e2e_weak_runner_internal_rate_kernel_smearing.py`

- **WEAK sparse migration matrices (A3 realism step; unit + e2e, not golden):**
      - Adds a pack format for sparse smearing/migration matrices (`rate_kernel.smear_sparse`, COO) with:
         - nonnegativity, index-range checks, duplicate (i,j) merging
         - column-stochastic enforcement (Σ_rec S(rec,true)=1)
         `integration_artifacts/mastereq/tests/test_weak_rate_kernel_sparse_smearing.py`
      - E2E check that a realistic-size sparse COO migration (25 bins) produces the expected reconstructed spectrum deformation:
         `integration_artifacts/mastereq/tests/test_e2e_weak_runner_internal_rate_kernel_sparse_smearing.py`
- **Microphysics-derived rate plumbing (n·σ·v → γ):**
   - Stability/sanity of microphysics helpers: `integration_artifacts/mastereq/tests/test_microphysics_scaffold.py`
   - End-to-end wiring equivalence (derive γ internally vs pass γ explicitly): `integration_artifacts/mastereq/tests/test_microphysics_wiring_equivalence.py`

- **EM runners ↔ declared-math equivalence (baseline + GEO map):**
   - Bhabha forward golden-output check: `integration_artifacts/mastereq/tests/test_equivalence_em_bhabha_golden_outputs.py`
   - MuMu forward golden-output check: `integration_artifacts/mastereq/tests/test_equivalence_em_mumu_golden_outputs.py`

- **EM paper run mode (single command → deterministic out/ artifacts; not accuracy):**
    - Runs the EM forward harnesses (Bhabha + mu+mu-) on repo-hosted HEPData-derived packs.
    - Writes deterministic CSV + JSON summaries under `out/` and emits provenance telemetry (resolved paths).
    - Evidence test (e2e):
       `integration_artifacts/mastereq/tests/test_e2e_em_paper_run_mode.py`

- **DM runners ↔ declared-math equivalence (CV protocol + GEO map):**
   - Holdout CV (env_model=none) golden-output check: `integration_artifacts/mastereq/tests/test_equivalence_dm_golden_outputs.py`
   - Holdout CV (env_model=thread + STIFFGATE calibration) golden-output check: `integration_artifacts/mastereq/tests/test_equivalence_dm_golden_outputs.py`

- **DM paper run mode (single command → deterministic out/ artifacts; not accuracy):**
    - Runs the DM holdout-CV runners on repo-hosted SPARC points (thread+STIFFGATE calibration + env_model=none branch).
    - Writes deterministic CSV + JSON summaries under `out/` and emits provenance telemetry (resolved paths).
    - Evidence test (e2e):
       `integration_artifacts/mastereq/tests/test_e2e_dm_paper_run_mode.py`

- **LIGO runner ↔ declared-math equivalence (quadrupole pattern generation):**
   - Quadrupole-drive golden-output check (plus/cross patterns): `integration_artifacts/mastereq/tests/test_equivalence_ligo_quadrupole_golden_outputs.py`
   - Golden artifacts (regenerated by `integration_artifacts/scripts/verdict_golden_harness.py` from `tools/verdict_commands.txt`):
     - `integration_artifacts/out/verdict_golden/out/LIGO_quadrupole_plus_FIXED4.csv`
     - `integration_artifacts/out/verdict_golden/out/LIGO_quadrupole_cross_FIXED4.csv`

- **STRONG runner ↔ declared-math equivalence (frozen baseline + GEO map):**
   - sigma_tot energy scan golden-output check: `integration_artifacts/mastereq/tests/test_equivalence_strong_sigma_tot_golden_outputs.py`
   - rho energy scan golden-output check: `integration_artifacts/mastereq/tests/test_equivalence_strong_rho_golden_outputs.py`

- **STRONG stateful “film” baseline (energy-axis internal state) ↔ golden outputs:**
    - Adds a state evolution `t=ln(s/sM)` basis engine (exact stepping, no drift) and derives
       $\sigma_{\rm SM}(s)$ and $d\sigma/d\ln s$ from an evolved internal state (not pointwise closed-form evaluation).
    - Equivalence to the existing golden CSV outputs (same canonical verdict settings):
       `integration_artifacts/mastereq/tests/test_equivalence_strong_stateful_matches_golden.py`
    - Internal-state evolution unit tests (this is a dynamics test surface, not just a formula check):
       `integration_artifacts/mastereq/tests/test_dynamics_strong_pdg_stateful_basis.py`

- **STRONG C1 amplitude-level core (toy eikonal; integrity + anti-fallback, not golden):**
    - Evolves an internal complex eikonal state $\chi(b,t)$ along $t=\ln(s/s_0)$ and computes
      $\sigma_{\rm tot}$ and $\rho$ from a forward-amplitude proxy (optical theorem).
      - Anti-fallback lock: when `STRONG_C1_POISON_PDG_CALLS=1`, the runner overwrites PDG baseline-eval
         functions with stubs that raise; the C1 path must still run successfully (no baseline calls).
      - C1.2 stability locks: the e2e test enforces numerical stability under `dt_max` refinement and `nb`
         (impact-parameter grid) refinement for both $\sigma_{\rm tot}$ and $\rho$.
         These are regression/integrity requirements (numerical stability), not physical-accuracy claims.
    - Evidence test (e2e):
       `integration_artifacts/mastereq/tests/test_e2e_strong_c1_amplitude_core_integrity_and_antifallback.py`

- **STRONG C2 pack/observable closure (chi2/cov + anti-fallback, not golden):**
    - Consumes a pack with an energy scan (and optional data/covariance), predicts $\sigma_{\rm tot}$ and $\rho$
      from the amplitude core, and computes residuals + $\chi^2$.
    - Anti-fallback lock: PDG/COMPETE baseline *eval calls* are poisoned; the C2 path must still run successfully.
    - Evidence test (e2e):
       `integration_artifacts/mastereq/tests/test_e2e_strong_c2_pack_chi2_closure_and_antifallback.py`

- **STRONG C3 (GEO inside evolution + response physics locks, not golden):**
    - Integrates GEO *inside* the amplitude-core evolution law (state-derived; not a post-hoc σ/ρ overlay).
    - Validates response/migration maps with physics locks (WEAK A3 pattern): nonnegativity + column-stochastic
      normalization for both dense and sparse COO.
    - Evidence test (e2e):
       `integration_artifacts/mastereq/tests/test_e2e_strong_c3_geo_in_evolution_response_and_separation.py`

- **STRONG C4 HEPData-like IO closure (CSV+cov paths, not golden):**
    - Consumes a pack that points to external data and covariance CSVs (HEPData-like `paths` style).
    - Computes predictions from the amplitude core and computes $\chi^2$ using either full covariance or diag uncertainties.
    - Evidence test (e2e):
       `integration_artifacts/mastereq/tests/test_e2e_strong_c4_hepdata_like_pack_ingestion.py`

- **STRONG C5A real-data reproduction packs (paths-based; smoke-only, not accuracy):**
   - Runs the same C4 runner on repo-hosted real CSV tables for $\sigma_{\rm tot}$ and $\rho$ via `paths`.
   - Enforces call-poison + IO provenance telemetry; asserts finite $\chi^2$ without claiming fit quality.
   - Evidence test (e2e):
      `integration_artifacts/mastereq/tests/test_e2e_strong_c5a_realdata_packs_smoke.py`

- **Entanglement/Photon bridge ↔ declared-math equivalence:**
    - Entanglement CHSH coincidence audit equivalence:
       `integration_artifacts/mastereq/tests/test_equivalence_entanglement_runner.py`
    - Photon birefringence prereg (locked formulas) equivalence:
       `integration_artifacts/mastereq/tests/test_equivalence_photon_birefringence_runner.py`

Non-claims (explicitly not proven by the above):
- That the runner outputs include or validate dissipative GKSL channels (they generally don’t).
- That the microphysics templates are quantitatively “true SM/BSM predictions” (they are documented placeholders until replaced by model-specific calculations).

## Canonical runner map (sector-by-sector)

Canonical command source: `tools/verdict_commands.txt`.

- EM (Bhabha): `em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py`
- EM (mu-mu): `em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py`
- Weak/oscillation: `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py`, `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py`
- Strong: `strong_sigma_tot_energy_scan_v2.py`, `strong_rho_energy_scan_v3.py`
   - Optional stateful runners (same declared math, but state-derived from an internal state evolved along energy):
      `strong_sigma_tot_energy_scan_stateful.py`, `strong_rho_energy_scan_stateful.py`
   - Optional C1 amplitude-core runner (internal state + evolution + integrity + anti-fallback; not golden-equivalent):
      `strong_amplitude_eikonal_energy_scan_c1.py`
- DM: `dm_holdout_cv_thread_STIFFGATE.py`, `dm_holdout_cv_thread.py`
- LIGO/GW: `improved_simulation_STABLE_v17_xy_quadrupole_drive_ANISO_PHYS_TENSOR_PHYS_FIXED4.py`
- Entanglement/Photon bridge:
   - `integration_artifacts/entanglement_photon_bridge/audit_nist_coinc_csv_bridgeE0_v1_DROPIN.py`
   - `integration_artifacts/entanglement_photon_bridge/run_prereg_cmb_birefringence_v1_DROPIN_SELFCONTAINED.ps1`
   - `integration_artifacts/entanglement_photon_bridge/run_prereg_birefringence_accumulation_v1_DROPIN_SELFCONTAINED_FIX.ps1`

### WEAK: phase-shift runner ↔ GKSL mass-sector mapping

Runner: `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py`

Key idea:
- The runner’s SM probability uses a two-flavor-like phase convention
  $$\Delta_{\rm runner}=1.267\,\Delta m^2\,L/E$$
  and then applies a kernel phase-shift $\Delta\to \Delta + d\phi(L,E)$.
- The GKSL reference uses the standard two-flavor convention
  $$\Delta_{\rm GKSL}=1.267\,\Delta m^2\,L/(4E).$$

So the equivalence is established by:
1) Mapping the runner’s $\Delta m^2$ into the GKSL convention via
   $$\Delta m^2_{\rm GKSL}=4\,\Delta m^2_{\rm runner}.$$
2) Matching the appearance-channel amplitude by choosing $\theta$ so
   $$\sin^2(2\theta)=A_0,$$
   where $A_0=\sin^2(\theta_{23})\sin^2(2\theta_{13})$ is what the runner hard-codes.
3) Implementing the runner’s additive phase shift $d\phi$ as a constant-in-$L$ mass-sector correction
   $$d\phi = 1.267\,\delta(\Delta m^2)\,\frac{L}{4E}\quad\Rightarrow\quad
   \delta(\Delta m^2)=d\phi\,\frac{4E}{1.267\,L}.$$

This check is encoded as a pytest test:
- `integration_artifacts/mastereq/tests/test_equivalence_weak_runner.py`

Run it:

```powershell
python -m pytest -q integration_artifacts/mastereq/tests/test_equivalence_weak_runner.py
```

### WEAK: golden-output per-bin phase-map equivalence (paper-grade claim)

The runner is not (currently) a single-parameter “physics model” in the strict sense, because the packs and runner logic can make the exported
$P_{\rm SM}$ be *pack-derived* (e.g. ratios like $N_{\rm sig,SM}/N_{\rm sig,noosc}$), include bin shifts, background-only bins, etc.

So the equivalence we validate at “golden CSV” level is the runner’s **algorithmic contract**:

1) Treat the exported $P_{\rm SM}$ as defining an *effective* phase $\Delta_{\rm eff}(L,E)$ through the runner’s own inverse mapping
   (appearance: $P=A_0\sin^2\Delta$, disappearance: $P=\cos^2\Delta$).
2) Apply the runner kernel update $\Delta\to\Delta + d\phi$.
3) Compare the resulting $P_{\rm geo}$ against the golden outputs.

We then show that the exact same map is representable as a GKSL unitary evolution by choosing an *effective* $\Delta m^2_{\rm eff}$ per bin
(equivalently per $(L,E)$) to reproduce $\Delta_{\rm eff}$, and applying the same $\delta(\Delta m^2)$ implied by $d\phi$.

This check is encoded as a pytest test:
- `integration_artifacts/mastereq/tests/test_equivalence_weak_golden_outputs.py`

Run it:

```powershell
python -m pytest -q integration_artifacts/mastereq/tests/test_equivalence_weak_golden_outputs.py
```

### STRONG: golden-output equivalence (sigma_tot and rho energy scans)

The STRONG runners are not GKSL density-matrix solvers; they are frozen-baseline energy-scan harnesses.
For paper-grade reproducibility, we validate that the golden CSV outputs satisfy the runners’ declared
math exactly (independent reimplementation), point-by-point.

New in this snapshot: an optional **stateful “film” implementation** of the same frozen-PDG baseline.
Instead of evaluating the closed form independently at each energy point, it evolves an internal basis state
along $t=\ln(s/s_M)$ and derives $\sigma_{\rm SM}(s)$ and $d\sigma/d\ln s$ from that state.
This is still a frozen-baseline harness (not a first-principles strong-sector engine), but it eliminates
the “photo overlay” implementation mode.

1) `strong_sigma_tot_energy_scan_v2.py` (total cross section)
    - Baseline: frozen PDG/COMPETE form $\sigma_{\rm SM}(\sqrt{s})$
    - GEO modulation (canonical run uses `template=cos`, `env_mode=eikonal`):
       $$\sigma_{\rm GEO}=\sigma_{\rm SM}\Big(1 + A\,|c_1|\,\cos(\delta_{\rm ref}\,\mathrm{scale}(s))\Big),\qquad
       \mathrm{scale}(s)=\frac{\ln(s/s_M)}{\ln(s_{\rm ref}/s_M)}.$$

    Evidence test:
    - `integration_artifacts/mastereq/tests/test_equivalence_strong_sigma_tot_golden_outputs.py`

2) `strong_rho_energy_scan_v3.py` (rho + amplitude rotation)
    - Proxy baseline: $\rho_{\rm SM}\approx(\pi/2)\,(d\sigma/d\ln s)/\sigma$ using the same frozen baseline.
    - Forward amplitude rotation:
       $$z=(\rho_{\rm SM}+i)\,e^{i\phi_{\rm geo}(s)},\qquad
       \sigma_{\rm GEO}=\sigma_{\rm SM}\,\Im z,\qquad
       \rho_{\rm GEO}=\Re z/\Im z.$$
       with $\phi_{\rm geo}(s)=A|c_1|\cos(\delta_{\rm ref}\,\mathrm{scale}(s))$ for the canonical eikonal mode.

    Evidence test:
    - `integration_artifacts/mastereq/tests/test_equivalence_strong_rho_golden_outputs.py`

### EM: golden-output equivalence (Bhabha and mu+mu- forward harnesses)

The EM runners are not GKSL density-matrix solvers; they are forward harnesses that fit nuisance normalizations
under a frozen baseline and apply a multiplicative GEO modulation $\mathrm{pred}_{\rm GEO}=\mathrm{pred}_{\rm SM}(1+\delta)$.

For paper-grade reproducibility, we validate that the golden CSV outputs satisfy the runners’ declared math exactly
(independent reimplementation), point-by-point, for the canonical verdict commands (including `--shape_only`,
`--freeze_betas`, and `--beta_nonneg`).

Evidence tests:
- `integration_artifacts/mastereq/tests/test_equivalence_em_bhabha_golden_outputs.py`
- `integration_artifacts/mastereq/tests/test_equivalence_em_mumu_golden_outputs.py`

### DM: golden-output equivalence (SPARC holdout CV)

The DM runners are k-fold **galaxy-holdout** CV harnesses. They:
1) Split by galaxy label, not by individual points.
2) Compute baseline $\chi^2$ on $g_{\rm bar}$ vs $g_{\rm obs}$ in $\log_{10} g$.
3) Apply the GEO map $g_{\rm pred} = g_{\rm bar} + g_{\rm geo}(A,\alpha,\mathrm{env})$ and report per-fold improvements.

For paper-grade reproducibility, we validate that the golden CSV fold summaries match an independent reimplementation
for the canonical verdict commands (including thread env normalization and, for STIFFGATE, train-fold-only gate calibration).

Evidence test:
- `integration_artifacts/mastereq/tests/test_equivalence_dm_golden_outputs.py`

## What is NOT checked yet

- Full pack-driven χ² reproduction (NOvA/T2K/MINOS end-to-end).
- EM/STRONG/DM equivalence to GKSL (those runners are not written as GKSL evolutions today).
- LIGO quadrupole-drive equivalence to GKSL (the LIGO runner is a classical lattice simulation, not a density-matrix solver).
- Any claim that the runner’s kernels correspond to a *physically derived* open-system environment.
- Any validation that the **microphysics-derived** rates (the `n·σ·v → γ` scaffolding) match runner outputs: the WEAK runner golden outputs are a unitary
   phase-map ($H$ update) and do not include dissipative Lindblad terms (no $\gamma$ to compare).

## Exactness boundary (important)

What is exact/reproducible in this repo:
- Runner declared-math equivalence checks (golden outputs + independent reimplementation tests).
- GKSL integration contracts and deterministic regression tests.
- Microphysics wiring checks (`use_microphysics=True` vs explicit same $\gamma$).

What is not “first-principles exact derivation complete” yet:
- Sector-by-sector full QFT dissipator derivations from SM/BSM amplitudes,
- medium-response closure + Born-Markov/secular validity proof per sector,
- non-Markovian closure where required.

## Next extensions

- Add an end-to-end WEAK check: parse a channels pack, reproduce per-bin P_sm/P_geo and the printed χ² summary, and compare to the runner outputs.
- Add sector-by-sector mapping docs: what exactly would be treated as Hamiltonian vs dissipator in GKSL for EM/STRONG/DM.
- If/when a runner exports damping-like observables (or we add a GKSL-damped runner mode), add a microphysics-to-runner equivalence test that compares
   predicted damping vs exported $\gamma$-sensitive outputs.

- Add explicit per-sector links from this file to `integration_artifacts/mastereq/derivation_mastereq.md` subsections so equation-level and runner-level evidence are navigable in one click.
