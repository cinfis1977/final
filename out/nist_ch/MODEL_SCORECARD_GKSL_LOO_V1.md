# NIST CH GKSL leave-one-run-out scorecard

| holdout_run | run_id | window | slots | trials_valid | J_data | J_model | delta_J | delta_j_per_1M | sign_ok | provider |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_11 | 01_11 | slot6 | 6 | 337818518 | 122 | 122 | 1.35319e-08 | 4.00567e-11 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |
| 01_11 | 01_11 | slots5-7 | 5-7 | 337818518 | 398 | 365.86 | -32.1401 | -0.0951403 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |
| 01_11 | 01_11 | slots4-8 | 4-8 | 337818518 | 550 | 609.488 | 59.4878 | 0.176094 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |
| 02_54 | 02_54 | slot6 | 6 | 203681460 | 8 | 8 | -6.78781e-10 | -3.33256e-12 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |
| 02_54 | 02_54 | slots5-7 | 5-7 | 203681460 | 41 | 24.1445 | -16.8555 | -0.0827544 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |
| 02_54 | 02_54 | slots4-8 | 4-8 | 203681460 | 176 | 40.8142 | -135.186 | -0.663712 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |
| 03_43 | 03_43 | slot6 | 6 | 107109594 | 13 | 13 | 2.52207e-09 | 2.35467e-11 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |
| 03_43 | 03_43 | slots5-7 | 5-7 | 107109594 | 49 | 39.0092 | -9.99082 | -0.0932766 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |
| 03_43 | 03_43 | slots4-8 | 4-8 | 107109594 | 151 | 65.1062 | -85.8938 | -0.801925 | YES | GKSL_PREDICTIVE_V2 (holdout bridge; center_slot=6; gamma_km_inv=8.10561e-25) |

## Notes
- Each row is scored with a params bundle fitted on all real runs except the listed holdout run.
- This is a GKSL-modulated predictive holdout bridge, not a calibrated closure.