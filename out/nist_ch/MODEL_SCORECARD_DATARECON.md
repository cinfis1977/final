# NIST CH/Eberhard model scorecard

| run_id | label | window | slots | trials_valid | J_data | J_model | delta_J | j_data_per_1M | j_model_per_1M | delta_j_per_1M | sign_ok | provider |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_11 | real_run | slot6 | 6 | 337818518 | 122 | 122 | 0 | 0.361141 | 0.361141 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 01_11 | real_run | slots5-7 | 5-7 | 337818518 | 398 | 398 | 4.54747e-13 | 1.17815 | 1.17815 | 1.33227e-15 | YES | DATA_RECON (plumbing only, NOT model) |
| 01_11 | real_run | slots4-8 | 4-8 | 337818518 | 550 | 550 | 0 | 1.62809 | 1.62809 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 02_54 | real_run | slot6 | 6 | 203681460 | 8 | 8 | 0 | 0.039277 | 0.039277 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 02_54 | real_run | slots5-7 | 5-7 | 203681460 | 41 | 41 | 0 | 0.201295 | 0.201295 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 02_54 | real_run | slots4-8 | 4-8 | 203681460 | 176 | 176 | 0 | 0.864094 | 0.864094 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 03_31 | training_stub | slot6 | 6 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 03_31 | training_stub | slots5-7 | 5-7 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 03_31 | training_stub | slots4-8 | 4-8 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 03_43 | real_run | slot6 | 6 | 107109594 | 13 | 13 | 0 | 0.121371 | 0.121371 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 03_43 | real_run | slots5-7 | 5-7 | 107109594 | 49 | 49 | 0 | 0.457475 | 0.457475 | 0 | YES | DATA_RECON (plumbing only, NOT model) |
| 03_43 | real_run | slots4-8 | 4-8 | 107109594 | 151 | 151 | 2.27374e-13 | 1.40977 | 1.40977 | 2.22045e-15 | YES | DATA_RECON (plumbing only, NOT model) |

## Notes
- This compares empirical `J_data` (from run*.summary.json) to `J_model` produced by the probability provider.
- Without a real provider, use `--toy_ok` only to sanity-check plumbing; it is **NOT** model-faithful.