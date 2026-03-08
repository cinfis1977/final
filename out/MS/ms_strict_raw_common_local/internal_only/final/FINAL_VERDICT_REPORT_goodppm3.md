# Particle-Specific Final Verdict (Prereg Lock: good_ppm=3.0)

Generated (UTC): 2026-03-04T08:32:08.822555+00:00

## Prereg Lock
- good_ppm: 3.0
- window_ppm: 30.0
- tail3_ppm: -300000.0
- min_n: 8
- max_bins: 8
- targets: `INPUTS/MS/particle_specific_cytofull_A1_B2_direct/targets_used.csv`

## Core Results
- median_abs_delta_p_success (A1-B2): 0.116172
- median_abs_delta_p_success (A1-B3 holdout): 0.119307
- holdout rank_corr_abs: 0.965035
- nz target count (A1-B2 / A1-B3): 12 / 12
- MAD rank correlation (A1-B2 vs A1-B3): 0.836364
- MAD top target match: T01 vs T01 -> True

## Third-Arm Consistency (A2-B3)
- rank_corr (B2 vs A23): 0.853147
- rank_corr (B3 vs A23): 0.853147
- top target triplet: T03, T03, T03 -> all_match=True

## Criteria
- C1 (p_success signature + holdout stability): True
- C2 (MAD signature stability): True
- C3 (third-arm consistency): True

## Final Verdict
**PASS**

## Artifact Paths
- JSON lock+verdict: `out/MS/ms_strict_raw_common_local/internal_only/final/prereg_lock_and_final_verdict_goodppm3.json`
- MD report: `out/MS/ms_strict_raw_common_local/internal_only/final/FINAL_VERDICT_REPORT_goodppm3.md`
- A1-B2 run dir: `out/MS/ms_strict_raw_common_local/internal_only/A1_B2`
- A1-B3 holdout run dir: `out/MS/ms_strict_raw_common_local/internal_only/A1_B3_holdout`
- A2-B3 third-arm run dir: `out/MS/ms_strict_raw_common_local/internal_only/A2_B3_thirdarm`