# Verdict Reproducer Commands — MASTER

> This is the **canonical master command reference** for the repository.
> It collects the current reproducibility commands across **all sectors**:
> WEAK, STRONG, EM, DM, GW / LIGO, FT-ICR mass spectrometry, Entanglement, and Photon.
>
> Important status boundary:
> - Commands collected here are the current **canonical reproducibility commands**.
> - Their presence in this file does **not** mean every sector is a current **performance-pass** sector.
> - Entanglement / Photon commands included here currently belong to **audit / bridge / prereg** lines unless explicitly upgraded later.
>
> Use this file as the single reference when you want to know:
> **“Where are all current run commands?”**

---

## WEAK (neutrino)

```powershell
py -3 .\nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py `
  --pack .\t2k_channels.json `
  --kernel rt --k_rt 180 `
  --A=-0.002 --alpha=0.7 --n 0 --E0 1 `
  --omega0_geom fixed --L0_km 295 `
  --phi 1.57079632679 --zeta 0.05 `
  --rho 2.6 --kappa_gate 0 --T0 1 --mu 0 --eta 0 `
  --bin_shift_app 0 --bin_shift_dis 0 `
  --breath_B 0.3 --breath_w0 0.0038785094488762877 --breath_gamma 0.2 `
  --thread_C 1.5 --thread_w0 -1 --thread_gamma 0.1 `
  --thread_weight_app 0 --thread_weight_dis 1 `
  --out ".\out\WEAK\t2k_BREATH_THREAD_C1.5_g0.1.csv"
```

```powershell
py -3 .\nova_mastereq_forward_kernel_BREATH_THREAD_v2.py `
  --pack .\minos_channels.json `
  --out .\out\minos_real_L0_735_gateON.csv `
  --kernel rt --k_rt 180 `
  --A -0.002 --alpha 0.7 --n 0 --E0 1 `
  --omega0_geom fixed --L0_km 735 `
  --phi 1.57079632679 --zeta 0.05 `
  --breath_B 0.3 --breath_w0 0.0038785094488762877 --breath_gamma 0.2 `
  --thread_C 1.5 --thread_w0 -1 --thread_gamma 0.1 `
  --thread_weight_app 0 --thread_weight_dis 1 `
  --thread_gate_mode resonant --thread_gate_band 1 `
  --rho 2.8 --Ye 0.5
```

```powershell
py -3 .\run_curvedcube_predict_dcp_v6.py --ordering IO --t2k_rc wRC --A 1e-3 --k_rt 180 --phi 1.57079632679 --zeta 0.05 --geo_dcp_mode du_phase
```

---

## STRONG (hadronic forward / total)

```powershell
py -3 .\strong_elastic_forward_dropin_ascii.py `
  --pack atlas13_pp_elastic_pack.json `
  --cov total `
  --A 0.0085 --alpha 7.5e-05 --phi 1.57079632679 `
  --geo_structure offdiag --geo_gen lam2 `
  --omega0_geom fixed --L0_km 810 `
  --zeta 0.05 --R_max 10 --t_ref_GeV 0.02 `
  --out .\out_strong_debug.csv
```

```powershell
py -3 .\strong_sigma_tot_energy_scan_v2.py `
  --data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --channel both `
  --A 0 `
  --env_mode eikonal --template cos --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 --c1_abs 0.725147 `
  --out .\out_sigmatot_NULL.csv `
  --chi2_out .\out_sigmatot_NULL_chi2.json
```

```powershell
py -3 .\strong_sigma_tot_energy_scan_v2.py `
  --data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --channel both `
  --A -0.003 `
  --env_mode eikonal --template cos --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 --c1_abs 0.725147 `
  --out .\out_sigmatot_GEO_Aneg003.csv `
  --chi2_out .\out_sigmatot_GEO_Aneg003_chi2.json
```

```powershell
py -3 .\strong_rho_energy_scan_v3.py `
  --data .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --channel both `
  --A 0 `
  --env_mode none `
  --out .\out_rho_NULL.csv `
  --chi2_out .\out_rho_NULL_chi2.json
```

```powershell
py -3 .\strong_rho_energy_scan_v3.py `
  --data .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --channel both `
  --A -0.003 `
  --env_mode eikonal_amp --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 --c1_abs 0.725147 `
  --template cos `
  --out .\out_rho_GEO_eikonalamp_Aneg003.csv `
  --chi2_out .\out_rho_GEO_eikonalamp_Aneg003_chi2.json
```

```powershell
py -3 .\strong_rho_from_sigmatot_dispersion_v1.py `
  --sigma_data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --rho_data   .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --A 0 `
  --env_mode eikonal --template cos --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 --c1_abs 0.725147 `
  --out .\out_rho_from_sig_NULL.csv `
  --chi2_out .\out_rho_from_sig_NULL_chi2.json
```

```powershell
py -3 .\strong_rho_from_sigmatot_dispersion_v1.py `
  --sigma_data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --rho_data   .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --A -0.003 `
  --env_mode eikonal --template cos --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 --c1_abs 0.725147 `
  --out .\out_rho_from_sig_GEO_Aneg003.csv `
  --chi2_out .\out_rho_from_sig_GEO_Aneg003_chi2.json
```

```powershell
py -3 .\strong_elastic_cni_rho_bridge_v1_ENV_AIAR_FIX2.py `
  --pack .\data\hepdata\totem13_rho_cni_ins1654549\elastic_pack.json `
  --cov total --rcond 1e-12 `
  --tmax 0.01 `
  --sigma_tot_mb 110.5 --rho 0.10 --B 20.0 `
  --A -0.003 `
  --geo_mode du_phase --template cos --s_map frac `
  --k_rt 180 --phi 1.57079632679 --zeta 0.05 `
  --env_z 0 `
  --out .\out_cni_GEO_Aneg003.csv `
  --chi2_out .\out_cni_GEO_Aneg003_chi2.json
```

---

## DM (SPARC / RAR)

```powershell
py -3 dm_fit_rar_mastereq_thread_STIFFGATE_v2.py `
  --points_csv .\data\sparc\sparc_points.csv `
  --model geo_add_const --g0 1.2e-10 `
  --env_model thread `
  --thread_mode down --thread_q 0.6 --thread_xi 0.5 --thread_norm median `
  --thread_gate_p 4 --thread_k2 1.0 `
  --thread_calibrate_from_galaxy --gal_hi_p 99.9 --gal_gate_eps 1e-6 --thread_Sc_factor 10 `
  --A_min 1e-6 --A_max 1e4 --nA 81 `
  --alpha_min 0.001 --alpha_max 2.0 --nAlpha 61 `
  --out_prefix .\out\dm_rar_thread_stiff_gate_autocal
```

```powershell
py -3 dm_holdout_cv_thread_STIFFGATE_v2.py `
  --points_csv .\data\sparc\sparc_points.csv `
  --model geo_add_const --g0 1.2e-10 `
  --env_model thread `
  --thread_mode down --thread_q 0.6 --thread_xi 0.5 --thread_norm median `
  --thread_gate_p 4 --thread_k2 1.0 `
  --thread_calibrate_from_galaxy --gal_hi_p 99.9 --gal_gate_eps 1e-6 --thread_Sc_factor 10 `
  --A_min 1e-6 --A_max 1e4 --nA 81 `
  --alpha_min 0.001 --alpha_max 2.0 --nAlpha 61 `
  --kfold 5 --seed 1 `
  --out_csv .\out\dm_cv_thread_stiff_gate_autocal_seed1_k5.csv
```

```powershell
py -3 dm_holdout_cv_thread_STIFFGATE_v2.py `
  --points_csv .\data\sparc\sparc_points.csv `
  --model geo_add_const --g0 1.2e-10 `
  --env_model none `
  --A_min 1e-6 --A_max 1e4 --nA 81 `
  --alpha_min 0.001 --alpha_max 2.0 --nAlpha 61 `
  --kfold 5 --seed 1 `
  --out_csv .\out\dm_cv_NONE_seed1_k5.csv
```

```powershell
py -3 .\dm_report_summary_v2.py `
  --cv_csv .\out\dm_cv_thread_stiff_gate_autocal_seed1_k5.csv,.\out\dm_cv_thread_stiff_gate_autocal_seed2_k5.csv,.\out\dm_cv_thread_stiff_gate_autocal_seed3_k5.csv,.\out\dm_cv_NONE_seed1_k5.csv,.\out\dm_cv_NONE_seed2_k5.csv,.\out\dm_cv_NONE_seed3_k5.csv `
  --labels thread_seed1,thread_seed2,thread_seed3,none_seed1,none_seed2,none_seed3 `
  --fit_summary_json .\out\dm_rar_thread_stiff_gate_autocal.summary.json `
  --out_prefix .\out\dm_report_thread_vs_none_seeds1_3
```

---

## LIGO (ringdown / detector projection)

```powershell
py -3 .\universe_fullgeom_action_sim_v9_TT2plane_energycols_backreact_fix4_rtface16_pulse_strictclosed_syncenergy_kappapost_leapfrog_detproj_LAL_RINGDOWN_TT_XCHECK_FIX3.py `
  --out_csv .\out\LIGO_MIN\GW150914_2PHASE_sim.csv `
  --event_utc 2015-09-14T09:50:45.391Z `
  --duration 0.2 --steps 16384 `
  --ringdown_drive --ring_f0_hz 250 --ring_tau_s 0.004 `
  --ring_t_start 0.0 --ring_t_end 0.02 `
  --sky_ra_deg 0 --sky_dec_deg 0 --pol_psi_deg 0 `
  --proj_detectors H1,L1
```

```powershell
py -3 .\gw150914_ringdown_only_null_v1_FIXED_v7_consistency_3det_projected_peakalign_v6_fixedlags.py `
  --h1_hdf5 .\data\gw\H-H1_GWOSC_4KHZ_R1-1186741846-32.hdf5 `
  --l1_hdf5 .\data\gw\L-L1_GWOSC_4KHZ_R1-1186741846-32.hdf5 `
  --v1_hdf5 .\data\gw\V-V1_GWOSC_4KHZ_R1-1186741846-32.hdf5 `
  --model_csv .\out\bh_network_response_SIM_QXY_T0AUTO250_v17.csv `
  --t_col t_s --model_col h_plus_proxy --model_t0peak_col h_plus_proxy `
  --center_guess_gps 1186741861.0 `
  --anchor_band 150,450 --analysis_band 80,300 `
  --ringdown_start_s 0.0 --ringdown_dur_s 0.04 `
  --time_scales 1 --max_model_lag_s 0 --no_sign_flip `
  --fixed_anchor_lag_s -0.008 `
  --fixed_anchor_lag_h1_v1_s 0.006 `
  --offsource_n 20000 --seed 777 `
  --out_prefix .\out\gw170814_ringdown_SIM_QXY_v17_projected_FIXEDLAGS_OFF20K `
  --plot_png
```

```powershell
py -3 .\improved_simulation_STABLE_v17_xy_quadrupole_drive_ANISO_PHYS_TENSOR_PHYS_FIXED4.py `
  --nx 6 --ny 6 --nz 1 `
  --target_inner_f_hz 320 `
  --k_out 140000 --c_out 40 `
  --k_diag 140000,110000,140000 --c_diag 40,35,40 `
  --k_rot_deg 22.5,0,0 --c_rot_deg 22.5,0,0 `
  --tensor_mode full `
  --readout_split x `
  --drive_pattern quad_plus_xy `
  --out_csv ".\out\gate0_split\PLUS.csv"
```

```powershell
py -3 .\improved_simulation_STABLE_v17_xy_quadrupole_drive_ANISO_PHYS_TENSOR_PHYS_FIXED4.py `
  --nx 6 --ny 6 --nz 1 `
  --target_inner_f_hz 320 `
  --k_out 140000 --c_out 40 `
  --k_diag 140000,110000,140000 --c_diag 40,35,40 `
  --k_rot_deg 22.5,0,0 --c_rot_deg 22.5,0,0 `
  --tensor_mode full `
  --readout_split x `
  --drive_pattern quad_cross_xy `
  --out_csv ".\out\gate0_split\CROSS.csv"
```

---

## EM/QED (Bhabha + μμ)

```powershell
py -3 .\em_mumu_forward.py `
  --pack .\data\hepdata\lep_mumu_pack.json `
  --cov total `
  --A 0 --alpha 7.5e-05 --phi 1.57079632679 `
  --out .\out_em_mumu_A0.csv
```

```powershell
py -3 .\em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov diag_total `
  --baseline_csv .\bhagen_cos09_v4_baseline_L0_Sp1.csv `
  --baseline_col sm_pred_pb --baseline_group_col group_id `
  --A 0 --alpha 7.5e-05 --phi 1.57079632679 `
  --geo_structure offdiag --geo_gen lam2 `
  --omega0_geom fixed --L0_km 810 `
  --zeta 0.05 --R_max 10 --t_ref_GeV 0.02 `
  --shape_only --freeze_betas --beta_nonneg `
  --out .\out_em_bhabha_diag_A0.csv
```

```powershell
py -3 .\em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov diag_total `
  --baseline_csv .\bhagen_cos09_v4_baseline_L0_Sp1.csv `
  --baseline_col sm_pred_pb --baseline_group_col group_id `
  --A 100000 --alpha 7.5e-05 --phi 1.57079632679 `
  --geo_structure offdiag --geo_gen lam2 `
  --omega0_geom fixed --L0_km 810 `
  --zeta 0.05 --R_max 10 --t_ref_GeV 0.02 `
  --shape_only --freeze_betas --beta_nonneg `
  --out .\out_em_bhabha_diag_A1e5.csv
```

```powershell
py -3 .\em_bhabha_holdout_contiguous_centerpivot_v1_2.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov diag_total `
  --baseline_csv .\bhagen_cos09_v4_baseline_L0_Sp1.csv `
  --baseline_col sm_pred_pb --baseline_group_col group_id `
  --A 100000 --alpha 7.5e-05 --phi 1.57079632679 `
  --geo_structure offdiag --geo_gen lam2 `
  --omega0_geom fixed --L0_km 810 `
  --zeta 0.05 --R_max 10 --t_ref_GeV 0.02 `
  --shape_only --freeze_betas --beta_nonneg `
  --pivot_mode center `
  --out .\out_em_bhabha_holdout_diag_A1e5.csv
```

---

## Entanglement — CHSH / coincidence export / memory / data-side Bell audit

### E1. NIST HDF5 click-bitpair audit (schema / sanity audit)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_nist_hdf5_click_bitpair_audit_v1_DROPIN_SELFCONTAINED.ps1 `
  -H5Path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  -OutDir "out" `
  -Prefix "nist_h5bitpair_audit"
```

### E2. NIST HDF5 -> coincidence CSV export (Bridge-E0 helper)

> Current canonical coincidence export wrapper for the paper-facing entanglement bridge line.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_nist_hdf5_export_coinc_bridgeE0_v1_2_1_DROPIN_SELFCONTAINED.ps1 `
  -Hdf5Path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  -DownloadRun '' `
  -OutcomeMode half `
  -OutCsv "out\nist_run4_coincidences.csv" `
  -SchemaTxt "out\nist_hdf5_schema_v1.txt" `
  -DebugTxt "out\nist_hdf5_export_debug_v1.txt"
```

### E3. Coincidence CSV audit (gap-binned bridge audit)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_audit_nist_coinc_csv_bridgeE0_v1_DROPIN_SELFCONTAINED.ps1 `
  -InCsv ".\out\nist_run4_coincidences.csv" `
  -GapBins 24 `
  -LogGapBins `
  -OutDir "out" `
  -Prefix "coinc_audit"
```

### E4. Preregistered entanglement-memory diagnostic (no fit)

> This is the current memory-statistic diagnostic line.
> It is **not** a first-principles Bell derivation.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_entanglement_memory_from_coinc_csv_v1_DROPIN_SELFCONTAINED.ps1 `
  -InCsv ".\out\nist_run4_coincidences.csv" `
  -NBins 12 `
  -LogGapBins `
  -KSigma 2.0 `
  -GlobalCHSHCheck `
  -NullGapShuffle `
  -NullOutcomeShuffle `
  -NullReps 200 `
  -OutCsv "out\entanglement_memory_prereg_v1.csv"
```

### E5. Data-side CH/Eberhard Bell audit — overall run summaries

> Current paper-facing verified branch = **slots 4–8**.

```powershell
py -3 .\CODE\nist_build_hdf5_ch_eberhard_runner_v1_DROPIN.py `
  --h5_path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  --slots "4-8" `
  --out_prefix ".\out\nist_ch\run03_43_slots4_8"
```

```powershell
py -3 .\CODE\nist_build_hdf5_ch_eberhard_runner_v1_DROPIN.py `
  --h5_path ".\data\nist\hdf5\2015_09_18\01_11_CH_pockel_100kHz.run4.afterTimingfix.dat.compressed.build.hdf5" `
  --slots "4-8" `
  --out_prefix ".\out\nist_ch\run01_11_slots4_8"
```

```powershell
py -3 .\CODE\nist_build_hdf5_ch_eberhard_runner_v1_DROPIN.py `
  --h5_path ".\data\nist\hdf5\2015_09_18\02_54_CH_pockel_100kHz.run4.afterTimingfix2.dat.compressed.build.hdf5" `
  --slots "4-8" `
  --out_prefix ".\out\nist_ch\run02_54_slots4_8"
```

### E6. Data-side CH/Eberhard Bell audit — split stability summaries (v1.1 global settings mapping)

> Use this branch for split diagnostics and scorecards.  
> This is still **data-side audit**, not model-side Bell closure.

```powershell
py -3 .\CODE\nist_ch_j_timesplits_v1_1_DROPIN.py `
  --h5_path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  --slots "4-8" `
  --n_splits 10 `
  --out_prefix ".\out\nist_ch_splits\run03_43_slots4_8_v1_1"
```

```powershell
py -3 .\CODE\nist_ch_j_timesplits_v1_1_DROPIN.py `
  --h5_path ".\data\nist\hdf5\2015_09_18\01_11_CH_pockel_100kHz.run4.afterTimingfix.dat.compressed.build.hdf5" `
  --slots "4-8" `
  --n_splits 10 `
  --out_prefix ".\out\nist_ch_splits\run01_11_slots4_8_v1_1"
```

```powershell
py -3 .\CODE\nist_ch_j_timesplits_v1_1_DROPIN.py `
  --h5_path ".\data\nist\hdf5\2015_09_18\02_54_CH_pockel_100kHz.run4.afterTimingfix2.dat.compressed.build.hdf5" `
  --slots "4-8" `
  --n_splits 10 `
  --out_prefix ".\out\nist_ch_splits\run02_54_slots4_8_v1_1"
```

### E7. CH/Eberhard split scorecard (v1.1 branch)

```powershell
py -3 .\CODE\nist_ch_j_splits_scorecard_v1_DROPIN.py `
  --in_glob ".\out\nist_ch_splits\*_v1_1.splits.csv" `
  --out_csv ".\out\nist_ch_splits\CH_J_SPLITS_SCORECARD.csv" `
  --out_md  ".\out\nist_ch_splits\CH_J_SPLITS_SCORECARD.md"
```

### Entanglement boundary note

The commands above establish the following current repo lines:

- CHSH / coincidence **audit**
- entanglement-memory **diagnostic**
- data-side CH/Eberhard **Bell audit**

They do **not** constitute a first-principles dynamic Bell performance pass.  
The missing layer remains: model-generated \(J_{\mathrm{model}}\) / \(E^{\mathrm{model}}_{ab}\) from locked \(H_s\), \(\mathcal{D}_s\), and a measurement map.

---

## Photon — bridge / prereg / falsifier commands

### P1. Accumulation-law prereg (signed / default metric)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_birefringence_accumulation_v1_DROPIN_SELFCONTAINED_FIX.ps1 `
  -OutCsv "out\birefringence_accumulation_prereg_v1.csv"
```

### P2. Accumulation-law prereg (absolute-metric variant)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_birefringence_accumulation_v1_DROPIN_SELFCONTAINED_FIX.ps1 `
  -AbsTest `
  -OutCsv "out\birefringence_accumulation_prereg_abs_v1.csv"
```

### P3. CMB birefringence prereg lock

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_cmb_birefringence_v1_DROPIN_SELFCONTAINED.ps1 `
  -OutCsv "out\cmb_birefringence_prereg_v1.csv"
```

### P4. Sky-fold anisotropy falsifier

> If this wrapper exists in the repo under the expected locked name, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_birefringence_skyfold_v1_DROPIN_SELFCONTAINED_FIX.ps1 `
  -OutCsv "out\birefringence_skyfold_prereg_v1.csv"
```

### Photon boundary note

The commands above establish the current photon line as:

- locked accumulation-law bridge observable
- optional absolute-metric variant
- CMB holdout-style prereg lock
- sky-fold falsifier

This is a functioning **bridge / falsification** layer.  
It is **not yet** a first-principles photon propagation performance closure.

---

## What should NOT be mixed into the main performance table

Do **not** treat the following as current performance-pass commands:

- CHSH decorrelation audit wrapper
- entanglement-memory diagnostic
- data-side CH/Eberhard J audit
- photon accumulation-law bridge runs
- CMB birefringence prereg lock
- sky-fold falsifier

These belong in an **audit / bridge / prereg command catalog**, not in the current performance-pass runbook.
