# Weak-Stable Global-Edge Falsifier Rollup

- global_frozen_weak_stable_edge: 0.33904771546
- global_edge_band_median_abs_distance: 0.022510457733

| run | pair | base_label | confidence | signed_dist_global | abs_dist_global | near_global_edge | conf_changed_vs_track8 | pair_verdict |
|---|---|---|---|---:|---:|---|---|---|
| A1_B2_ModeA | T05<->T12 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | -0.00114803227637 | 0.00114803227637 | True | False | GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_ModeA | T08<->T09 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | -0.00163583576279 | 0.00163583576279 | True | False | GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_ModeB | T05<->T12 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | -0.0012108823733 | 0.0012108823733 | True | False | GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_ModeB | T08<->T09 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | -0.00105437869443 | 0.00105437869443 | True | False | GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_direct_ModeB_holdout | T05<->T12 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | -0.000879170387197 | 0.000879170387197 | True | False | GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED |
| A1_B2_direct_ModeB_holdout | T08<->T09 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | -0.00107794169686 | 0.00107794169686 | True | False | GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED |
| Combined_A1_B2_plus_holdout | T05<->T12 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | -0.00125006623195 | 0.00125006623195 | True | False | GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED |
| Combined_A1_B2_plus_holdout | T08<->T09 | STABLE-INTERMEDIATE-CANDIDATE | WEAK_STABLE | -0.00123400380311 | 0.00123400380311 | True | False | GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED |

## Explicit Answers
1. Is T05<->T12 still a genuine weak-stable boundary pair under one single frozen edge? **GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED**
2. Is T09<->T08 still a genuine weak-stable boundary pair under one single frozen edge? **GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED**
3. Are observed confidence drifts still physically consistent with boundary proximity under one single frozen edge? **YES**
4. Or were earlier near-edge conclusions dependent on run-specific edge recalculation? **NO**

