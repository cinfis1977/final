# Real-data scorecard (run_id=2026-03-03_run02)

Bu dosya **tek amaç** içindir: “gerçek veriyle uyum ne durumda?” sorusunu tek sayfada sayılarla göstermek.

- kaynak index: [RUN_INDEX_2026-03-03_run02.md](RUN_INDEX_2026-03-03_run02.md)
- mekanizma/overlay bayrakları ayrı rapor: [VERDICT_2026-03-03_run02.md](VERDICT_2026-03-03_run02.md)
- fit-siz “one-for-all” teşhis raporu (bin/pull/top katkılar): [ONEFORALL_DIAGNOSTICS_2026-03-03_run02.md](ONEFORALL_DIAGNOSTICS_2026-03-03_run02.md)
- WEAK χ² inşası (neden “debug distance”): [CHI2_CONSTRUCTION_AUDIT_WEAK_2026-03-03_run02.md](CHI2_CONSTRUCTION_AUDIT_WEAK_2026-03-03_run02.md)
- WEAK metrik duyarlılığı (aynı pred, farklı χ² tanımı): [WEAK_METRIC_SENSITIVITY_2026-03-03_run02_vs_run05.md](WEAK_METRIC_SENSITIVITY_2026-03-03_run02_vs_run05.md)

## Metri̇k tanımı

- Uyum için en temel sayı: $\chi^2$ ve mümkünse $\chi^2/\nu$ (burada $\nu$ = `ndof`).
- DM holdout CV için: `delta_chi2_test` (pozitifse testte iyileşme var).

## WEAK (T2K)

Kaynaklar:
- phase-map çıktısı: [logs/weak/2026-03-03_run02/t2k_phase_map_fixedbyclaude/terminal_output_and_exit_code.txt](weak/2026-03-03_run02/t2k_phase_map_fixedbyclaude/terminal_output_and_exit_code.txt)
- GKSL dynamics çıktısı: [logs/weak/2026-03-03_run02/t2k_gksl_dynamics/terminal_output_and_exit_code.txt](weak/2026-03-03_run02/t2k_gksl_dynamics/terminal_output_and_exit_code.txt)

Özet (terminalden):
- phase-map: `TOTAL chi2_GEO = 732.457`
- GKSL: `TOTAL chi2_GEO = 726.495`
- kanallar: 4 × `bins=18` → yaklaşık $\nu\approx 72$ varsayımıyla:
  - phase-map: $\chi^2/\nu \approx 732.457/72 \approx 10.17$
  - GKSL: $\chi^2/\nu \approx 726.495/72 \approx 10.09$

Yorum (sadece metrik): **uyum kötü** (1 civarında değil).

## STRONG (PDG rho pack)

Kaynak:
- [logs/strong/2026-03-03_run02/strong_c5a_paper_run/artifacts/rho_summary.json](strong/2026-03-03_run02/strong_c5a_paper_run/artifacts/rho_summary.json)

Özet (JSON’dan):
- `chi2.total = 85.1123`
- `chi2.ndof = 4`
- $\chi^2/\nu \approx 21.28$

Yorum (sadece metrik): **uyum çok kötü**.

## EM (Bhabha örneği)

Kaynak:
- [logs/em/2026-03-03_run02/em_paper_run/artifacts/bhabha_summary.json](em/2026-03-03_run02/em_paper_run/artifacts/bhabha_summary.json)

Özet (JSON’dan):
- `chi2.geo = 2040.1909` (bu koşuda `shape_only` ve `sm=geo`)
- `chi2.ndof = 60`
- $\chi^2/\nu \approx 34.00$

Yorum (sadece metrik): **uyum çok kötü**.

## DM (C2 holdout CV)

Kaynak:
- [logs/dm/2026-03-03_run02/dm_c2_holdout_cv_paper_run/artifacts/dm_c2_cv_summary.json](dm/2026-03-03_run02/dm_c2_holdout_cv_paper_run/artifacts/dm_c2_cv_summary.json)

Özet (JSON’dan):
- `telemetry.folds_are_galaxy_holdout = true`
- `telemetry.leakage_guard_disjoint_train_test = true`
- `telemetry.train_only_calibration = true`
- `telemetry.delta_chi2_test.max = 0.0` ve `min = 0.0`
- `fold_details[*].A_best = 0.0`

Yorum (sadece metrik): **testte iyileşme yok** (predictive kanıt yok).

## Tek satır sonuç

Bu run02 çıktıları **gerçek veriyle uyum açısından** genel olarak çok kötü metrikler veriyor (WEAK/STRONG/EM’de $\chi^2/\nu\gg 1$, DM-C2 holdout CV’de test iyileşmesi yok).
