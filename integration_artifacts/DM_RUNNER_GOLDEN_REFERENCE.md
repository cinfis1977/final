# DM runner golden reference (canonical prereg)

Bu doküman, DM (SPARC/RAR) sektöründe “doğru runner”ların hangileri olduğunu ve **PASS** kuralının runner kodunda *tam olarak nasıl hesaplandığını* netleştirir.

## Canonical kaynak

Ana orkestrasyon:
- [tools/run_verdict.ps1](tools/run_verdict.ps1) komutları buradan okur:
- [tools/verdict_commands.txt](tools/verdict_commands.txt)

DM prereg için canonical komutlar iki adet runner çalıştırır:

1) THREAD env (STIFFGATE; galaxy-closed)
- Runner: [dm_holdout_cv_thread_STIFFGATE.py](dm_holdout_cv_thread_STIFFGATE.py)
- Amaç: `env_model=thread` altında (galaxy-closed gate ile) prereg fixed-param CV.

2) NO-ENV baseline
- Runner: [dm_holdout_cv_thread.py](dm_holdout_cv_thread.py)
- Amaç: `env_model=none` ile baseline prereg fixed-param CV.

Bu iki koşunun “karşılaştırması” paper’da da kilitlenmiştir:
- [paper/paper_final.md](paper/paper_final.md) bölüm “8.5 DM — SPARC/RAR”

## PASS kuralı (runner seviyesinde)

Her iki runner da fold bazında şu büyüklükleri hesaplayıp CSV’ye yazar:

- `chi2_test_base`: test fold için baseline (g_bar) chi2
- `chi2_test_best`: test fold için GEO modeliyle tahmin edilen g_pred chi2
- `delta_chi2_test = chi2_test_base - chi2_test_best`

Paper’daki prereg kural:
- PASS iff tüm fold’larda `delta_chi2_test > 0`.

Runner kodunda bu mantık açıkça var:
- [dm_holdout_cv_thread.py](dm_holdout_cv_thread.py) fold print: `test Δχ²={delta_test}`
- [dm_holdout_cv_thread_STIFFGATE.py](dm_holdout_cv_thread_STIFFGATE.py) fold print: `test Δχ²={delta_test}`

## Otomatik golden check (önerilen)

Bu repo içinde, ana `out/` klasörünü ezmeden canonical DM prereg koşusunu tekrar üretmek ve PASS kuralını otomatik doğrulamak için:

- Script: [integration_artifacts/scripts/dm_prereg_golden_check.py](integration_artifacts/scripts/dm_prereg_golden_check.py)

Bu script:
- canonical iki runner’ı çalıştırır (A ve alpha fixed, kfold=5, seed=2026)
- çıktı CSV’lerini `integration_artifacts/out/dm_prereg_golden/` altına yazar
- iki CSV’de de `delta_chi2_test > 0` koşulunu fold-bazında kontrol eder
- bir özet markdown üretir: `integration_artifacts/out/dm_prereg_golden/DM_GOLDEN_SUMMARY.md`

Çalıştırma:

```powershell
python integration_artifacts/scripts/dm_prereg_golden_check.py
```

Sadece mevcut CSV’leri kontrol etmek istersen:

```powershell
python integration_artifacts/scripts/dm_prereg_golden_check.py --skip_run
```
