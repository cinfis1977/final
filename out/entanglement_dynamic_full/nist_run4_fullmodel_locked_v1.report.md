# Entanglement dynamic/full-model runner v1 report
- input CSV: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\integration_artifacts\entanglement_photon_bridge\nist_run4_coincidences.csv`
- out prefix: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\entanglement_dynamic_full\nist_run4_fullmodel_locked_v1`

## Observed CHSH
- S_signed = 2.45504135783
- S_abs    = 2.45504135783

## Model prediction
- S_model_signed = -1.27390576445
- S_model_abs    = 1.27390576445
- |S_abs - S_model_abs| = 1.18113559338

## Null (if computed)
- null_trials = 5000
- p_S_abs (P(null >= S_obs_abs)) = 0
- p95_S_abs = 0.123463

## Notes
- This runner is **full-model** only when the GKSL integration is active and state audit confirms non-trivial state features.
- If your coincidence CSV lacks timing columns, state features default to gap-based proxies computed from `coinc_idx` ordering.
- Telemetry is written separately to document which named state variables entered the locked gamma map and which remained audit-only.
