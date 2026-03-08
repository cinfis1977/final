# NIST CH/Eberhard model scorecard

| run_id | label | window | slots | trials_valid | J_data | J_model | delta_J | j_data_per_1M | j_model_per_1M | delta_j_per_1M | sign_ok | provider |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_11 | real_run | slot6 | 6 | 337818518 | 122 | -219388 | -219510 | 0.361141 | -649.426 | -649.787 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 01_11 | real_run | slots5-7 | 5-7 | 337818518 | 398 | -645089 | -645487 | 1.17815 | -1909.57 | -1910.75 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 01_11 | real_run | slots4-8 | 4-8 | 337818518 | 550 | -1.05393e+06 | -1.05448e+06 | 1.62809 | -3119.82 | -3121.44 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 02_54 | real_run | slot6 | 6 | 203681460 | 8 | -133693 | -133701 | 0.039277 | -656.383 | -656.422 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 02_54 | real_run | slots5-7 | 5-7 | 203681460 | 41 | -393111 | -393152 | 0.201295 | -1930.03 | -1930.23 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 02_54 | real_run | slots4-8 | 4-8 | 203681460 | 176 | -642256 | -642432 | 0.864094 | -3153.24 | -3154.1 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 03_31 | training_stub | slot6 | 6 | 363 | 0 | -0.154453 | -0.154453 | 0 | -425.491 | -425.491 | YES | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 03_31 | training_stub | slots5-7 | 5-7 | 363 | 0 | -0.454154 | -0.454154 | 0 | -1251.11 | -1251.11 | YES | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 03_31 | training_stub | slots4-8 | 4-8 | 363 | 0 | -0.741987 | -0.741987 | 0 | -2044.04 | -2044.04 | YES | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 03_43 | real_run | slot6 | 6 | 107109594 | 13 | -70261.7 | -70274.7 | 0.121371 | -655.98 | -656.101 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 03_43 | real_run | slots5-7 | 5-7 | 107109594 | 49 | -206598 | -206647 | 0.457475 | -1928.84 | -1929.3 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |
| 03_43 | real_run | slots4-8 | 4-8 | 107109594 | 151 | -337534 | -337685 | 1.40977 | -3151.3 | -3152.71 | NO | NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs) |

## Notes
- This compares empirical `J_data` (from run*.summary.json) to `J_model` produced by the probability provider.
- Without a real provider, use `--toy_ok` only to sanity-check plumbing; it is **NOT** model-faithful.