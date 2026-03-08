# Entanglement dynamic/full-model runner v1 report
- input CSV: `out\nist_run4_coincidences_offsetjoin.csv`
- out prefix: `out\entanglement_dynamic_full\nist_run4_from_offsetjoin_seed12345`

## Observed CHSH
- S_signed = 2.69701047322
- S_abs    = 2.69701047322

## Model prediction
- S_model_signed = -1.27390576445
- S_model_abs    = 1.27390576445
- |S_abs - S_model_abs| = 1.42310470877

## Null (if computed)
- null_trials = 20000
- p_S_abs (P(null >= S_obs_abs)) = 0
- p95_S_abs = 0.084074

## Notes
- This runner is **full-model** only when the GKSL integration is active and state audit confirms non-trivial state features.
- If your coincidence CSV lacks timing columns, state features default to gap-based proxies computed from `coinc_idx` ordering.
