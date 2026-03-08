# NIST CH/Eberhard model scorecard

| run_id | label | window | slots | trials_valid | J_data | J_model | delta_J | j_data_per_1M | j_model_per_1M | delta_j_per_1M | sign_ok | provider |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_11 | real_run | slot6 | 6 | 337818518 | 122 | 0 | -122 | 0.361141 | 0 | -0.361141 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 01_11 | real_run | slots5-7 | 5-7 | 337818518 | 398 | 0 | -398 | 1.17815 | 0 | -1.17815 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 01_11 | real_run | slots4-8 | 4-8 | 337818518 | 550 | 0 | -550 | 1.62809 | 0 | -1.62809 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 02_54 | real_run | slot6 | 6 | 203681460 | 8 | 0 | -8 | 0.039277 | 0 | -0.039277 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 02_54 | real_run | slots5-7 | 5-7 | 203681460 | 41 | 0 | -41 | 0.201295 | 0 | -0.201295 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 02_54 | real_run | slots4-8 | 4-8 | 203681460 | 176 | 0 | -176 | 0.864094 | 0 | -0.864094 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 03_31 | training_stub | slot6 | 6 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 03_31 | training_stub | slots5-7 | 5-7 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 03_31 | training_stub | slots4-8 | 4-8 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 03_43 | real_run | slot6 | 6 | 107109594 | 13 | 0 | -13 | 0.121371 | 0 | -0.121371 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 03_43 | real_run | slots5-7 | 5-7 | 107109594 | 49 | 0 | -49 | 0.457475 | 0 | -0.457475 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |
| 03_43 | real_run | slots4-8 | 4-8 | 107109594 | 151 | 0 | -151 | 1.40977 | 0 | -1.40977 | NO | PARAMMODEL v5 (calibrated bridge; alpha_pair=1; beta_pair=0) |

## Notes
- This compares empirical `J_data` (from run*.summary.json) to `J_model` produced by the probability provider.
- Without a real provider, use `--toy_ok` only to sanity-check plumbing; it is **NOT** model-faithful.