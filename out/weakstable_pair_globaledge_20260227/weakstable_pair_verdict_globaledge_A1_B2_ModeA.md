# Weak-Stable Global-Edge Verdict: A1_B2_ModeA

## Exact Input Paths
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2\ModeA_points.csv`
- targets_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2_direct\targets_used.csv`
- archived_track8_comparator_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\track8_current_layer_generated_frozen.csv`

## Reference-Only Context
- weakstable_pair_falsifier_rollup.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\weakstable_pair_falsifier_20260227\weakstable_pair_falsifier_rollup.md`
- weakstable_pair_verdict_A1_B2_ModeA.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\weakstable_pair_falsifier_20260227\weakstable_pair_verdict_A1_B2_ModeA.md`
- weakstable_pair_verdict_A1_B2_ModeB.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\weakstable_pair_falsifier_20260227\weakstable_pair_verdict_A1_B2_ModeB.md`
- weakstable_pair_verdict_A1_B2_direct_ModeB_holdout.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\weakstable_pair_falsifier_20260227\weakstable_pair_verdict_A1_B2_direct_ModeB_holdout.md`
- weakstable_pair_verdict_Combined_A1_B2_plus_holdout.md: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\weakstable_pair_falsifier_20260227\weakstable_pair_verdict_Combined_A1_B2_plus_holdout.md`

## Frozen Thresholds
- width_scale = 1.0
- corridor_min = 0.25
- reject_max = 0.75
- leak_ratio_max = 0.9
- sep_s0 = 0.11
- confidence_quantile = 0.25

## Single Global Frozen Weak-Stable Edge
- global_frozen_weak_stable_edge = 0.33904771546
- global_edge_band_median_abs_distance = 0.022510457733

## Analyzed Pairs
- T05<->T12
- T09<->T08

## Raw Target Window Stats
- T05: weighted_median_mz=816.217959189, local_spread_mz=0.00594484495832, point_count=3957, summed_intensity=815321533.443
- T08: weighted_median_mz=816.284638625, local_spread_mz=0.00561186559867, point_count=2098, summed_intensity=802881843.053
- T09: weighted_median_mz=816.150905795, local_spread_mz=0.00592051071089, point_count=2177, summed_intensity=736015253.58
- T12: weighted_median_mz=816.350577437, local_spread_mz=0.0058407449701, point_count=2197, summed_intensity=709420875.946

## Pair Metrics + Archived Comparator
- T05<->T12: delta_mz=0.132618248105, sep_norm=0.546612833704, overlap=0.875799366368, corridor=0.875799366368, rejection=0.124200633632, leak_reduction=0.437899683184, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, stable_margin=0.625799366368, signed_dist_global=-0.00114803227637, abs_dist_global=0.00114803227637, near_global_edge=True, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist_global=0
- T08<->T09: delta_mz=0.133732830746, sep_norm=0.54868615909, overlap=0.874823759395, corridor=0.874823759395, rejection=0.125176240605, leak_reduction=0.437411879697, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, stable_margin=0.624823759395, signed_dist_global=-0.00163583576279, abs_dist_global=0.00163583576279, near_global_edge=True, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist_global=0

## Pair-Level Verdicts
- T05<->T12: GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED

Note: local_spread_mz uses weighted MAD fallback (no separate robust spread method found in current project scripts).

