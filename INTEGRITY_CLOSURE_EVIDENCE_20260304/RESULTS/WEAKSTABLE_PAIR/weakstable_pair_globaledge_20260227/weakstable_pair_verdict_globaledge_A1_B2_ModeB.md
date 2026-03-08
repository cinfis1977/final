# Weak-Stable Global-Edge Verdict: A1_B2_ModeB

## Exact Input Paths
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2\ModeB_points.csv`
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
- T05: weighted_median_mz=816.216700724, local_spread_mz=0.00585622364611, point_count=3872, summed_intensity=989059814.268
- T08: weighted_median_mz=816.283246744, local_spread_mz=0.00557023221677, point_count=2103, summed_intensity=953168283.929
- T09: weighted_median_mz=816.150842343, local_spread_mz=0.00568253617155, point_count=2078, summed_intensity=998871126.984
- T12: weighted_median_mz=816.349462508, local_spread_mz=0.00605581433342, point_count=2101, summed_intensity=874549602.585

## Pair Metrics + Archived Comparator
- T05<->T12: delta_mz=0.13276178465, sep_norm=0.546880905664, overlap=0.875673666174, corridor=0.875673666174, rejection=0.124326333826, leak_reduction=0.437836833087, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, stable_margin=0.625673666174, signed_dist_global=-0.0012108823733, abs_dist_global=0.0012108823733, near_global_edge=True, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist_global=0
- T08<->T09: delta_mz=0.132404401025, sep_norm=0.546212859441, overlap=0.875986673532, corridor=0.875986673532, rejection=0.124013326468, leak_reduction=0.437993336766, base_label=STABLE-INTERMEDIATE-CANDIDATE, boundary_confidence=WEAK_STABLE, stable_margin=0.625986673532, signed_dist_global=-0.00105437869443, abs_dist_global=0.00105437869443, near_global_edge=True, comp_label=STABLE-INTERMEDIATE-CANDIDATE, comp_conf=WEAK_STABLE, comp_signed_dist_global=0

## Pair-Level Verdicts
- T05<->T12: GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED
- T08<->T09: GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED

Note: local_spread_mz uses weighted MAD fallback (no separate robust spread method found in current project scripts).

