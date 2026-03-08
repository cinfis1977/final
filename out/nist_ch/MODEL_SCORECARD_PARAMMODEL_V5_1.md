# NIST CH/Eberhard model scorecard

| run_id | label | window | slots | trials_valid | J_data | J_model | delta_J | j_data_per_1M | j_model_per_1M | delta_j_per_1M | sign_ok | provider |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_11 | real_run | slot6 | 6 | 337818518 | 122 | 122 | 1.35319e-08 | 0.361141 | 0.361141 | 4.00567e-11 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1.00986; beta_pair=-0.000834425) |
| 01_11 | real_run | slots5-7 | 5-7 | 337818518 | 398 | 398 | 6.43331e-09 | 1.17815 | 1.17815 | 1.90437e-11 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1.00986; beta_pair=-0.000834425) |
| 01_11 | real_run | slots4-8 | 4-8 | 337818518 | 550 | 550 | -1.2061e-09 | 1.62809 | 1.62809 | -3.57026e-12 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1.00986; beta_pair=-0.000834425) |
| 02_54 | real_run | slot6 | 6 | 203681460 | 8 | 8 | -6.78781e-10 | 0.039277 | 0.039277 | -3.33256e-12 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=0.98749; beta_pair=0.00645129) |
| 02_54 | real_run | slots5-7 | 5-7 | 203681460 | 41 | 41 | 5.6599e-10 | 0.201295 | 0.201295 | 2.7788e-12 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=0.98749; beta_pair=0.00645129) |
| 02_54 | real_run | slots4-8 | 4-8 | 203681460 | 176 | 176 | -1.6548e-09 | 0.864094 | 0.864094 | -8.1245e-12 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=0.98749; beta_pair=0.00645129) |
| 03_31 | training_stub | slot6 | 6 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1; beta_pair=0) |
| 03_31 | training_stub | slots5-7 | 5-7 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1; beta_pair=0) |
| 03_31 | training_stub | slots4-8 | 4-8 | 363 | 0 | 0 | 0 | 0 | 0 | 0 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1; beta_pair=0) |
| 03_43 | real_run | slot6 | 6 | 107109594 | 13 | 13 | 2.52207e-09 | 0.121371 | 0.121371 | 2.35467e-11 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1.01146; beta_pair=0.00964635) |
| 03_43 | real_run | slots5-7 | 5-7 | 107109594 | 49 | 49 | -3.22544e-10 | 0.457475 | 0.457475 | -3.01137e-12 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1.01146; beta_pair=0.00964635) |
| 03_43 | real_run | slots4-8 | 4-8 | 107109594 | 151 | 151 | 1.10862e-09 | 1.40977 | 1.40977 | 1.03502e-11 | YES | PARAMMODEL v5.1 (calibrated bridge; direct CH channels; alpha_pair=1.01146; beta_pair=0.00964635) |

## Notes
- This compares empirical `J_data` (from run*.summary.json) to `J_model` produced by the probability provider.
- Without a real provider, use `--toy_ok` only to sanity-check plumbing; it is **NOT** model-faithful.