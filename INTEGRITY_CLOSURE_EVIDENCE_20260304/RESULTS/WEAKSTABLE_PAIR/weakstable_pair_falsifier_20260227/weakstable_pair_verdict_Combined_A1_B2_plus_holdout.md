# Weak-Stable Pair Verdict: Combined_A1_B2_plus_holdout

## Exact Input Paths
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2\ModeA_points.csv`
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2\ModeB_points.csv`
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv`
- targets_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2_direct\targets_used.csv`
- archived_track8_comparator_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\track8_current_layer_generated_frozen.csv`

## Reference Context Files (Not Threshold Source)
- arm_by_arm_rebuild_rollup.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\arm_by_arm_rebuild_frozen_20260227\arm_by_arm_rebuild_rollup.md`
- rebuilt_two_center_verdict_A1_B2_ModeA.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\arm_by_arm_rebuild_frozen_20260227\rebuilt_two_center_verdict_A1_B2_ModeA.md`
- rebuilt_two_center_verdict_A1_B2_ModeB.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\arm_by_arm_rebuild_frozen_20260227\rebuilt_two_center_verdict_A1_B2_ModeB.md`
- rebuilt_two_center_verdict_A1_B2_direct_ModeB_holdout.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\arm_by_arm_rebuild_frozen_20260227\rebuilt_two_center_verdict_A1_B2_direct_ModeB_holdout.md`
- rebuilt_two_center_verdict_Combined_A1_B2_plus_holdout.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\arm_by_arm_rebuild_frozen_20260227\rebuilt_two_center_verdict_Combined_A1_B2_plus_holdout.md`

## Frozen Thresholds
- width_scale = 1.0
- corridor_min = 0.25
- reject_max = 0.75
- leak_ratio_max = 0.9
- sep_s0 = 0.11
- confidence_quantile = 0.25

## Analyzed Pairs
- T05<->T12
- T09<->T08

## Raw Target Window Stats (T05, T12, T09, T08)
- T05: weighted_median_mz=816.21718903, local_spread_mz=0.00568838836773, point_count=11813, summed_intensity=3028051692.93
- T08: weighted_median_mz=816.283656937, local_spread_mz=0.00586592780007, point_count=6401, summed_intensity=2815416544.17
- T09: weighted_median_mz=816.150842343, local_spread_mz=0.00576875359206, point_count=6462, summed_intensity=2815773946.82
- T12: weighted_median_mz=816.350040313, local_spread_mz=0.00622081525376, point_count=6562, summed_intensity=2604821122.94

## Pair Metrics + Comparator (Archived Track8)
- weak_stable_edge_cut (run): 0.337797649228
- edge_band_median_abs_distance (run): 0.0272453753396
- T05<->T12: delta_mz=0.132851282858, sep_norm=0.547047894064, corridor=0.875595298457, rejection=0.124404701543, leak_reduction=0.437797649228, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, signed_dist=0, abs_dist=0, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist=0, near_edge=True, pair_verdict=BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: delta_mz=0.132814594369, sep_norm=0.546979454486, corridor=0.875627423314, rejection=0.124372576686, leak_reduction=0.437813711657, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=STRONG_STABLE, signed_dist=1.60624288351e-05, abs_dist=1.60624288351e-05, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist=0, near_edge=True, pair_verdict=BOUNDARY-PROXIMITY-SUPPORTED

## Pair-Level Verdicts
- T05<->T12: BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: BOUNDARY-PROXIMITY-SUPPORTED

Note: local_spread_mz uses weighted MAD fallback (no separate robust spread formula found in project scripts).

