# WEAK verdict (2026-03-03_run02)

## Kanıt dizinleri

- Phase-map (proxy referans): [t2k_phase_map_fixedbyclaude/](t2k_phase_map_fixedbyclaude/)
- GKSL dynamics (state evolution): [t2k_gksl_dynamics/](t2k_gksl_dynamics/)

## Verdict (RUN_OK / MECH_OK / PRED_OK)

Bu sektörde iki koşu birlikte tutuluyor: biri proxy referans, diğeri açık GKSL state evolution.

- `t2k_phase_map_fixedbyclaude`
  - RUN_OK=YES (rc=0, artifact var)
  - MECH_OK=NA (state evolution iddiası yok; proxy referans koşu)
  - PRED_OK=NA (bu koşu “predictive power” test protokolü değil)
  - kanıt: [terminal_output_and_exit_code.txt](t2k_phase_map_fixedbyclaude/terminal_output_and_exit_code.txt), [artifacts/t2k_phase_map.csv](t2k_phase_map_fixedbyclaude/artifacts/t2k_phase_map.csv)

- `t2k_gksl_dynamics`
  - RUN_OK=YES (rc=0, artifact var)
  - MECH_OK=YES (GKSL satırları + kanal bazlı chi2 dökümü)
  - PRED_OK=NA (tek nokta değerlendirme; kalibrasyon+holdout yok)
  - kanıt: [terminal_output_and_exit_code.txt](t2k_gksl_dynamics/terminal_output_and_exit_code.txt), [artifacts/t2k_gksl_dynamics.csv](t2k_gksl_dynamics/artifacts/t2k_gksl_dynamics.csv)

## Audit notları (neden bu anlamlı?)

- Bu sektörde tek başına “PRED_OK” iddiası yok; ama “mekanizma gerçekten GKSL ile çalışıyor mu?” sorusuna güçlü kanıt var.
