# One-for-all real-data diagnostics (2026-03-03_run02)

This report is **fit-free**: it does not optimize parameters. It only audits scoring definitions and highlights where mismatch concentrates.

## WEAK (phase-map (fixedbyclaude))

- source_csv: logs/weak/2026-03-03_run02/t2k_phase_map_fixedbyclaude/artifacts/t2k_phase_map.csv
- totals: sum(obs)=418  sum(pred_sm)=370.288777  obs/pred_sm=1.128849
- loose-chi2: chi2_SM=733.128805  chi2_GEO=732.457362  dchi2=0.671443  (systfrac=0.0, sigma_floor=0.0)
- poisson-dev: chi2_SM=259.210201  chi2_GEO=258.559009  dchi2=0.651192

**Per-channel (loose-chi2)**
| channel | bins | sum(obs) | sum(pred_sm) | chi2_sm_loose | chi2_geo_loose | dchi2_loose |
| --- | --- | --- | --- | --- | --- | --- |
| T2K_app_FHC | 18 | 181 | 151.764706 | 405.655942 | 404.45201 | 1.203932 |
| T2K_app_RHC | 18 | 55 | 44.735294 | 77.723742 | 77.796128 | -0.072386 |
| T2K_dis_FHC | 18 | 136 | 117.830882 | 224.124881 | 224.510635 | -0.385754 |
| T2K_dis_RHC | 18 | 46 | 55.957895 | 25.624241 | 25.698589 | -0.074348 |

**Top 8 loose-chi2 contributors (SM)**
| channel | i | E_ctr | obs | pred_sm | pred_geo | contrib |
| --- | --- | --- | --- | --- | --- | --- |
| T2K_app_FHC | 13 | 0.9 | 22 | 1.102941 | 1.105248 | 395.929608 |
| T2K_dis_FHC | 17 | 2.916667 | 19 | 1.470588 | 1.466168 | 208.950588 |
| T2K_app_RHC | 13 | 0.9 | 9 | 0.529412 | 0.530519 | 71.750865 |
| T2K_dis_RHC | 13 | 2.25 | 0 | 7.831579 | 7.8066 | 7.831579 |
| T2K_dis_FHC | 13 | 2.25 | 19 | 11.397059 | 11.360707 | 5.071898 |
| T2K_app_RHC | 6 | 0.433333 | 7 | 3.264706 | 3.269692 | 4.273715 |
| T2K_dis_RHC | 8 | 1.416667 | 6 | 3.157895 | 3.145724 | 2.557895 |
| T2K_dis_RHC | 6 | 1.083333 | 7 | 3.915789 | 3.89719 | 2.42923 |

| channel | i | E_ctr | obs | pred_sm | pred_geo | contrib |
| --- | --- | --- | --- | --- | --- | --- |
| T2K_app_FHC | 13 | 0.9 | 22 | 1.102941 | 1.105248 | 395.016058 |
| T2K_dis_FHC | 17 | 2.916667 | 19 | 1.470588 | 1.466168 | 209.686217 |
| T2K_app_RHC | 13 | 0.9 | 9 | 0.529412 | 0.530519 | 71.732109 |
| T2K_dis_RHC | 13 | 2.25 | 0 | 7.831579 | 7.8066 | 7.8066 |
| T2K_dis_FHC | 13 | 2.25 | 19 | 11.397059 | 11.360707 | 5.136898 |
| T2K_app_RHC | 6 | 0.433333 | 7 | 3.264706 | 3.269692 | 4.255812 |
| T2K_dis_RHC | 8 | 1.416667 | 6 | 3.157895 | 3.145724 | 2.589829 |
| T2K_dis_RHC | 6 | 1.083333 | 7 | 3.915789 | 3.89719 | 2.470351 |


## WEAK (GKSL dynamics)

- source_csv: logs/weak/2026-03-03_run02/t2k_gksl_dynamics/artifacts/t2k_gksl_dynamics.csv
- totals: sum(obs)=418  sum(pred_sm)=370.288777  obs/pred_sm=1.128849
- loose-chi2: chi2_SM=733.128805  chi2_GEO=726.495389  dchi2=6.633416  (systfrac=0.0, sigma_floor=0.0)
- poisson-dev: chi2_SM=259.210201  chi2_GEO=258.310649  dchi2=0.899552

**Per-channel (loose-chi2)**
| channel | bins | sum(obs) | sum(pred_sm) | chi2_sm_loose | chi2_geo_loose | dchi2_loose |
| --- | --- | --- | --- | --- | --- | --- |
| T2K_app_FHC | 18 | 181 | 151.764706 | 405.655942 | 398.991748 | 6.664194 |
| T2K_app_RHC | 18 | 55 | 44.735294 | 77.723742 | 77.559226 | 0.164516 |
| T2K_dis_FHC | 18 | 136 | 117.830882 | 224.124881 | 224.315409 | -0.190528 |
| T2K_dis_RHC | 18 | 46 | 55.957895 | 25.624241 | 25.629006 | -0.004765 |

**Top 8 loose-chi2 contributors (SM)**
| channel | i | E_ctr | obs | pred_sm | pred_geo | contrib |
| --- | --- | --- | --- | --- | --- | --- |
| T2K_app_FHC | 13 | 0.9 | 22 | 1.102941 | 1.119792 | 395.929608 |
| T2K_dis_FHC | 17 | 2.916667 | 19 | 1.470588 | 1.469544 | 208.950588 |
| T2K_app_RHC | 13 | 0.9 | 9 | 0.529412 | 0.5375 | 71.750865 |
| T2K_dis_RHC | 13 | 2.25 | 0 | 7.831579 | 7.825862 | 7.831579 |
| T2K_dis_FHC | 13 | 2.25 | 19 | 11.397059 | 11.388739 | 5.071898 |
| T2K_app_RHC | 6 | 0.433333 | 7 | 3.264706 | 3.279282 | 4.273715 |
| T2K_dis_RHC | 8 | 1.416667 | 6 | 3.157895 | 3.155385 | 2.557895 |
| T2K_dis_RHC | 6 | 1.083333 | 7 | 3.915789 | 3.912446 | 2.42923 |

| channel | i | E_ctr | obs | pred_sm | pred_geo | contrib |
| --- | --- | --- | --- | --- | --- | --- |
| T2K_app_FHC | 13 | 0.9 | 22 | 1.102941 | 1.119792 | 389.343084 |
| T2K_dis_FHC | 17 | 2.916667 | 19 | 1.470588 | 1.469544 | 209.12399 |
| T2K_app_RHC | 13 | 0.9 | 9 | 0.529412 | 0.5375 | 71.613907 |
| T2K_dis_RHC | 13 | 2.25 | 0 | 7.831579 | 7.825862 | 7.825862 |
| T2K_dis_FHC | 13 | 2.25 | 19 | 11.397059 | 11.388739 | 5.086717 |
| T2K_app_RHC | 6 | 0.433333 | 7 | 3.264706 | 3.279282 | 4.221576 |
| T2K_dis_RHC | 8 | 1.416667 | 6 | 3.157895 | 3.155385 | 2.564451 |
| T2K_dis_RHC | 6 | 1.083333 | 7 | 3.915789 | 3.912446 | 2.436581 |


## EM (Bhabha)

- summary_json: logs/em/2026-03-03_run02/em_paper_run/artifacts/bhabha_summary.json
- pred_csv: logs/em/2026-03-03_run02/em_paper_run/artifacts/bhabha_pred.csv
- cov_csv: C:/Dropbox/projects/new_master_equation_with_gauga_structure_test_git/lep_bhabha_cov_total.csv  (choice=total)
- ndof(summary): 60
- chi2(recomputed): sm=2040.190931  geo=2040.190931  delta=0

**Top 8 |pull| bins (diag(cov) pull; diagnostic)**
| i | pull | resid | cos_ctr | obs | pred_sm |
| --- | --- | --- | --- | --- | --- |
| 59 | 25.158652 | 219.50769 | 0.855 | 565 | 345.49231 |
| 14 | 22.862292 | 260.50769 | 0.855 | 606 | 345.49231 |
| 44 | 22.196886 | 232.50769 | 0.855 | 578 | 345.49231 |
| 29 | 17.31088 | 260.50769 | 0.855 | 606 | 345.49231 |
| 13 | 11.795098 | 62.47832 | 0.765 | 194 | 131.52168 |
| 58 | 9.8567 | 42.47832 | 0.765 | 174 | 131.52168 |
| 49 | -8.099535 | -3.242417 | -0.09 | 2.8 | 6.042417 |
| 43 | 7.899129 | 41.47832 | 0.765 | 173 | 131.52168 |

Note: With correlated systematics, per-bin pulls are only diagnostic; the official chi2 is the full cov form.


## EM (MuMu)

- summary_json: logs/em/2026-03-03_run02/em_paper_run/artifacts/mumu_summary.json
- pred_csv: logs/em/2026-03-03_run02/em_paper_run/artifacts/mumu_pred.csv
- cov_csv: C:/Dropbox/projects/new_master_equation_with_gauga_structure_test_git/lep_mumu_cov_total.csv  (choice=total)
- ndof(summary): 30
- chi2(recomputed): sm=18.606787  geo=18.606787  delta=0

**Top 8 |pull| bins (diag(cov) pull; diagnostic)**
| i | pull | resid | cos_ctr | obs | pred_sm |
| --- | --- | --- | --- | --- | --- |
| 24 | -1.596869 | -0.407312 | -0.1 | 0.54 | 0.947312 |
| 14 | 1.546293 | 1.082911 | -0.1 | 1.9 | 0.817089 |
| 4 | 1.424572 | 0.2714 | -0.1 | 1.27 | 0.9986 |
| 25 | 1.415527 | 0.425484 | 0.1 | 1.7 | 1.274516 |
| 20 | -1.122457 | -0.325521 | -0.9 | 0.19 | 0.515521 |
| 21 | -1.009012 | -0.211915 | -0.7 | 0.28 | 0.491915 |
| 19 | -0.998479 | -1.098535 | 0.9 | 1.9 | 2.998535 |
| 6 | 0.946545 | 0.237579 | 0.3 | 2.03 | 1.792421 |

Note: With correlated systematics, per-bin pulls are only diagnostic; the official chi2 is the full cov form.


## STRONG (sigma_tot)

- summary_json: logs/strong/2026-03-03_run02/strong_c5a_paper_run/artifacts/sigma_tot_summary.json
- pred_csv: logs/strong/2026-03-03_run02/strong_c5a_paper_run/artifacts/sigma_tot_pred.csv
- cov_csv: C:/Dropbox/projects/new_master_equation_with_gauga_structure_test_git/integration_artifacts/mastereq/packs/strong_c5a/pdg_sigma_tot_cov_diag.csv
- ndof(summary): 22
- chi2(recomputed): 8812.930059

**Top 8 |pull| points (diag(cov) pull; diagnostic)**
| i | pull | resid | sqrts_GeV | obs | pred |
| --- | --- | --- | --- | --- | --- |
| 18 | -63.419547 | -9.512932 | 52.8 | 42.38 | 51.892932 |
| 19 | -34.156244 | -8.539061 | 44.7 | 41.8 | 50.339061 |
| 20 | -33.421041 | -6.684208 | 30.6 | 40.15 | 46.834208 |
| 16 | -32.019727 | -9.926115 | 62.5 | 43.55 | 53.476115 |
| 21 | -21.251023 | -5.312756 | 23.5 | 39.1 | 44.412756 |
| 15 | -19.233359 | -23.08003 | 200 | 41.6 | 64.68003 |
| 13 | -14.514331 | -13.498328 | 546 | 61.26 | 74.758328 |
| 17 | -10.495482 | -9.445934 | 62.3 | 44 | 53.445934 |


## STRONG (rho)

- summary_json: logs/strong/2026-03-03_run02/strong_c5a_paper_run/artifacts/rho_summary.json
- pred_csv: logs/strong/2026-03-03_run02/strong_c5a_paper_run/artifacts/rho_pred.csv
- ndof(summary): 4
- chi2(recomputed): 85.112325

**Top 8 |pull| points (diag(cov) pull; diagnostic)**
| i | pull | resid | sqrts_GeV | obs | pred |
| --- | --- | --- | --- | --- | --- |
| 0 | 5.838673 | 0.08758 | 541 | 0.135 | 0.04742 |
| 3 | 5.099271 | 0.056092 | 13000 | 0.098 | 0.041908 |
| 2 | 4.809198 | 0.048092 | 13000 | 0.09 | 0.041908 |
| 1 | 1.375234 | 0.094891 | 1800 | 0.14 | 0.045109 |


## DM (C2 holdout CV)

- summary_json: logs/dm/2026-03-03_run02/dm_c2_holdout_cv_paper_run/artifacts/dm_c2_cv_summary.json
- cv_csv: logs/dm/2026-03-03_run02/dm_c2_holdout_cv_paper_run/artifacts/dm_c2_cv.csv
- params: A_min=0.0  A_max=0.2  nA=21  kfold=4
- A_best(unique): [0.0]
- max |delta_chi2_train| across folds: 0
- max |delta_chi2_test| across folds: 0
- interpretation: A collapses to 0 in every fold -> either (a) A has near-zero effect under current scoring/dynamics, or (b) scoring/clamps make A ineffective.

