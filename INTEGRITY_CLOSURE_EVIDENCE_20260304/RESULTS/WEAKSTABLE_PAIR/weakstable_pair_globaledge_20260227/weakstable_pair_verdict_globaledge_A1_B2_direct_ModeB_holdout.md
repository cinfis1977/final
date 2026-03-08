# Weak-Stable Global-Edge Verdict: A1_B2_direct_ModeB_holdout

## Exact Input Paths
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
- T05: weighted_median_mz=816.217195967, local_spread_mz=0.00564717759039, point_count=3984, summed_intensity=1223670345.22
- T08: weighted_median_mz=816.283346069, local_spread_mz=0.00583972741379, point_count=2200, summed_intensity=1059366417.19
- T09: weighted_median_mz=816.150887869, local_spread_mz=0.00593985744933, point_count=2207, summed_intensity=1080887566.25
- T12: weighted_median_mz=816.349200423, local_spread_mz=0.00562258302239, point_count=2264, summed_intensity=1020850644.41

## Pair Metrics + Archived Comparator
- T05<->T12: delta_mz=0.132004455962, sep_norm=0.545462914875, overlap=0.876337090146, corridor=0.876337090146, rejection=0.123662909854, leak_reduction=0.438168545073, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, stable_margin=0.626337090146, signed_dist_global=-0.000879170387197, abs_dist_global=0.000879170387197, near_global_edge=True, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist_global=0
- T08<->T09: delta_mz=0.1324582001, sep_norm=0.546313550316, overlap=0.875939547527, corridor=0.875939547527, rejection=0.124060452473, leak_reduction=0.437969773763, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, stable_margin=0.625939547527, signed_dist_global=-0.00107794169686, abs_dist_global=0.00107794169686, near_global_edge=True, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist_global=0

## Pair-Level Verdicts
- T05<->T12: GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED

Note: local_spread_mz uses weighted MAD fallback (no separate robust spread method found in current project scripts).

