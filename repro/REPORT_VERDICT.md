# Group Verdict Report

- Source summary: `repro/run_summary.csv`
- Groups: 6
- Verdict counts: {"UNKNOWN": 5, "NA": 1}

| group_id | sector | verdict | data_ok | required_runs | present_runs | notes | logs |
|---|---|---|---|---|---|---|---|
| STRONG_rho_data_hepdata_pdg_rho_clean_for_runner_csv | STRONG | UNKNOWN | YES | A=0 and A=-0.003 | A=-0.003 | required A=0 and A=-0.003 runs not both present | [repro/logs/013_UNSPECIFIED_strong_rho_energy_scan_v3.log](logs/013_UNSPECIFIED_strong_rho_energy_scan_v3.log) |
| STRONG_sigma_tot_data_hepdata_pdg_sigma_tot_clean_for_runner_csv | STRONG | UNKNOWN | YES | A=0 and A=-0.003 | A=-0.003 | required A=0 and A=-0.003 runs not both present | [repro/logs/012_UNSPECIFIED_strong_sigma_tot_energy_scan_v2.log](logs/012_UNSPECIFIED_strong_sigma_tot_energy_scan_v2.log) |
| WEAK_minos_single | WEAK | UNKNOWN | NO | 1 | 3 | no chi2 markers produced | [repro/logs/009_UNSPECIFIED_nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.log](logs/009_UNSPECIFIED_nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.log) [repro/logs/010_UNSPECIFIED_nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.log](logs/010_UNSPECIFIED_nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.log) [repro/logs/011_UNSPECIFIED_nova_mastereq_forward_kernel_BREATH_THREAD_v2.log](logs/011_UNSPECIFIED_nova_mastereq_forward_kernel_BREATH_THREAD_v2.log) |
| LIGO_pattern_generation | LIGO | NA | NO_DATA | drive_pattern=quad_plus_xy and quad_cross_xy | 0 | pattern generation only, no data input |  |
| DM_prereg | DM | UNKNOWN | YES | >=1 PASS prereg run | 2 | PASS runs present; group-level rule not specified | [repro/logs/014_UNSPECIFIED_dm_holdout_cv_thread_STIFFGATE.log](logs/014_UNSPECIFIED_dm_holdout_cv_thread_STIFFGATE.log) [repro/logs/015_UNSPECIFIED_dm_holdout_cv_thread.log](logs/015_UNSPECIFIED_dm_holdout_cv_thread.log) |
| EM_prereg | EM | UNKNOWN | NO | >=1 PASS prereg run | 9 | PASS runs present; group-level rule not specified | [repro/logs/001_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/001_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log) [repro/logs/002_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/002_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log) [repro/logs/003_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/003_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log) [repro/logs/004_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/004_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log) [repro/logs/005_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/005_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log) [repro/logs/006_UNSPECIFIED_em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/006_UNSPECIFIED_em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.log) [repro/logs/007_UNSPECIFIED_em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/007_UNSPECIFIED_em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.log) [repro/logs/008_UNSPECIFIED_em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/008_UNSPECIFIED_em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.log) [repro/logs/016_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log](logs/016_UNSPECIFIED_em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.log) |

## Metrics JSON

- `STRONG_rho_data_hepdata_pdg_rho_clean_for_runner_csv`: `{"runner_family": "rho", "dataset": "data\\hepdata\\pdg_rho_clean_for_runner.csv", "a_values_present": [-0.003]}`
- `STRONG_sigma_tot_data_hepdata_pdg_sigma_tot_clean_for_runner_csv`: `{"runner_family": "sigma_tot", "dataset": "data\\hepdata\\pdg_sigma_tot_clean_for_runner.csv", "a_values_present": [-0.003]}`
- `WEAK_minos_single`: `{"chi2_marker_present": false}`
- `LIGO_pattern_generation`: `{"patterns": []}`
- `DM_prereg`: `{}`
- `EM_prereg`: `{}`
