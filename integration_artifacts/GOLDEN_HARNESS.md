# Golden harness (canonical runners, isolated outputs)

Bu harness, main proje içinde canonical kabul edilen `tools/verdict_commands.txt` komutlarını **yeniden koşturur**, ama output path’lerini otomatik olarak `integration_artifacts/out/verdict_golden/` altına **rewrite** ederek ana projenin `out/` klasörünü ezmez.

Amaç:
- “Doğru runner hangisi?” sorusunu canonical komut listesinden *mekanik olarak* sabitlemek.
- Runner’ların reproducible şekilde çalıştığını ve beklenen output dosyalarını ürettiğini doğrulamak.
- Daha sonra yapılacak **GKSL master equation ↔ runner** equivalence kontrollerine “golden artefact” sağlamak.

## Canonical kaynak

- Orkestrasyon: [tools/run_verdict.ps1](tools/run_verdict.ps1)
- Canonical komut listesi: [tools/verdict_commands.txt](tools/verdict_commands.txt)

## Kullanım

Repo root’tan:

```powershell
python integration_artifacts/scripts/verdict_golden_harness.py
```

Sadece belirli aralık:

```powershell
python integration_artifacts/scripts/verdict_golden_harness.py --start 1 --end 10
```

Sadece komutları rewrite edip yazdır (koşturma yok):

```powershell
python integration_artifacts/scripts/verdict_golden_harness.py --dry_run
```

## Rewrite edilen output flag’leri

Şu an rewrite edilenler:
- `--out`
- `--out_csv`
- `--chi2_out`

Gerekirse diğer output flag’leri eklenebilir.

## Çıktılar

Harness koştuktan sonra:
- `integration_artifacts/out/verdict_golden/RUN_SUMMARY.md`
- `integration_artifacts/out/verdict_golden/RUN_SUMMARY.json`

## Sıradaki aşama (physics correctness)

Bu harness tek başına “master equation doğru mu / runner implementasyonu doğru mu?” kanıtlamaz.
Bir sonraki aşama:
- GKSL (integration_artifacts/mastereq) çıktısını
- canonical runner çıktılarıyla
aynı input parametreleri altında, ara büyüklükler + nihai skorlar seviyesinde **birebir kıyaslayan** equivalence testleri.
