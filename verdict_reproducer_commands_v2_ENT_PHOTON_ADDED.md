# Verdict Reproducer Commands — v2 (Entanglement / Photon added)

> Goal: copy-paste reproducibility of the **locked / prereg / audit** runs that are currently canonical in this repo.
> Important boundary:
> - **Performance-pass** sectors live in the main performance runbook / verdict batch.
> - **Entanglement / Photon** commands below are current **audit / bridge / prereg** commands.
> - These commands do **not** by themselves imply first-principles dynamic closure.

---

## Entanglement — CHSH / coincidence export / memory / data-side Bell audit

### E1. NIST HDF5 click-bitpair audit (schema / sanity audit)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_nist_hdf5_click_bitpair_audit_v1_DROPIN_SELFCONTAINED.ps1 `
  -H5Path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  -OutDir "out" `
  -Prefix "nist_h5bitpair_audit"
```

### E2. NIST HDF5 -> coincidence CSV export (Bridge-E0 helper)

> Current canonical coincidence export wrapper for the paper-facing entanglement bridge line.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_nist_hdf5_export_coinc_bridgeE0_v1_2_1_DROPIN_SELFCONTAINED.ps1 `
  -Hdf5Path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  -DownloadRun '' `
  -OutcomeMode half `
  -OutCsv "out\nist_run4_coincidences.csv" `
  -SchemaTxt "out\nist_hdf5_schema_v1.txt" `
  -DebugTxt "out\nist_hdf5_export_debug_v1.txt"
```

### E3. Coincidence CSV audit (gap-binned bridge audit)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_audit_nist_coinc_csv_bridgeE0_v1_DROPIN_SELFCONTAINED.ps1 `
  -InCsv ".\out\nist_run4_coincidences.csv" `
  -GapBins 24 `
  -LogGapBins `
  -OutDir "out" `
  -Prefix "coinc_audit"
```

### E4. Preregistered entanglement-memory diagnostic (no fit)

> This is the current memory-statistic diagnostic line.
> It is **not** a first-principles Bell derivation.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_entanglement_memory_from_coinc_csv_v1_DROPIN_SELFCONTAINED.ps1 `
  -InCsv ".\out\nist_run4_coincidences.csv" `
  -NBins 12 `
  -LogGapBins `
  -KSigma 2.0 `
  -GlobalCHSHCheck `
  -NullGapShuffle `
  -NullOutcomeShuffle `
  -NullReps 200 `
  -OutCsv "out\entanglement_memory_prereg_v1.csv"
```

### E5. Data-side CH/Eberhard Bell audit — overall run summaries

> Current paper-facing verified branch = **slots 4–8**.

```powershell
py -3 .\CODE\nist_build_hdf5_ch_eberhard_runner_v1_DROPIN.py `
  --h5_path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  --slots "4-8" `
  --out_prefix ".\out\nist_ch\run03_43_slots4_8"
```

```powershell
py -3 .\CODE\nist_build_hdf5_ch_eberhard_runner_v1_DROPIN.py `
  --h5_path ".\data\nist\hdf5\2015_09_18\01_11_CH_pockel_100kHz.run4.afterTimingfix.dat.compressed.build.hdf5" `
  --slots "4-8" `
  --out_prefix ".\out\nist_ch\run01_11_slots4_8"
```

```powershell
py -3 .\CODE\nist_build_hdf5_ch_eberhard_runner_v1_DROPIN.py `
  --h5_path ".\data\nist\hdf5\2015_09_18\02_54_CH_pockel_100kHz.run4.afterTimingfix2.dat.compressed.build.hdf5" `
  --slots "4-8" `
  --out_prefix ".\out\nist_ch\run02_54_slots4_8"
```

### E6. Data-side CH/Eberhard Bell audit — split stability summaries (v1.1 global settings mapping)

> Use this branch for split diagnostics and scorecards.  
> This is still **data-side audit**, not model-side Bell closure.

```powershell
py -3 .\CODE\nist_ch_j_timesplits_v1_1_DROPIN.py `
  --h5_path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  --slots "4-8" `
  --n_splits 10 `
  --out_prefix ".\out\nist_ch_splits\run03_43_slots4_8_v1_1"
```

```powershell
py -3 .\CODE\nist_ch_j_timesplits_v1_1_DROPIN.py `
  --h5_path ".\data\nist\hdf5\2015_09_18\01_11_CH_pockel_100kHz.run4.afterTimingfix.dat.compressed.build.hdf5" `
  --slots "4-8" `
  --n_splits 10 `
  --out_prefix ".\out\nist_ch_splits\run01_11_slots4_8_v1_1"
```

```powershell
py -3 .\CODE\nist_ch_j_timesplits_v1_1_DROPIN.py `
  --h5_path ".\data\nist\hdf5\2015_09_18\02_54_CH_pockel_100kHz.run4.afterTimingfix2.dat.compressed.build.hdf5" `
  --slots "4-8" `
  --n_splits 10 `
  --out_prefix ".\out\nist_ch_splits\run02_54_slots4_8_v1_1"
```

### E7. CH/Eberhard split scorecard (v1.1 branch)

```powershell
py -3 .\CODE\nist_ch_j_splits_scorecard_v1_DROPIN.py `
  --in_glob ".\out\nist_ch_splits\*_v1_1.splits.csv" `
  --out_csv ".\out\nist_ch_splits\CH_J_SPLITS_SCORECARD.csv" `
  --out_md  ".\out\nist_ch_splits\CH_J_SPLITS_SCORECARD.md"
```

### Entanglement boundary note

The commands above establish the following current repo lines:

- CHSH / coincidence **audit**
- entanglement-memory **diagnostic**
- data-side CH/Eberhard **Bell audit**

They do **not** constitute a first-principles dynamic Bell performance pass.  
The missing layer remains: model-generated \(J_{\mathrm{model}}\) / \(E^{\mathrm{model}}_{ab}\) from locked \(H_s\), \(\mathcal{D}_s\), and a measurement map.

---

## Photon — bridge / prereg / falsifier commands

### P1. Accumulation-law prereg (signed / default metric)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_birefringence_accumulation_v1_DROPIN_SELFCONTAINED_FIX.ps1 `
  -OutCsv "out\birefringence_accumulation_prereg_v1.csv"
```

### P2. Accumulation-law prereg (absolute-metric variant)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_birefringence_accumulation_v1_DROPIN_SELFCONTAINED_FIX.ps1 `
  -AbsTest `
  -OutCsv "out\birefringence_accumulation_prereg_abs_v1.csv"
```

### P3. CMB birefringence prereg lock

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_cmb_birefringence_v1_DROPIN_SELFCONTAINED.ps1 `
  -OutCsv "out\cmb_birefringence_prereg_v1.csv"
```

### P4. Sky-fold anisotropy falsifier

> If this wrapper exists in the repo under the expected locked name, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_prereg_birefringence_skyfold_v1_DROPIN_SELFCONTAINED_FIX.ps1 `
  -OutCsv "out\birefringence_skyfold_prereg_v1.csv"
```

### Photon boundary note

The commands above establish the current photon line as:

- locked accumulation-law bridge observable
- optional absolute-metric variant
- CMB holdout-style prereg lock
- sky-fold falsifier

This is a functioning **bridge / falsification** layer.  
It is **not yet** a first-principles photon propagation performance closure.

---

## What should NOT be mixed into the main performance table

Do **not** treat the following as current performance-pass commands:

- CHSH decorrelation audit wrapper
- entanglement-memory diagnostic
- data-side CH/Eberhard J audit
- photon accumulation-law bridge runs
- CMB birefringence prereg lock
- sky-fold falsifier

These belong in an **audit / bridge / prereg command catalog**, not in the current performance-pass runbook.
