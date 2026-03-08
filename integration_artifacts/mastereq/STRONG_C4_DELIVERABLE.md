# STRONG C4 deliverable (HEPData-like pack ingestion)

C4 is the STRONG step that makes the closure runner **paper-facing**:

**HEPData-like real-data pack ingestion (CSV+cov paths) + e2e reproduction + call-poison + schema locks**.

This deliverable is about reproducible IO closure and anti-fallback discipline.
It is **not** a claim of physical accuracy.

## What C4 is (and is not)

### C4 is

- A pack JSON that points to external CSV artifacts (data + optional covariance).
- A runner that reads those CSVs, predicts $\sigma_{\rm tot}(s_i)$ and $\rho(s_i)$ from the amplitude core,
  and computes residuals + $\chi^2$.
- Support for both diagonal uncertainties (from columns in the data CSV) and full covariance matrices (from CSV paths).
- Anti-fallback call-poison + telemetry, as in C1/C2/C3.
- An e2e regression test that constructs a synthetic CSV+cov pack and proves `data=pred ⇒ χ²≈0`.

### C4 is not

- Not a model upgrade.
- Not a fit/tuning deliverable.

## Implementation (this repo snapshot)

- Runner:
  - `strong_amplitude_pack_hepdata_c4.py`

- Evidence test (e2e):
  - `integration_artifacts/mastereq/tests/test_e2e_strong_c4_hepdata_like_pack_ingestion.py`

## Pack format

```json
{
  "meta": {"name": "..."},
  "model": {"s0_GeV2": 1.0, "dt_max": 0.05, "nb": 600, "b_max": 12.0},
  "geo": {"A": 0.0, "template": "cos", "phi0": 0.0, "omega": 1.0},
  "paths": {
    "data_csv": "scan.csv",
    "cov_sigma_tot_csv": "cov_sigma.csv",
    "cov_rho_csv": "cov_rho.csv"
  },
  "columns": {
    "sqrts_GeV": "sqrts_GeV",
    "sigma_tot_mb": "sigma_tot_mb",
    "sigma_tot_unc_mb": "sigma_tot_unc_mb",
    "rho": "rho",
    "rho_unc": "rho_unc"
  }
}
```

## Anti-fallback

Enable call-poison with one of:

- `STRONG_C1_POISON_PDG_CALLS=1`
- `STRONG_C2_POISON_PDG_CALLS=1`
- `STRONG_C3_POISON_PDG_CALLS=1`
- `STRONG_C4_POISON_PDG_CALLS=1`
