# WEAK metric sensitivity (run02 gauss_loose vs run05 poisson_dev)

Bu rapor **veri-eşleşmesi update’i değildir**. Aynı pack + aynı model parametreleriyle sadece *skor tanımı* değiştirildi:

- run02: legacy `gauss_loose` (debug)
- run05: `poisson_dev` (fit-siz Poisson deviance)

## Evidence links

- run02 phase-map terminal: [weak/2026-03-03_run02/t2k_phase_map_fixedbyclaude/terminal_output_and_exit_code.txt](weak/2026-03-03_run02/t2k_phase_map_fixedbyclaude/terminal_output_and_exit_code.txt)
- run02 GKSL terminal: [weak/2026-03-03_run02/t2k_gksl_dynamics/terminal_output_and_exit_code.txt](weak/2026-03-03_run02/t2k_gksl_dynamics/terminal_output_and_exit_code.txt)
- run05 phase-map terminal: [weak/2026-03-03_run05/t2k_phase_map_poisson_dev/terminal_output_and_exit_code.txt](weak/2026-03-03_run05/t2k_phase_map_poisson_dev/terminal_output_and_exit_code.txt)
- run05 GKSL terminal: [weak/2026-03-03_run05/t2k_gksl_dynamics_poisson_dev/terminal_output_and_exit_code.txt](weak/2026-03-03_run05/t2k_gksl_dynamics_poisson_dev/terminal_output_and_exit_code.txt)

## Totals (reported by runner)

| runner | chi2_mode | TOTAL chi2_GEO | Delta (SM-GEO) |
|---|---|---:|---:|
| phase-map | gauss_loose (run02) | 732.457 | 0.671 |
| GKSL | gauss_loose (run02) | 726.495 | 6.633 |
| phase-map | poisson_dev (run05) | 258.559 | 0.651 |
| GKSL | poisson_dev (run05) | 258.311 | 0.900 |

## Takeaway

- Bu fark **modelin/verinin değiştiği** anlamına gelmez; sadece “mesafe/likelihood” tanımı değişti.
- Bu yüzden “uyum kötü” kararını verirken hangi metrikle konuştuğumuzu explicit tutmak gerekir.
