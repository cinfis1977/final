# DM verdict (2026-03-03_run02)

## Kanıt dizinleri

- Proxy CV (DM v0): [dm_proxy_paper_run/](dm_proxy_paper_run/)
- Dynamics C1: [dm_c1_dynamics_paper_run/](dm_c1_dynamics_paper_run/)
- Dynamics C2 (real SPARC pack): [dm_c2_realpack_dynamics_paper_run/](dm_c2_realpack_dynamics_paper_run/)
- Dynamics C2 holdout CV: [dm_c2_holdout_cv_paper_run/](dm_c2_holdout_cv_paper_run/)

## Verdict (RUN_OK / MECH_OK / PRED_OK)

### Proxy CV (DM v0)

- RUN_OK=YES
- MECH_OK=NA (proxy koşu; dynamics iddiası yok)
- PRED_OK=LIMITED
  - not: bu CV “predictive” gibi görünebilir ama dynamics core değil; ayrıca burada kullanılan grid tek nokta (`nA=1`, `nAlpha=1`) olduğu için “model araması” kanıtı zayıf.
  - kanıt: [artifacts/dm_cv_none_summary.json](dm_proxy_paper_run/artifacts/dm_cv_none_summary.json), [artifacts/dm_cv_thread_STIFFGATE_summary.json](dm_proxy_paper_run/artifacts/dm_cv_thread_STIFFGATE_summary.json)

### Dynamics C1

- RUN_OK=YES
- MECH_OK=YES (state evolution; proxy overlay yok)
  - kanıt: [artifacts/dm_c1_summary_forward.json](dm_c1_dynamics_paper_run/artifacts/dm_c1_summary_forward.json) (`dm_dynamics_core_used=true`, `proxy_overlay_used=false`, poison aktif)
- PRED_OK=NA
  - not: bu koşu toy/tek-pack üzerinde; gerçek veri holdout protokolü değil.

### Dynamics C2 (real SPARC pack)

- RUN_OK=YES
- MECH_OK=YES (state evolution; proxy overlay yok)
  - kanıt: [artifacts/dm_c2_summary_forward.json](dm_c2_realpack_dynamics_paper_run/artifacts/dm_c2_summary_forward.json), [artifacts/pack_dm_c2_sparc.json](dm_c2_realpack_dynamics_paper_run/artifacts/pack_dm_c2_sparc.json)
- PRED_OK=NA
  - not: bu paper-run bir holdout/selection testi değil.

### Dynamics C2 holdout CV

- RUN_OK=YES
- MECH_OK=YES (leakage guards + poison)
  - kanıt: [artifacts/dm_c2_cv_summary.json](dm_c2_holdout_cv_paper_run/artifacts/dm_c2_cv_summary.json) (`folds_are_galaxy_holdout=true`, `leakage_guard_disjoint_train_test=true`, `train_only_calibration=true`, poison aktif)
- PRED_OK=NO
  - kanıt: aynı summary’de `delta_chi2_test.max=0.0` ve fold’larda `A_best=0.0` → testte iyileşme yok.

## Audit notları

- DM tarafında “proxy overlay’e kayma” açısından en güçlü sinyal: dynamics summary JSON’larında `proxy_overlay_used=false` ve proxy çağrıları için poison aktif olması.
- “Predictive power” iddiası için tek gerçek test C2 holdout CV; bu run02’de o test **başarısız (PRED_OK=NO)**.
