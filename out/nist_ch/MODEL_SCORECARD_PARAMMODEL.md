# NIST CH/Eberhard model scorecard

| run_id | label | window | slots | trials_valid | J_data | J_model | delta_J | j_data_per_1M | j_model_per_1M | delta_j_per_1M | sign_ok | provider |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_11 | real_run | slot6 | 6 | 337818518 | 122 | 122.341 | 0.340699 | 0.361141 | 0.362149 | 0.00100853 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1.00986) |
| 01_11 | real_run | slots5-7 | 5-7 | 337818518 | 398 | 416.298 | 18.2979 | 1.17815 | 1.23231 | 0.054165 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1.00986) |
| 01_11 | real_run | slots4-8 | 4-8 | 337818518 | 550 | 712.828 | 162.828 | 1.62809 | 2.11009 | 0.481998 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1.00986) |
| 02_54 | real_run | slot6 | 6 | 203681460 | 8 | 8.1871 | 0.187104 | 0.039277 | 0.0401956 | 0.000918611 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=0.98749) |
| 02_54 | real_run | slots5-7 | 5-7 | 203681460 | 41 | -7.77344 | -48.7734 | 0.201295 | -0.0381647 | -0.239459 | NO | PARAMMODEL v4.1 (bridge; alpha_pair=0.98749) |
| 02_54 | real_run | slots4-8 | 4-8 | 203681460 | 176 | -22.3116 | -198.312 | 0.864094 | -0.109542 | -0.973636 | NO | PARAMMODEL v4.1 (bridge; alpha_pair=0.98749) |
| 03_31 | training_stub | slot6 | 6 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1) |
| 03_31 | training_stub | slots5-7 | 5-7 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1) |
| 03_31 | training_stub | slots4-8 | 4-8 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1) |
| 03_43 | real_run | slot6 | 6 | 107109594 | 13 | 13.1155 | 0.115531 | 0.121371 | 0.12245 | 0.00107863 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1.01146) |
| 03_43 | real_run | slots5-7 | 5-7 | 107109594 | 49 | 57.7422 | 8.74218 | 0.457475 | 0.539094 | 0.081619 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1.01146) |
| 03_43 | real_run | slots4-8 | 4-8 | 107109594 | 151 | 103.244 | -47.7558 | 1.40977 | 0.963912 | -0.445859 | YES | PARAMMODEL v4.1 (bridge; alpha_pair=1.01146) |

## Notes
- This compares empirical `J_data` (from run*.summary.json) to `J_model` produced by the probability provider.
- Without a real provider, use `--toy_ok` only to sanity-check plumbing; it is **NOT** model-faithful.