# DM-C2 paper run report

This report is produced by `run_dm_c2_paper_run.py`.
It is an IO/schema + runner-smoke artifact; not an accuracy claim.

- points_csv: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\data\sparc\sparc_points.csv
- n_galaxies: 5
- pack_path: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\log_capture\2026-03-03_run02\dm_c2_paper\pack_dm_c2_sparc.json

## DM-C2 forward

- pack.schema_version: dm_c2_pack_v1
- pack.path: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\log_capture\2026-03-03_run02\dm_c2_paper\pack_dm_c2_sparc.json
- dt: 0.001  n_steps: 300  order_mode: forward
- chi2.total: 1818252.1629112887  ndof: 1500
- boundedness: finite_all=True g_in_0_1=True epsilon_nonneg=True
- DM_POISON_PROXY_CALLS: 1
- stability_not_accuracy: True

## DM-C2 reverse

- pack.schema_version: dm_c2_pack_v1
- pack.path: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\log_capture\2026-03-03_run02\dm_c2_paper\pack_dm_c2_sparc.json
- dt: 0.001  n_steps: 300  order_mode: reverse
- chi2.total: 1818252.1631839795  ndof: 1500
- boundedness: finite_all=True g_in_0_1=True epsilon_nonneg=True
- DM_POISON_PROXY_CALLS: 1
- stability_not_accuracy: True
