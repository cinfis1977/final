# DM-C2 holdout/CV paper run report

This report is produced by `run_dm_c2_cv_paper_run.py`.
It is a leakage-safety + determinism artifact; not an accuracy claim.

- points_csv: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\data\sparc\sparc_points.csv
- pack_path: out\dm_c2_cv_paper\pack_dm_c2_sparc.json
- out_csv: out\dm_c2_cv_paper\dm_c2_cv.csv
- out_json: out\dm_c2_cv_paper\dm_c2_cv_summary.json

## DM-C2 holdout/CV

- pack.schema_version: dm_c2_pack_v1
- pack.path: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\dm_c2_cv_paper\pack_dm_c2_sparc.json
- kfold: 4  seed: 2026
- dt: 0.001  n_steps: 240  order_mode: forward
- A_grid: [0.0, 0.2]  nA: 21
- delta_chi2_test.min: 0.0
- delta_chi2_test.max: 0.0
- leakage_guard_disjoint_train_test: True
- DM_POISON_PROXY_CALLS: 1
- stability_not_accuracy: True
