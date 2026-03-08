# STRONG verdict (2026-03-03_run02)

## Kanıt dizini

- run: [strong_c5a_paper_run/](strong_c5a_paper_run/)

## Verdict (RUN_OK / MECH_OK / PRED_OK)

- RUN_OK=YES
  - kanıt: [terminal_output_and_exit_code.txt](strong_c5a_paper_run/terminal_output_and_exit_code.txt) + artifacts klasörü
- MECH_OK=YES (anti-fallback ile baseline/proxy kaçış yok)
  - kanıt: [artifacts/rho_summary.json](strong_c5a_paper_run/artifacts/rho_summary.json)
- PRED_OK=NA
  - not: bu koşu “IO closure + integrity” telemetrisi üretiyor; bağımsız holdout/predictive protokol içermiyor.

## “Proxy overlay” kaçış kontrolü (anti-fallback)

- [artifacts/rho_summary.json](strong_c5a_paper_run/artifacts/rho_summary.json) içinde:
  - `anti_fallback.pdg_call_poison_active = true` → PDG fonksiyonları zehirlenmiş.
  - `pdg_baseline_used = false` → PDG baseline overlay kullanılmamış.
  - `io.data_loaded_from_paths = true` → gerçek veri CSV’lerinden okuma yapılmış.

## Not

- Bu run’ın stdout’u boş olabilir; verdict’i artifacts içindeki telemetry/provenance üzerinden verdik.
