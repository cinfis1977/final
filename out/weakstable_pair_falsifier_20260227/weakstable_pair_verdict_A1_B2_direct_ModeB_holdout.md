# Weak-Stable Pair Verdict: A1_B2_direct_ModeB_holdout

## Exact Input Paths
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
- T05: weighted_median_mz=816.217195967, local_spread_mz=0.00564717759039, point_count=3984, summed_intensity=1223670345.22
- T08: weighted_median_mz=816.283346069, local_spread_mz=0.00583972741379, point_count=2200, summed_intensity=1059366417.19
- T09: weighted_median_mz=816.150887869, local_spread_mz=0.00593985744933, point_count=2207, summed_intensity=1080887566.25
- T12: weighted_median_mz=816.349200423, local_spread_mz=0.00562258302239, point_count=2264, summed_intensity=1020850644.41

## Pair Metrics + Comparator (Archived Track8)
- weak_stable_edge_cut (run): 0.337969773763
- edge_band_median_abs_distance (run): 0.0270394479944
- T05<->T12: delta_mz=0.132004455962, sep_norm=0.545462914875, corridor=0.876337090146, rejection=0.123662909854, leak_reduction=0.438168545073, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=STRONG_STABLE, signed_dist=0.000198771309658, abs_dist=0.000198771309658, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist=0, near_edge=True, pair_verdict=BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: delta_mz=0.1324582001, sep_norm=0.546313550316, corridor=0.875939547527, rejection=0.124060452473, leak_reduction=0.437969773763, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, signed_dist=0, abs_dist=0, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist=0, near_edge=True, pair_verdict=BOUNDARY-PROXIMITY-SUPPORTED

## Pair-Level Verdicts
- T05<->T12: BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: BOUNDARY-PROXIMITY-SUPPORTED

Note: local_spread_mz uses weighted MAD fallback (no separate robust spread formula found in project scripts).

