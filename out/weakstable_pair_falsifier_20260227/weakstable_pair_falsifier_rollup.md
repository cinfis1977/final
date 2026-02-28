# Weak-Stable Pair Falsifier Rollup

| run | pair | base_label | confidence | signed_dist | abs_dist | near_edge | conf_changed_vs_track8 | pair_verdict |
|---|---|---|---|---:|---:|---|---|---|
| A1_B2_ModeA | T05<->T12 | STABLE-INTERMEDIATE-CANDIDATE | STRONG_STABLE | 0.000487803486418 | 0.000487803486418 | True | True | BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_ModeA | T08<->T09 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | 0 | 0 | True | False | BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_ModeB | T05<->T12 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | 0 | 0 | True | False | BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_ModeB | T08<->T09 | STABLE-INTERMEDIATE-CANDIDATE | STRONG_STABLE | 0.000156503678871 | 0.000156503678871 | True | True | BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_direct_ModeB_holdout | T05<->T12 | STABLE-INTERMEDIATE-CANDIDATE | STRONG_STABLE | 0.000198771309658 | 0.000198771309658 | True | True | BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_direct_ModeB_holdout | T08<->T09 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | 0 | 0 | True | False | BOUNDARY-PROXIMITY-SUPPORTED |
| Combined_A1_B2_plus_holdout | T05<->T12 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | 0 | 0 | True | False | BOUNDARY-PROXIMITY-SUPPORTED |
| Combined_A1_B2_plus_holdout | T08<->T09 | STABLE-INTERMEDIATE-CANDIDATE | STRONG_STABLE | 1.60624288351e-05 | 1.60624288351e-05 | True | True | BOUNDARY-PROXIMITY-SUPPORTED |

## Explicit Answers
1. Is T05<->T12 a genuine weak-stable boundary pair across arms? **YES**
2. Is T09<->T08 a genuine weak-stable boundary pair across arms? **YES**
3. Are observed confidence drifts physically consistent with boundary proximity? **YES**
4. Or does the confidence layer appear too sharp? **NO**

