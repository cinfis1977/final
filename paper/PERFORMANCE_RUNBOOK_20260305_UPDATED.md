# PERFORMANCE Runbook — sector-by-sector commands + verdicts (drop-in)

**Project root (workdir):** `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git`  
**Rule:** The word **pass** is used **only** for **performance**.

---

## Summary (performance-only)

- **WEAK:** **performance pass**
- **STRONG:** **performance pass** *(rho tension exists, but net improvement is positive)*
- **EM:** **not a performance pass** *(closure ok; Delta chi2 = 0 in both branches)*
- **DM:** **performance pass**
- **MS:** **performance pass** *(internal_only strict run and full ablation both passed)*
- **LIGO:** **performance pass** *(canonical exact branch; locally re-confirmed at OFF20K exact; OFF100K is optional stronger rerun)*

---

## Global criteria used (performance)

- **WEAK:** `TOTAL SCORE > 0`
- **STRONG:** net `Delta chi2 total > 0` (sigma_tot + rho combined)
- **DM:** `telemetry.all_folds_delta_test_positive = true` (k-fold test improvement)
- **MS:** prereg final verdict `PASS` and dynamics stateful integrity true
- **LIGO:** canonical exact GW170814 branch has strong null p-metrics (key: `p_joint_abs_and_minabs`)

---

# 1) WEAK — performance

## Why performance pass
Observed in-session:
- `TOTAL SCORE = 0.489377` (positive)

## Run command
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

py -3 .\score_nova_minos_t2k_penalty.py `
  --runner .\nova_mastereq_forward_kernel_BREATH_THREAD_v2.py `
  --pack_nova .\nova_channels.json `
  --pack_minos .\minos_channels.json `
  --runner_args "--kernel rt --k_rt 180 --A -0.002 --alpha 0.7 --n 0 --E0 1 --omega0_geom fixed --phi 1.57079632679 --zeta 0.05 --rho 2.6 --kappa_gate 0 --T0 1 --mu 0 --eta 0 --breath_B 0.3 --breath_w0 0.0038785 --breath_gamma 0.2 --thread_C 1.5 --thread_w0 -1 --thread_gamma 0.1 --thread_weight_app 0 --thread_weight_dis 1" `
  --t2k_penalty_cli .\t2k_penalty_cli.py `
  --t2k_profiles .\t2k_release_extract\t2k_frequentist_profiles.json `
  --hierarchy NH `
  --rc wRC `
  --s2th23 0.55 `
  --dm2 0.0025 `
  --dcp -1.5
```

---

# 2) STRONG — performance

## Why performance pass
In-session verified:
- sigma_tot: `pp dchi2 = +3.235630`, `pbarp dchi2 = +0.209162`
- rho: `dchi2 = -0.6558912131`
- **Net:** `Delta chi2 total = +2.7889007869` (positive)

## Run commands
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git
New-Item -ItemType Directory -Force .\LOCAL_RUNS\STRONG | Out-Null

# sigma_tot NULL
py -3 .\strong_sigma_tot_energy_scan_v2.py `
  --data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --channel both `
  --A 0 `
  --env_mode none `
  --out .\LOCAL_RUNS\STRONG\sigmatot_NULL.csv `
  --chi2_out .\LOCAL_RUNS\STRONG\sigmatot_NULL_chi2.json

# sigma_tot GEO
py -3 .\strong_sigma_tot_energy_scan_v2.py `
  --data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --channel both `
  --A -0.003 `
  --env_mode eikonal `
  --template cos `
  --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 `
  --c1_abs 0.725147 `
  --out .\LOCAL_RUNS\STRONG\sigmatot_GEO_Aneg003.csv `
  --chi2_out .\LOCAL_RUNS\STRONG\sigmatot_GEO_Aneg003_chi2.json

# rho NULL
py -3 .\strong_rho_energy_scan_v3.py `
  --data .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --channel both `
  --A 0 `
  --env_mode none `
  --out .\LOCAL_RUNS\STRONG\rho_NULL.csv `
  --chi2_out .\LOCAL_RUNS\STRONG\rho_NULL_chi2.json

# rho GEO
py -3 .\strong_rho_energy_scan_v3.py `
  --data .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --channel both `
  --A -0.003 `
  --env_mode eikonal_amp `
  --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 `
  --c1_abs 0.725147 `
  --template cos `
  --out .\LOCAL_RUNS\STRONG\rho_GEO_Aneg003.csv `
  --chi2_out .\LOCAL_RUNS\STRONG\rho_GEO_Aneg003_chi2.json
```

---

# 3) EM — not a performance pass (closure ok)

## Why not a performance pass
Both branches have `Delta chi2 = 0`:
- Bhabha: `chi2_SM == chi2_GEO`
- MuMu: `chi2_SM == chi2_GEO`

## Run commands (for record)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git
New-Item -ItemType Directory -Force .\LOCAL_RUNS\EM | Out-Null

# Bhabha
py -3 .\em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov total `
  --A 0 `
  --out .\LOCAL_RUNS\EM\bhabha_pred.csv `
  --out_json .\LOCAL_RUNS\EM\bhabha_summary.json

# MuMu
py -3 .\em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_mumu_pack.json `
  --cov total `
  --A 0 `
  --out .\LOCAL_RUNS\EM\mumu_pred.csv `
  --out_json .\LOCAL_RUNS\EM\mumu_summary.json
```

---

# 4) DM — performance

## Precondition (bundle fix already done)
`thread_env_model.py` must exist at the project root.

## Why performance pass
Rerun produces `dm_cv_thread_STIFFGATE_summary.json` with:
- `telemetry.all_folds_delta_test_positive = true`

## Run command
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git
New-Item -ItemType Directory -Force .\LOCAL_RUNS\DM | Out-Null

py -3 .\run_dm_paper_run.py `
  --out_dir .\LOCAL_RUNS\DM\dm_paper_pass_A01778_a0001 `
  --points_csv .\data\sparc\sparc_points.csv `
  --kfold 5 `
  --seed 2026 `
  --A 0.1778279410 `
  --alpha 0.001
```

---

# 5) MS — performance

## A) internal_only strict run — performance pass

### Why performance pass
Final prereg file shows:
- `final_verdict = "PASS"`
- `C1_psuccess = true`
- `C2_mad = true`
- `C3_thirdarm = true`

Aggregator shows:
- `prereg_all_pass = true`
- `dynamics_stateful_all = true`

### Run commands (internal_only; validated)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

$runId = "ms_strict_raw_common_local"

New-Item -ItemType Directory -Force ".\out\MS\$runId\internal_only\A1_B2" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\internal_only\A1_B3_holdout" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\internal_only\A2_B3_thirdarm" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\internal_only\final" | Out-Null

# A1_B2
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2\ModeB_points.csv `
  --out_dir ".\out\MS\$runId\internal_only\A1_B2" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation internal_only `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# A1_B3_holdout
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir ".\out\MS\$runId\internal_only\A1_B3_holdout" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation internal_only `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# A2_B3_thirdarm
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A2_B3\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir ".\out\MS\$runId\internal_only\A2_B3_thirdarm" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation internal_only `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# Finalizer
py -3 .\runners\finalize_particle_specific_goodppm_lock_from_runs_v1_0.py `
  --root . `
  --pair_b2_dir ".\out\MS\$runId\internal_only\A1_B2" `
  --pair_b3_dir ".\out\MS\$runId\internal_only\A1_B3_holdout" `
  --third_arm_dir ".\out\MS\$runId\internal_only\A2_B3_thirdarm" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --out_dir ".\out\MS\$runId\internal_only\final" `
  --good_ppm 3 `
  --window_ppm 30 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --mode_a_points .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv `
  --mode_b2_points .\data\MS\particle_specific_cytofull_A1_B2\ModeB_points.csv `
  --mode_b3_points .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --mode_a2_points .\data\MS\particle_specific_cytofull_A2_B3\ModeA_points.csv

# Aggregator
py -3 .\ms_dynamics_integrity_aggregate_v1_DROPIN.py --run_id $runId
```

## B) full ablation — performance pass

### Why performance pass
In-session validated:

#### Final prereg
- `final_verdict = "PASS"`
- `C1_psuccess = true`
- `C2_mad = true`
- `C3_thirdarm = true`

#### Aggregator
- `prereg_all_pass = true`
- `dynamics_stateful_all = true`

#### Telemetry
Across all three full arms:
- `ablation = "full"`
- `internal_dynamics_used = true`
- `thread_env_used = true`
- `stateful_steps_total = 527`

This confirms that the full branch passed with thread environment enabled.

### Run commands (full; validated)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

$runId = "ms_strict_raw_common_full_local"

New-Item -ItemType Directory -Force ".\out\MS\$runId\full\A1_B2" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\full\A1_B3_holdout" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\full\A2_B3_thirdarm" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\full\final" | Out-Null

# A1_B2
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2\ModeB_points.csv `
  --out_dir ".\out\MS\$runId\full\A1_B2" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation full `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# A1_B3_holdout
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir ".\out\MS\$runId\full\A1_B3_holdout" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation full `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# A2_B3_thirdarm
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A2_B3\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir ".\out\MS\$runId\full\A2_B3_thirdarm" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation full `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# Finalizer
py -3 .\runners\finalize_particle_specific_goodppm_lock_from_runs_v1_0.py `
  --root . `
  --pair_b2_dir ".\out\MS\$runId\full\A1_B2" `
  --pair_b3_dir ".\out\MS\$runId\full\A1_B3_holdout" `
  --third_arm_dir ".\out\MS\$runId\full\A2_B3_thirdarm" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --out_dir ".\out\MS\$runId\full\final" `
  --good_ppm 3 `
  --window_ppm 30 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --mode_a_points .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv `
  --mode_b2_points .\data\MS\particle_specific_cytofull_A1_B2\ModeB_points.csv `
  --mode_b3_points .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --mode_a2_points .\data\MS\particle_specific_cytofull_A2_B3\ModeA_points.csv

# Aggregator
py -3 .\ms_dynamics_integrity_aggregate_v1_DROPIN.py --run_id $runId
```

---

# 6) LIGO — performance (canonical exact branch)

## Why performance pass (locally re-confirmed)
Exact OFF20K rerun produced:
- `p_joint_abs_and_minabs = 0.0`
- `p_abs_corr = 0.0295`
- `p_min_abs_corr = 0.0435`

## Canonical exact OFF20K run command (validated)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

py -3 .\gw170814_ringdown_only_null_v1_FIXED_v7_consistency_3det_projected_peakalign_v6_fixedlags.py `
  --h1_hdf5 ".\data\gw\H-H1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --l1_hdf5 ".\data\gw\L-L1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --v1_hdf5 ".\data\gw\V-V1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --model_csv ".\out\LIGO\MODEL_BASIS_HYBRID_lam1e+09.csv" `
  --model_col_plus h_plus_proxy `
  --model_col_cross h_cross_proxy `
  --model_t0peak_col h_plus_proxy `
  --auto_event gw170814 `
  --center_guess_gps 1186741861.0 `
  --anchor_band 150,500 `
  --analysis_band 150,500 `
  --fixed_anchor_lag_s -0.008 `
  --fixed_anchor_lag_h1_v1_s 0.006 `
  --max_model_lag_s 0.0 `
  --ringdown_start_s 0.002 `
  --ringdown_dur_s 0.02 `
  --time_scales 1 `
  --psi_deg 45 `
  --seed 777 `
  --offsource_n 20000 `
  --no_sign_flip `
  --out_prefix ".\out\LIGO\gw170814_HYB_lam1e9_psi45_OFF20K_seed777_EXACT"
```

## Optional: canonical exact OFF100K (stronger, slower)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

py -3 .\gw170814_ringdown_only_null_v1_FIXED_v7_consistency_3det_projected_peakalign_v6_fixedlags.py `
  --h1_hdf5 ".\data\gw\H-H1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --l1_hdf5 ".\data\gw\L-L1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --v1_hdf5 ".\data\gw\V-V1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --model_csv ".\out\LIGO\MODEL_BASIS_HYBRID_lam1e+09.csv" `
  --model_col_plus h_plus_proxy `
  --model_col_cross h_cross_proxy `
  --model_t0peak_col h_plus_proxy `
  --auto_event gw170814 `
  --center_guess_gps 1186741861.0 `
  --anchor_band 150,500 `
  --analysis_band 150,500 `
  --fixed_anchor_lag_s -0.008 `
  --fixed_anchor_lag_h1_v1_s 0.006 `
  --max_model_lag_s 0.0 `
  --ringdown_start_s 0.002 `
  --ringdown_dur_s 0.02 `
  --time_scales 1 `
  --psi_deg 45 `
  --seed 777 `
  --offsource_n 100000 `
  --no_sign_flip `
  --out_prefix ".\out\LIGO\gw170814_HYB_lam1e9_psi45_OFF100K_seed777_EXACT"
```
