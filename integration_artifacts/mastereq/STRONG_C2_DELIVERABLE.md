# STRONG C2 deliverable (pack/observable closure + χ²)

C2 is the STRONG analogue of WEAK’s “dynamics → pipeline closure” layer:

**Amplitude-core outputs → pack/observable closure + χ²/cov + anti-fallback + e2e**.

This deliverable is about *closure and integrity*, not about physical accuracy.

## What C2 is (and is not)

### C2 is

- A pack-driven interface that specifies an energy scan (and optionally data + covariance).
- A deterministic prediction path:
  - amplitude-level internal state evolves along $t=\ln(s/s_0)$
  - observables derived from state: $\sigma_{\rm tot}\propto \Im F$, $\rho=\Re F/\Im F$
- A residual and chi-square calculation:
  $$r = y - \hat y,\qquad \chi^2 = r^\top C^{-1} r$$
  or diagonal-uncertainty fallback if no covariance is provided.
- Anti-fallback locks compatible with C1:
  - call-poison of PDG/COMPETE baseline *eval* functions
  - telemetry flags: `amplitude_core_used=true`, `pdg_baseline_used=false`
- An e2e regression test (not a golden output requirement): synthetic pack with `data=pred` gives $\chi^2\approx 0$.

### C2 is not

- Not a claim of **physical-model accuracy**.
- Not a fit/tuning deliverable.

## Implementation (this repo snapshot)

- Runner: `strong_amplitude_pack_chi2_c2.py`
  - Inputs: `--pack pack.json`
  - Outputs:
    - `--out_csv`: per-point predictions + optional residual/pull columns
    - `--out_json`: chi2 summary + integrity + anti-fallback telemetry

- Evidence test (e2e):
  - `integration_artifacts/mastereq/tests/test_e2e_strong_c2_pack_chi2_closure_and_antifallback.py`

## Pack format (minimal)

A minimal STRONG C2 pack is:

```json
{
  "meta": {"name": "..."},
  "scan": {"sqrts_GeV": [7.0, 20.0, 200.0, 13000.0], "channel": "pp"},
  "model": {"s0_GeV2": 1.0, "dt_max": 0.05, "nb": 600, "b_max": 20.0},
  "data": {
    "sigma_tot_mb": {"y": [..], "unc": [..]},
    "rho": {"y": [..], "unc": [..]}
  }
}
```

Optional extensions:

- `data.*.cov`: either `{ "matrix": [[...]] }` or `{ "path": "relative.csv" }`.
- `response`: linear map applied to predictions per observable
  - dense: `{ "dense": [[...]] }`
  - sparse COO: `{ "sparse_coo": {"n": N, "i": [...], "j": [...], "v": [...] } }`
- `factors`: per-point multiplicative factors per observable (`sigma_tot_mb`, `rho`).

## Anti-fallback mechanism

Set one of:

- `STRONG_C1_POISON_PDG_CALLS=1`
- `STRONG_C2_POISON_PDG_CALLS=1`

The runner will import known baseline harness modules and overwrite their baseline-eval
functions with stubs that raise (call-poison). This prevents accidental fallback
without breaking imports.
