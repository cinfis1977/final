# NIST CH term decomposition audit

- provider: .\CODE\ch_model_prob_provider_v1_GKSL_DETECTORFIRST_V2_DROPIN.py
- profile_form: tilt_abs_quad
- gamma_km_inv: 1
- L0_km: 1

## Global
- mean_abs_J_delta_slot6: 35.4019
- mean_abs_J_delta_wide: 386.624
- dominant_term_counts_wide: {"N_pp_00": 6}

## Run/window summary
| holdout_run | window | J_data | J_model | J_delta | dominant_term | dominant_delta |
| --- | --- | --- | --- | --- | --- | --- |
| 01_11 | slot6 | 122 | 77.1269 | -44.8731 | N_pp_00 | -854.504 |
| 01_11 | slots5-7 | 398 | 0.949537 | -397.05 | N_pp_00 | -2527.61 |
| 01_11 | slots4-8 | 550 | -486.65 | -1036.65 | N_pp_00 | -4132.98 |
| 02_54 | slot6 | 8 | 44.1295 | 36.1295 | N_pp_00 | 160.165 |
| 02_54 | slots5-7 | 41 | 123.466 | 82.4656 | N_pp_00 | 810.037 |
| 02_54 | slots4-8 | 176 | 166.787 | -9.21275 | N_pp_00 | 1906.21 |
| 03_43 | slot6 | 13 | -12.203 | -25.203 | N_pp_00 | 465.501 |
| 03_43 | slots5-7 | 49 | -139.861 | -188.861 | N_pp_00 | 1426.1 |
| 03_43 | slots4-8 | 151 | -454.503 | -605.503 | N_pp_00 | 2402.31 |