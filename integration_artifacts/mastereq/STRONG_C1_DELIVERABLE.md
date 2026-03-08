# STRONG C1 deliverable (amplitude-level core)

This deliverable is the STRONG analogue of the WEAK A3 closure line:

**internal state + evolution law + observable from state + integrity + closure + anti-fallback**.

## What C1 is (and is not)

### C1 is

- An **amplitude-level** internal state core: a complex eikonal state $\chi(b,t)$ or forward amplitude $F(s,0)$.
- A deterministic **evolution law** along $t=\ln(s/s_0)$.
- Observables computed **from the evolved state**:
  - optical-theorem proxy: $\sigma_{\rm tot}(s) \propto \mathrm{Im}\,F(s,0)$
  - $\rho(s)=\mathrm{Re}F/\mathrm{Im}F$
- **Integrity tests** that assert basic physical/numerical sanity (nonnegativity, absorptivity/|S|≤1, boundedness).
- **Anti-fallback e2e locks** that fail if PDG/COMPETE baseline code is imported/called.

### C1 is not

- Not a PDG/COMPETE frozen baseline reproduction.
- Not “QCD from first principles”. It is a **toy strong-sector motor** whose value is structural closure and anti-proxy discipline.

## Implementation (this repo snapshot)

- Core module: `integration_artifacts/mastereq/strong_c1_eikonal_amplitude.py`
  - State: `EikonalC1State` with arrays $\chi_R(b,t),\chi_I(b,t)$
  - Evolution: stable deterministic update with absorptivity clamp ($\chi_I\ge 0$)
  - Observables: `sigma_tot_rho_from_state` computed from forward amplitude proxy built from $\Gamma(b)=1-e^{i\chi(b)}$

- Runner: `strong_amplitude_eikonal_energy_scan_c1.py`
  - Reads `sqrts_GeV` points, evolves the internal state, writes $\sigma_{\rm tot}$ and $\rho$
  - Supports a null default for GEO phase rotation (kept for runbook symmetry)
  - Anti-fallback: when `STRONG_C1_POISON_PDG_CALLS=1`, imports the PDG baseline harness modules and overwrites baseline-eval functions with stubs that raise
  - Telemetry flags: `amplitude_core_used=true`, `pdg_baseline_used=false`, plus explicit `F_re/F_im` mapping

- Tests:
  - `integration_artifacts/mastereq/tests/test_e2e_strong_c1_amplitude_core_integrity_and_antifallback.py`
    - Runs the C1 runner end-to-end
    - Asserts integrity conditions
    - Asserts anti-fallback guard is active

## C1.2 numerical refinement locks (minimum)

To reduce “numerical artefact” risk (grid/step sensitivity), the C1 e2e test also enforces:

- **dt refinement**: halving `--dt_max` must not change
  - $\sigma_{\rm tot}$ by more than 5% (max relative deviation over scan points)
  - $\rho$ by more than 0.10 (max absolute deviation)
- **b-grid refinement**: doubling `--nb` must not change
  - $\sigma_{\rm tot}$ by more than 5%
  - $\rho$ by more than 0.10

These tolerances are intentionally loose: they are stability locks ("motor not broken"), not precision claims.

They are **numerical stability** regression requirements only; they are **not** a claim of physical-model correctness.

## Relationship to the existing STRONG “stateful film” step

The existing `strong_*_stateful.py` runners + `integration_artifacts/mastereq/strong_pdg_stateful_dynamics.py` are **bridge/scaffolding**:

- **Stateful reproduction of the frozen PDG/COMPETE baseline (+ GEO)**
- Not amplitude-level strong dynamics

C1 exists to ensure STRONG has a real “motor” path that cannot silently collapse back to a baseline overlay.
