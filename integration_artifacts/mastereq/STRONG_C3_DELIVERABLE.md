# STRONG C3 deliverable (GEO-in-evolution + response physics locks)

C3 advances STRONG to the WEAK A3-style discipline:

**GEO state-derived integration inside evolution law + response physics locks (dense/sparse) + e2e separation + anti-fallback**.

This is a closure/integrity deliverable. It is not a claim of physical accuracy.

## What C3 is (and is not)

### C3 is

- GEO integrated *inside* the amplitude-core evolution law (not a post-hoc overlay on σ/ρ).
  - Evidence is an explicit telemetry flag: `geo.geo_applied_in_evolution=true`.
- Response / migration validation with physics locks (WEAK A3 pattern):
  - nonnegative entries
  - index-range checks (sparse COO)
  - **column-stochastic** normalization (Σ_rec R(rec,true)=1) for both dense and sparse maps
- E2E separation evidence:
  - GEO=0 and GEO≠0 runs on the same pack/data produce different χ² (with anti-fallback active)

### C3 is not

- Not a claim of “this is the correct strong-sector physics”.
- Not a tuning/fitting deliverable.

## Implementation (this repo snapshot)

- Evolution core (C1 module, extended with a C3 GEO hook):
  - `integration_artifacts/mastereq/strong_c1_eikonal_amplitude.py`
  - GEO enters as a bounded modulation of the source strength inside `_g_of_t()`.

- Runner:
  - `strong_amplitude_pack_chi2_c3.py`
  - Reads a pack with `scan`, optional `data/cov`, optional `geo`, optional `response`.
  - Validates response maps by default (`response.validate=true`).

- Evidence test (e2e):
  - `integration_artifacts/mastereq/tests/test_e2e_strong_c3_geo_in_evolution_response_and_separation.py`

## Pack additions (beyond C2)

- `geo` block:

```json
"geo": {"A": 0.2, "template": "cos", "phi0": 0.0, "omega": 1.0}
```

- `response.validate` (optional, default true)

```json
"response": {"validate": true, "sigma_tot_mb": {"dense": [[...]]}, "rho": {"sparse_coo": {"n": 4, "i": [...], "j": [...], "v": [...]}}}
```

## Anti-fallback

Same call-poison mechanism as C1/C2. Enable with one of:

- `STRONG_C1_POISON_PDG_CALLS=1`
- `STRONG_C2_POISON_PDG_CALLS=1`
- `STRONG_C3_POISON_PDG_CALLS=1`
