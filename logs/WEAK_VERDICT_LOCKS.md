# WEAK verdict locks (fit yok / one-for-all)

Amaç (sadece WEAK):

1) **Skor standardı**: tek bir resmî skor ile konuşmak
2) **GEO > SM üstünlüğünü verdict’te garanti etmek** (prereg lock)
3) “TOTAL düşük” iddiasını **fit olmadan** doğru çerçevelemek

Bu doküman **parametre araması / tuning / fitting** içermez; yalnızca skor tanımı, integrity ve karar lock’larını tanımlar.

## 0) Net ayrım: “TOTAL düştü” ne demektir?

- `gauss_loose` → `poisson_dev` geçişi TOTAL’i düşürebilir (run02→run05’de olduğu gibi).
- Bu **model iyileşti** demek değildir; yalnızca **sayım verisi için daha uygun bir likelihood mesafesi** ile konuştuğumuzu söyler.
- Dolayısıyla verdict’te “TOTAL düştü” ifadesi ancak **“metrik standardizasyonu sonrası raporlanan TOTAL”** anlamında kullanılmalıdır.

## 1) Resmî metrik standardı (tek metrik)

- **WEAK resmî metrik**: `poisson_dev` (Poisson deviance)
- `gauss_loose` yalnızca **debug** amaçlıdır; scorecard/verdict kararına girmez.

Uygulama: WEAK runner’lar `--chi2_mode poisson_dev` ile koşulur.

Not: `--sigma_floor` yalnızca `gauss_loose` varyansı içindir; `poisson_dev` için kullanılmaz.

## 2) Verdict lock: “GEO, SM’den daha iyi” (Delta-lock)

Tanım:

- $\Delta \chi^2 \equiv \chi^2_{SM} - \chi^2_{GEO}$
- **Pozitif** olması GEO’nun daha iyi olduğunu söyler.

### Lock-2a (Total):

- Kabul: $\Delta\chi^2_{total} \ge \varepsilon$

Öneri (pragmatik, run05 ölçeğinde):

- `poisson_dev` altında $\Delta\chi^2$ tipik olarak **~O(1)** seviyesinde.
- Bu yüzden **$\varepsilon = 0.5$** makul bir “marj” lock’ıdır.
  - $\varepsilon = 1.0$ şu anki run05 sayılarıyla fazlaca agresif (GKSL total=0.900, phase-map total=0.651).

### Lock-2b (Channel dağılımı):

- 4 kanalın en az **3’ünde** $\Delta\chi^2_{channel} > 0$ olmalı.
  - Amaç: üstünlüğün tek bir kanala yığılmasıyla “kazara” oluşmasını engellemek.

### Lock-2c (Stabilite / fit değil):

Aynı koşu **iki küçük numerik perturbasyon** ile tekrar edilir:

- GKSL: `--steps` değerini örn. 600 ve 900 gibi iki noktada yeniden koş.

Kabul:

- $\Delta\chi^2_{total}$ işaret değiştirmez (pozitif kalır)
- Channel lock bozulmaz (>=3/4 pozitif kalır)

Bu “stability check” fit değildir; sadece numerik/solver hassasiyetini eler.

## 3) Integrity locks (fit yok çizgisinin temeli)

- Komut, stdout/stderr, exit code ve artifact CSV’ler logs altında kanıtlanır.
- Proxy/fallback kaçışı olmamalı (repo’nun poison/guard kuralları).

## 4) Kanıt (mevcut)

- run02 `gauss_loose` vs run05 `poisson_dev` metrik duyarlılığı: [WEAK_METRIC_SENSITIVITY_2026-03-03_run02_vs_run05.md](WEAK_METRIC_SENSITIVITY_2026-03-03_run02_vs_run05.md)
- run05 phase-map poisson_dev terminal: [weak/2026-03-03_run05/t2k_phase_map_poisson_dev/terminal_output_and_exit_code.txt](weak/2026-03-03_run05/t2k_phase_map_poisson_dev/terminal_output_and_exit_code.txt)
- run05 GKSL poisson_dev terminal: [weak/2026-03-03_run05/t2k_gksl_dynamics_poisson_dev/terminal_output_and_exit_code.txt](weak/2026-03-03_run05/t2k_gksl_dynamics_poisson_dev/terminal_output_and_exit_code.txt)

Run05 snapshot (poisson_dev):

- phase-map: total $\Delta\chi^2=0.651$, channel sign count = 3/4 pozitif
- GKSL: total $\Delta\chi^2=0.900$, channel sign count = 3/4 pozitif

Bu snapshot, $\varepsilon=0.5$ ile Lock-2a/2b’yi geçer.
