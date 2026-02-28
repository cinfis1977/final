# Weak-Stable Pair Verdict: A1_B2_ModeA

## Exact Input Paths
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2\ModeA_points.csv`
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
- T05: weighted_median_mz=816.217959189, local_spread_mz=0.00594484495832, point_count=3957, summed_intensity=815321533.443
- T08: weighted_median_mz=816.284638625, local_spread_mz=0.00561186559867, point_count=2098, summed_intensity=802881843.053
- T09: weighted_median_mz=816.150905795, local_spread_mz=0.00592051071089, point_count=2177, summed_intensity=736015253.58
- T12: weighted_median_mz=816.350577437, local_spread_mz=0.0058407449701, point_count=2197, summed_intensity=709420875.946

## Pair Metrics + Comparator (Archived Track8)
- weak_stable_edge_cut (run): 0.337411879697
- edge_band_median_abs_distance (run): 0.0276767459011
- T05<->T12: delta_mz=0.132618248105, sep_norm=0.546612833704, corridor=0.875799366368, rejection=0.124200633632, leak_reduction=0.437899683184, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=STRONG_STABLE, signed_dist=0.000487803486418, abs_dist=0.000487803486418, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist=0, near_edge=True, pair_verdict=BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: delta_mz=0.133732830746, sep_norm=0.54868615909, corridor=0.874823759395, rejection=0.125176240605, leak_reduction=0.437411879697, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, signed_dist=0, abs_dist=0, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist=0, near_edge=True, pair_verdict=BOUNDARY-PROXIMITY-SUPPORTED

## Pair-Level Verdicts
- T05<->T12: BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: BOUNDARY-PROXIMITY-SUPPORTED

Note: local_spread_mz uses weighted MAD fallback (no separate robust spread formula found in project scripts).

