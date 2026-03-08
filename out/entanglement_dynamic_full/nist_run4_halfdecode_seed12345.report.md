# Entanglement dynamic/full-model runner v1 report
- input CSV: `out\nist_run4_coincidences_offsetjoin_half.csv`
- out prefix: `out\entanglement_dynamic_full\nist_run4_halfdecode_seed12345`

## Observed CHSH
- S_signed = 2.73112078036
- S_abs    = 2.73112078036

## Model prediction
- S_model_signed = -1.27390576445
- S_model_abs    = 1.27390576445
- |S_abs - S_model_abs| = 1.45721501591

## Null (if computed)
- null_trials = 20000
- p_S_abs (P(null >= S_obs_abs)) = 0
- p95_S_abs = 0.0835228

## Notes
- This runner is **full-model** only when the GKSL integration is active and state audit confirms non-trivial state features.
- If your coincidence CSV lacks timing columns, state features default to gap-based proxies computed from `coinc_idx` ordering.
