# Particle-Specific Final Verdict (Prereg Lock: good_ppm=3.0)

Generated (UTC): 2026-03-03T22:27:13.574230+00:00

## Prereg Lock
- good_ppm: 3.0
- window_ppm: 30.0
- tail3_ppm: -300000.0
- min_n: 8
- max_bins: 8
- targets: `out/MS/real_cyto_3arm_20260304/thread_only/A1_B2/targets_used.csv`

## Core Results
- median_abs_delta_p_success (A1-B2): 0.145193
- median_abs_delta_p_success (A1-B3 holdout): 0.136623
- holdout rank_corr_abs: 0.391608
- nz target count (A1-B2 / A1-B3): 12 / 12
- MAD rank correlation (A1-B2 vs A1-B3): 0.827273
- MAD top target match: T06 vs T06 -> True

## Third-Arm Consistency (A2-B3)
- rank_corr (B2 vs A23): 0.587413
- rank_corr (B3 vs A23): 0.426573
- top target triplet: T02, T09, T03 -> all_match=False

## Criteria
- C1 (p_success signature + holdout stability): False
- C2 (MAD signature stability): True
- C3 (third-arm consistency): False

## Final Verdict
**FAIL**

## Artifact Paths
- JSON lock+verdict: `out/MS/real_cyto_3arm_20260304/thread_only/final/prereg_lock_and_final_verdict_goodppm3.json`
- MD report: `out/MS/real_cyto_3arm_20260304/thread_only/final/FINAL_VERDICT_REPORT_goodppm3.md`
- A1-B2 run dir: `out/MS/real_cyto_3arm_20260304/thread_only/A1_B2`
- A1-B3 holdout run dir: `out/MS/real_cyto_3arm_20260304/thread_only/A1_B3_holdout`
- A2-B3 third-arm run dir: `out/MS/real_cyto_3arm_20260304/thread_only/A2_B3_thirdarm`