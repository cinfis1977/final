# EM verdict (2026-03-03_run02)

## Kanıt dizini

- run: [em_paper_run/](em_paper_run/)

## Verdict (RUN_OK / MECH_OK / PRED_OK)

- RUN_OK=YES
  - kanıt: [terminal_output_and_exit_code.txt](em_paper_run/terminal_output_and_exit_code.txt) + artifacts klasörü
- MECH_OK=YES (baseline import overlay yok)
  - kanıt: [artifacts/bhabha_summary.json](em_paper_run/artifacts/bhabha_summary.json) içindeki `baseline_import_used=false`
- PRED_OK=NA
  - not: bu koşu `shape_only + freeze_betas` ile “paper-run / IO closure” modunda; predictive holdout testi değil.

## “Baseline/proxy overlay” kontrolü

- [artifacts/bhabha_summary.json](em_paper_run/artifacts/bhabha_summary.json) içinde:
  - `telemetry.baseline_import_used = false` → baseline import overlay yok.
  - `params.shape_only = true` ve `params.freeze_betas = true` → bu koşu zaten “paper-run / IO closure” proxy modu.

## Not

- EM burada state-evolution iddiası taşımıyor; amaç şema/IO kapanışı ve deterministik artifact üretimi.
