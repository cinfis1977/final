# Weak-Stable Global-Edge Verdict: Combined_A1_B2_plus_holdout

## Exact Input Paths
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2\ModeA_points.csv`
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2\ModeB_points.csv`
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv`
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
- T05: weighted_median_mz=816.21718903, local_spread_mz=0.00568838836773, point_count=11813, summed_intensity=3028051692.93
- T08: weighted_median_mz=816.283656937, local_spread_mz=0.00586592780007, point_count=6401, summed_intensity=2815416544.17
- T09: weighted_median_mz=816.150842343, local_spread_mz=0.00576875359206, point_count=6462, summed_intensity=2815773946.82
- T12: weighted_median_mz=816.350040313, local_spread_mz=0.00622081525376, point_count=6562, summed_intensity=2604821122.94

## Pair Metrics + Archived Comparator
- T05<->T12: delta_mz=0.132851282858, sep_norm=0.547047894064, overlap=0.875595298457, corridor=0.875595298457, rejection=0.124404701543, leak_reduction=0.437797649228, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, stable_margin=0.625595298457, signed_dist_global=-0.00125006623195, abs_dist_global=0.00125006623195, near_global_edge=True, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist_global=0
- T08<->T09: delta_mz=0.132814594369, sep_norm=0.546979454486, overlap=0.875627423314, corridor=0.875627423314, rejection=0.124372576686, leak_reduction=0.437813711657, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, stable_margin=0.625627423314, signed_dist_global=-0.00123400380311, abs_dist_global=0.00123400380311, near_global_edge=True, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist_global=0

## Pair-Level Verdicts
- T05<->T12: GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED

Note: local_spread_mz uses weighted MAD fallback (no separate robust spread method found in current project scripts).

