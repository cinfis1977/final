# Two-Center Diagnostic Rebuild Verdict

## Inputs
- targets_csv: `C:\Dropbox\projects\new_master_equation_with_gauge_structure_test\out\particle_specific_cytofull_A1_B2_direct\targets_used.csv`
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauge_structure_test\out\particle_specific_cytofull_A1_B2\ModeA_points.csv`
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauge_structure_test\out\particle_specific_cytofull_A1_B2\ModeB_points.csv`
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauge_structure_test\out\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv`
- raw_points: `C:\Dropbox\projects\new_master_equation_with_gauge_structure_test\out\particle_specific_cytofull_A2_B3\ModeA_points.csv`
- current_two_center_csv: `C:\Dropbox\projects\new_master_equation_with_gauge_structure_test\paper\Two_Center_Shadow_Pair_Classification_Track5_v1_PREPAPER_live.csv`

## Frozen Base Logic
- fitting: none
- pair discipline: adjacent + next_nearest
- label logic: preserved (corridor/reject/leak thresholding)
- inferred width_scale: `1`
- inferred corridor_min: `0.25`
- inferred reject_max: `0.75`
- inferred leak_ratio_max: `0.9`
- inferred sep_s0: `0.11`

## Comparison Summary
- matched_pairs: **21**
- only_current_pairs: **0**
- only_rebuilt_pairs: **0**
- classification_changes: **0**
- boundary_confidence_changes: **9**
- max_abs_delta_mz_diff: **0.026265323464**
- max_abs_corridor_proxy_diff: **0.0236921946042**

## Artifacts
- rebuilt_target_windows_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\two_center_raw_rebuild_20260227\rebuilt_target_windows.csv`
- rebuilt_pair_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\two_center_raw_rebuild_20260227\rebuilt_two_center_pair_metrics.csv`
- comparison_csv: `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\two_center_raw_rebuild_20260227\rebuilt_vs_current_comparison.csv`

## Verdict
- **PASS-DIAGNOSTIC-REBUILD**

