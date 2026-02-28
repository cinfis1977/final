# Rebuilt Two-Center Verdict (Frozen Audit)

## Input Paths (Exact)
- raw_point_01: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv`
- targets_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\particle_specific_cytofull_A1_B2_direct\targets_used.csv`
- track8_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\track8_current_layer_generated_frozen.csv`
- track8_script: ``
- track8_comparator_used: `track8_csv:C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\track8_current_layer_generated_frozen.csv`

## Frozen Thresholds (Ex-Ante)
- width_scale: `1.0`
- corridor_min: `0.25`
- reject_max: `0.75`
- leak_ratio_max: `0.9`
- sep_s0: `0.11`
- confidence_quantile: `0.25`

## Comparison Summary
- matched_pairs: **21**
- only_track8_pairs: **0**
- only_rebuilt_pairs: **0**
- classification_changes: **0**
- confidence_changes: **1**

## Shell Distribution (Rebuilt)
- adjacent / REPULSIVE: 3
- adjacent / STABLE-INTERMEDIATE-CANDIDATE: 8
- next_nearest / REPULSIVE: 5
- next_nearest / STABLE-INTERMEDIATE-CANDIDATE: 5

## Shell Monotonicity
- status: **OK**
- adjacent_stable_fraction: 0.727272727273
- next_nearest_stable_fraction: 0.5
- adjacent_median_delta_mz: 0.108297784726
- next_nearest_median_delta_mz: 29.1574322157

## Watch Anchors
- T02<->T03: track8=STABLE-INTERMEDIATE-CANDIDATE -> rebuilt=STABLE-INTERMEDIATE-CANDIDATE, bc_track8=STRONG_STABLE -> bc_rebuilt=STRONG_STABLE
- T12<->T07: track8=REPULSIVE -> rebuilt=REPULSIVE, bc_track8=STRONG_REPULSIVE -> bc_rebuilt=STRONG_REPULSIVE

## Verdict
- **PASS-DIAGNOSTIC-REBUILD**

