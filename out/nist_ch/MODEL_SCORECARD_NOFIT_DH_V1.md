# NIST CH/Eberhard model scorecard

| run_id | label | window | slots | trials_valid | J_data | J_model | delta_J | j_data_per_1M | j_model_per_1M | delta_j_per_1M | sign_ok | provider |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_11 | real_run | slot6 | 6 | 337818518 | 122 | -770.742 | -892.742 | 0.361141 | -2.28153 | -2.64267 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 01_11 | real_run | slots5-7 | 5-7 | 337818518 | 398 | -2312.18 | -2710.18 | 1.17815 | -6.84443 | -8.02258 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 01_11 | real_run | slots4-8 | 4-8 | 337818518 | 550 | -3853.54 | -4403.54 | 1.62809 | -11.4071 | -13.0352 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 02_54 | real_run | slot6 | 6 | 203681460 | 8 | -465.447 | -473.447 | 0.039277 | -2.28517 | -2.32445 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 02_54 | real_run | slots5-7 | 5-7 | 203681460 | 41 | -1396.31 | -1437.31 | 0.201295 | -6.85536 | -7.05665 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 02_54 | real_run | slots4-8 | 4-8 | 203681460 | 176 | -2327.13 | -2503.13 | 0.864094 | -11.4253 | -12.2894 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 03_31 | training_stub | slot6 | 6 | 363 | 0 | -0.000717916 | -0.000717916 | 0 | -1.97773 | -1.97773 | YES | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 03_31 | training_stub | slots5-7 | 5-7 | 363 | 0 | -0.0021537 | -0.0021537 | 0 | -5.93305 | -5.93305 | YES | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 03_31 | training_stub | slots4-8 | 4-8 | 363 | 0 | -0.00358941 | -0.00358941 | 0 | -9.88819 | -9.88819 | YES | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 03_43 | real_run | slot6 | 6 | 107109594 | 13 | -244.703 | -257.703 | 0.121371 | -2.2846 | -2.40597 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 03_43 | real_run | slots5-7 | 5-7 | 107109594 | 49 | -734.093 | -783.093 | 0.457475 | -6.85366 | -7.31113 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |
| 03_43 | real_run | slots4-8 | 4-8 | 107109594 | 151 | -1223.46 | -1374.46 | 1.40977 | -11.4225 | -12.8323 | NO | NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding) |

## Notes
- This compares empirical `J_data` (from run*.summary.json) to `J_model` produced by the probability provider.
- Without a real provider, use `--toy_ok` only to sanity-check plumbing; it is **NOT** model-faithful.