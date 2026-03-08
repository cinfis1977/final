# Integrity & Performance report (run_id=2026-03-03_run02)

- index: [RUN_INDEX_2026-03-03_run02.md](RUN_INDEX_2026-03-03_run02.md)
- gerçek-veri metrikleri (tek sayfa): [REALDATA_SCORECARD_2026-03-03_run02.md](REALDATA_SCORECARD_2026-03-03_run02.md)

## Tanımlar (tek-etiket yok)

- **INTEGRITY_OK** = “çıktı gerçekten hedef mekanizmadan geliyor” kanıtı
  - anti-fallback/poison aktifken de çalışır
  - telemetry/provenance: `*_core_used=true` ve `*_overlay_used=false` / `*_baseline_used=false`
  - (varsa) mapping/assert ve leakage guard bayrakları

- **PERFORMANCE_OK** = “gerçek veri üzerinde predictive/uyum başarımı” kanıtı
  - örn. holdout/CV’de `delta_test > 0`
  - veya $\chi^2/\nu \sim 1$ gibi bir yakınlık ölçütü

> INTEGRITY_OK olmadan PERFORMANCE_OK anlamsızdır.

## Run notu

- `2026-03-03_run01` geçersiz (capture harness exception → `EXIT_CODE:999`).
- Bu rapor sadece `2026-03-03_run02` kanıtlarına dayanır.

## WEAK (T2K)

- INTEGRITY_OK: **YES (GKSL state evolution kanıtı var)**
  - kanıt: [weak/2026-03-03_run02/t2k_gksl_dynamics/terminal_output_and_exit_code.txt](weak/2026-03-03_run02/t2k_gksl_dynamics/terminal_output_and_exit_code.txt) içindeki `GKSL base dm2 ...` ve kanal bazlı döküm
- PERFORMANCE_OK: **NO (yakınlık kötü)**
  - özet metrik: $\chi^2/\nu \approx 726.495/72 \approx 10.09$
  - kanıt: [REALDATA_SCORECARD_2026-03-03_run02.md](REALDATA_SCORECARD_2026-03-03_run02.md)

## STRONG (C5A PDG rho/sigma_tot)

- INTEGRITY_OK: **YES (anti-fallback aktif, baseline overlay yok)**
  - kanıt: [strong/2026-03-03_run02/strong_c5a_paper_run/artifacts/rho_summary.json](strong/2026-03-03_run02/strong_c5a_paper_run/artifacts/rho_summary.json)
    - `anti_fallback.pdg_call_poison_active=true`
    - `pdg_baseline_used=false`
- PERFORMANCE_OK: **NO (yakınlık çok kötü)**
  - özet metrik: $\chi^2/\nu \approx 85.11/4 \approx 21.28$
  - kanıt: [REALDATA_SCORECARD_2026-03-03_run02.md](REALDATA_SCORECARD_2026-03-03_run02.md)

## EM (Bhabha/MuMu paper-run)

- INTEGRITY_OK: **YES (baseline-import overlay yok; beyanlı proxy/IO-closure modu)**
  - kanıt: [em/2026-03-03_run02/em_paper_run/artifacts/bhabha_summary.json](em/2026-03-03_run02/em_paper_run/artifacts/bhabha_summary.json)
    - `telemetry.baseline_import_used=false`
- PERFORMANCE_OK: **NO (yakınlık çok kötü)**
  - özet metrik (Bhabha): $\chi^2/\nu \approx 2040.19/60 \approx 34.00$
  - kanıt: [REALDATA_SCORECARD_2026-03-03_run02.md](REALDATA_SCORECARD_2026-03-03_run02.md)

## DM (proxy CV + C1/C2 dynamics + C2 holdout CV)

- INTEGRITY_OK: **YES (dynamics core kullanımı + proxy overlay kapalı + poison aktif)**
  - kanıt (C1): [dm/2026-03-03_run02/dm_c1_dynamics_paper_run/artifacts/dm_c1_summary_forward.json](dm/2026-03-03_run02/dm_c1_dynamics_paper_run/artifacts/dm_c1_summary_forward.json)
    - `telemetry.dm_dynamics_core_used=true`
    - `telemetry.proxy_overlay_used=false`
    - `telemetry.poison.DM_POISON_PROXY_CALLS="1"`
  - kanıt (C2): [dm/2026-03-03_run02/dm_c2_realpack_dynamics_paper_run/artifacts/dm_c2_summary_forward.json](dm/2026-03-03_run02/dm_c2_realpack_dynamics_paper_run/artifacts/dm_c2_summary_forward.json)
- PERFORMANCE_OK: **NO (holdout CV test iyileşmesi yok)**
  - kanıt: [dm/2026-03-03_run02/dm_c2_holdout_cv_paper_run/artifacts/dm_c2_cv_summary.json](dm/2026-03-03_run02/dm_c2_holdout_cv_paper_run/artifacts/dm_c2_cv_summary.json)
    - `telemetry.delta_chi2_test.max=0.0`
    - `fold_details[*].A_best=0.0`

## Tek satır sonuç

`run02`: INTEGRITY_OK (tüm sektörler) = **YES**; PERFORMANCE_OK (tüm sektörler) = **NO** (bu konfigürasyon/parametrelerle gerçek veriye yakınlık/predictive kanıt yok).
