# Final prereg run command list (for Codex)

> Run everything from the **repo root**. No absolute local paths.  
> Convention: `A=0` = NULL reference; `A!=0` = GEO modulation (single-shot, scan‑free).

## 0) Setup (optional but recommended)

```powershell
New-Item -ItemType Directory -Force -Path .\out\WEAK,.\out\STRONG,.\out\EM,.\out\LIGO | Out-Null
```

---

## Latest PASS bundle (v3)

For the most recent consolidated commands (WEAK/STRONG/EM/DM + DM integrity-pack driver), use:

- `CODEX_FINAL_RUN_COMMANDS_v3.txt`

The DM integrity-pack driver is `run_dm_thread_integrity_pack_v1.py` and writes a scorecard under `out/DM/...`.

---

## 1) WEAK verdict (single parameter set; T2K as official penalty term)

### 1.1 T2K penalty (official frequentist profiles)

```powershell
py -3 .	2k_penalty_cli.py `
  --profiles .	2k_release_extract	2k_frequentist_profiles.json `
  --hierarchy NH `
  --rc wRC `
  --s2th23 0.55 `
  --dm2 0.0025 `
  --dcp -1.5
```

**Codex output capture:** parse `TOTAL_dchi2_penalty` from stdout.

### 1.2 Weak composite score (NOvA + MINOS − T2K penalty)

```powershell
py -3 .\score_nova_minos_t2k_penalty.py `
  --runner .
ova_mastereq_forward_kernel_BREATH_THREAD_v2.py `
  --pack_nova  .
ova_channels.json `
  --pack_minos .\minos_channels.json `
  --runner_args "--kernel rt --k_rt 180 --A -0.002 --alpha 0.7 --n 0 --E0 1 --omega0_geom fixed --phi 1.57079632679 --zeta 0.05 --rho 2.6 --kappa_gate 0 --T0 1 --mu 0 --eta 0 --breath_B 0.3 --breath_w0 0.0038785 --breath_gamma 0.2 --thread_C 1.5 --thread_w0 -1 --thread_gamma 0.1 --thread_weight_app 0 --thread_weight_dis 1" `
  --t2k_penalty_cli .	2k_penalty_cli.py `
  --t2k_profiles .	2k_release_extract	2k_frequentist_profiles.json `
  --hierarchy NH `
  --rc wRC `
  --s2th23 0.55 `
  --dm2 0.0025 `
  --dcp -1.5
```

**Codex output capture:** parse lines:
- `dchi2_NOvA = ...`
- `dchi2_MINOS = ...`
- `T2K penalty = ...`
- `TOTAL SCORE = ...`

### 1.3 (Sanity-only) T2K forward on approx pack (do not include in score)

```powershell
py -3 .
ova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py `
  --pack .	2k_channels_real_approx.json `
  --kernel rt --k_rt 180 `
  --A -0.002 --alpha 0.7 --n 0 --E0 1 `
  --omega0_geom fixed --L0_km 295 `
  --phi 1.57079632679 --zeta 0.05 `
  --rho 2.6 --kappa_gate 0 --T0 1 --mu 0 --eta 0 `
  --bin_shift_app 0 --bin_shift_dis 0 `
  --breath_B 0.3 --breath_w0 0.00387850944887629 --breath_gamma 0.2 `
  --thread_C 1.0 --thread_w0 0.00387850944887629 --thread_gamma 0.2 `
  --thread_weight_app 0 --thread_weight_dis 1 `
  --out .\out\WEAK	2k_BREATH_THREAD_validation_APPROXREAL.csv
```

---

## 2) STRONG verdict (sector-total; σ_tot drives PASS; ρ may be flagged as tension)

### 2.1 σ_tot (NULL + GEO)

```powershell
py -3 .\strong_sigma_tot_energy_scan_v2.py `
  --data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --channel both `
  --A 0 `
  --env_mode none `
  --out .\out\STRONG\sigmatot_NULL.csv `
  --chi2_out .\out\STRONG\sigmatot_NULL_chi2.json

py -3 .\strong_sigma_tot_energy_scan_v2.py `
  --data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --channel both `
  --A -0.003 `
  --env_mode eikonal --template cos --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 --c1_abs 0.725147 `
  --out .\out\STRONG\sigmatot_GEO_Aneg003.csv `
  --chi2_out .\out\STRONG\sigmatot_GEO_Aneg003_chi2.json
```

### 2.2 ρ (NULL + GEO)

```powershell
py -3 .\strong_rho_energy_scan_v3.py `
  --data .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --channel both `
  --A 0 `
  --env_mode none `
  --out .\out\STRONG
ho_NULL.csv `
  --chi2_out .\out\STRONG
ho_NULL_chi2.json

py -3 .\strong_rho_energy_scan_v3.py `
  --data .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --channel both `
  --A -0.003 `
  --env_mode eikonal_amp --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 --c1_abs 0.725147 `
  --template cos `
  --out .\out\STRONG
ho_GEO_Aneg003.csv `
  --chi2_out .\out\STRONG
ho_GEO_Aneg003_chi2.json
```

### 2.3 ρ_from_σ_tot_dispersion (optional consistency check)

```powershell
py -3 .\strong_rho_from_sigmatot_dispersion_v1.py `
  --sigma_data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --rho_data   .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --A 0 `
  --env_mode none --template cos `
  --out .\out\STRONG
ho_from_sig_NULL.csv `
  --chi2_out .\out\STRONG
ho_from_sig_NULL_chi2.json

py -3 .\strong_rho_from_sigmatot_dispersion_v1.py `
  --sigma_data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --rho_data   .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --A -0.003 `
  --env_mode eikonal --template cos `
  --sqrts_ref_GeV 13000 --delta_geo_ref -1.315523 --c1_abs 0.725147 `
  --out .\out\STRONG
ho_from_sig_GEO_Aneg003.csv `
  --chi2_out .\out\STRONG
ho_from_sig_GEO_Aneg003_chi2.json
```

**Codex metric rule:**
- For each channel, compute `Δχ² = chi2_NULL − chi2_GEO` using the `*_chi2.json` files.
- Sector-total: `Δχ²_STRONG,total = Δχ²_sigma_tot + Δχ²_rho`.
- If `Δχ²_rho < 0` but sector-total > 0 → report **PASS with ρ tension/investigating**.

---

## 3) DM verdict (SPARC/RAR) — PASS (scan-free)

```powershell
py -3 .\dm_holdout_cv_thread_STIFFGATE.py `
  --points_csv .\data\sparc\sparc_points.csv `
  --model geo_add_const --g0 1.2e-10 `
  --env_model thread `
  --thread_mode down --thread_q 0.6 --thread_xi 0.5 --thread_norm median `
  --thread_gate_p 4 --thread_k2 1.0 `
  --thread_calibrate_from_galaxy --gal_hi_p 99.9 --gal_gate_eps 1e-6 --thread_Sc_factor 10 `
  --A_min 0.1778279410 --A_max 0.1778279410 --nA 1 `
  --alpha_min 0.001 --alpha_max 0.001 --nAlpha 1 `
  --kfold 5 --seed 2026 `
  --out_csv .\out\dm_cv_thread_STIFFGATE_FIXED_A01778_a0001_seed2026_k5.csv

py -3 .\dm_holdout_cv_thread.py `
  --points_csv .\data\sparc\sparc_points.csv `
  --model geo_add_const --g0 1.2e-10 `
  --env_model none `
  --A_min 0.1778279410 --A_max 0.1778279410 --nA 1 `
  --alpha_min 0.001 --alpha_max 0.001 --nAlpha 1 `
  --kfold 5 --seed 2026 `
  --out_csv .\out\dm_cv_NONE_FIXED_A01778_a0001_seed2026_k5.csv
```

**Codex verdict rule:** PASS iff **all 5 folds** have `Δχ²_test > 0`.

---

## 4) LIGO verdict — GW170814 OFF100K confirmation (ψ=30°,45°)

### 4.1 Generate PLUS/CROSS bases

```powershell
py -3 .\improved_simulation_STABLE_v17_xy_quadrupole_drive_ANISO_PHYS_TENSOR_PHYS_FIXED4.py `
  --sim_seconds 0.2 --dt 0.00005 --save_every 10 --snapshot_dt 0.0002 `
  --nx 6 --mass 1 --tension 1 --radius 1 --kappa 0.0 --c0 0.4 `
  --drift_type gaussian --drift_sigma 0.02 `
  --drive_pattern quad_plus_xy --drive_gain 20 `
  --readout_split x `
  --out_csv .\out\LIGO\gate0_split\PLUS.csv

py -3 .\improved_simulation_STABLE_v17_xy_quadrupole_drive_ANISO_PHYS_TENSOR_PHYS_FIXED4.py `
  --sim_seconds 0.2 --dt 0.00005 --save_every 10 --snapshot_dt 0.0002 `
  --nx 6 --mass 1 --tension 1 --radius 1 --kappa 0.0 --c0 0.4 `
  --drift_type gaussian --drift_sigma 0.02 `
  --drive_pattern quad_cross_xy --drive_gain 20 `
  --readout_split x `
  --out_csv .\out\LIGO\gate0_split\CROSS.csv
```

### 4.2 Hybrid basis (λ=1e9)

```powershell
py -3 .uild_hybrid_basis.py `
  --plus_csv  .\out\LIGO\gate0_split\PLUS.csv `
  --cross_csv .\out\LIGO\gate0_split\CROSS.csv `
  --out_csv   .\out\LIGO\MODEL_BASIS_HYBRID_lam1e+09.csv `
  --lam 1000000000
```

### 4.3 GW170814 OFF100K runs (ψ=30°,45°)

```powershell
py -3 .\gw170814_ringdown_only_null_v1_FIXED_v7_consistency_3det_projected_peakalign_v6_fixedlags.py `
  --auto_event gw170814 `
  --basis_csv .\out\LIGO\MODEL_BASIS_HYBRID_lam1e+09.csv `
  --psi 30 `
  --seed 777 `
  --offsource_n 100000 `
  --tukey_alpha 0.2 `
  --bandpass_low 30 --bandpass_high 450 `
  --whiten_method psd_interp `
  --offsource_stride 0.5 `
  --lag_H1 -0.008 --lag_L1 0.0 --lag_V1 0.006 `
  --time_scale_H1 1.0 --time_scale_L1 1.0 --time_scale_V1 1.0 `
  --out_json .\out\LIGO\gw170814_OFF100K_psi30.json

py -3 .\gw170814_ringdown_only_null_v1_FIXED_v7_consistency_3det_projected_peakalign_v6_fixedlags.py `
  --auto_event gw170814 `
  --basis_csv .\out\LIGO\MODEL_BASIS_HYBRID_lam1e+09.csv `
  --psi 45 `
  --seed 777 `
  --offsource_n 100000 `
  --tukey_alpha 0.2 `
  --bandpass_low 30 --bandpass_high 450 `
  --whiten_method psd_interp `
  --offsource_stride 0.5 `
  --lag_H1 -0.008 --lag_L1 0.0 --lag_V1 0.006 `
  --time_scale_H1 1.0 --time_scale_L1 1.0 --time_scale_V1 1.0 `
  --out_json .\out\LIGO\gw170814_OFF100K_psi45.json
```

**Codex verdict capture:** read `p_joint` from each JSON; report as confirmation.

---

## 5) MS (Mass Spectrometry) — particle-specific, integrity-gated dynamics (3-arm)

Runs the three prereg arms (A1–B2 discovery, A1–B3 holdout, A2–B3 third-arm) using the
explicit-dynamics scan-series runner, then calls the prereg finalizer.

Outputs under `out/MS/<run_id>/<ablation>/...` including `final/FINAL_VERDICT_REPORT_goodppm3.md`.

```powershell
py -3 .\run_ms_particle_specific_dynamic_3arm_v1_0.py `
  --run_id 20260304_MS_DYNAMIC `
  --mode_a1_points .\path\to\A1_points.csv `
  --mode_b2_points .\path\to\B2_points.csv `
  --mode_b3_points .\path\to\B3_points.csv `
  --mode_a2_points .\path\to\A2_points.csv `
  --targets_csv .\path\to\targets.csv `
  --ablations internal_only thread_only full `
  --window_ppm 30 --good_ppm 3 --min_n 8 --max_bins 8 `
  --alpha 0.30 --alpha_g_floor 0.25
```

## 6) EM prereg (LEP Bhabha; shape-only)

### 5.1 NULL / GEO / sign-flip

```powershell
py -3 .\em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov diag_total `
  --baseline_csv .hagen_cos09_v4_baseline_L0_Sp1.csv `
  --baseline_col sm_pred_pb --baseline_group_col group_id `
  --shape_only --freeze_betas --beta_nonneg `
  --A 0 --alpha 7.5e-05 --phi 1.57079632679 `
  --out .\out\EMhabha_diag_A0.csv

py -3 .\em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov diag_total `
  --baseline_csv .hagen_cos09_v4_baseline_L0_Sp1.csv `
  --baseline_col sm_pred_pb --baseline_group_col group_id `
  --shape_only --freeze_betas --beta_nonneg `
  --A 100000 --alpha 7.5e-05 --phi 1.57079632679 `
  --out .\out\EMhabha_diag_A1e5.csv

py -3 .\em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov diag_total `
  --baseline_csv .hagen_cos09_v4_baseline_L0_Sp1.csv `
  --baseline_col sm_pred_pb --baseline_group_col group_id `
  --shape_only --freeze_betas --beta_nonneg `
  --A -100000 --alpha 7.5e-05 --phi 1.57079632679 `
  --out .\out\EMhabha_diag_Aneg1e5.csv
```

### 5.2 Predictive holdout

```powershell
py -3 .\em_bhabha_holdout_contiguous_centerpivot_v1_2.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov diag_total `
  --baseline_csv .hagen_cos09_v4_baseline_L0_Sp1.csv `
  --baseline_col sm_pred_pb --baseline_group_col group_id `
  --shape_only --freeze_betas --beta_nonneg `
  --pivot_mode center `
  --A 100000 --alpha 7.5e-05 --phi 1.57079632679 `
  --out .\out\EMhabha_holdout_diag_A1e5.csv
```

### 5.3 μμ sanity

```powershell
py -3 .\em_mumu_forward.py `
  --pack .\data\hepdata\lep_mumu_pack.json `
  --cov total `
  --A 0 --alpha 7.5e-05 --phi 1.57079632679 `
  --out .\out\EM\mumu_A0.csv
```

---

## 7) “Do NOT use” list (hard rules)

- `t2k_channels.json` (deprecated / never use).
- Any DM command with `--nA > 1` or `--nAlpha > 1` (scan; forbidden for final verdict).
- Any “pick best run from a grid” logic (forbidden for final verdict).
