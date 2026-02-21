# particle_specific_finalize_from_runs_v1_0 (DROP-IN)

What this does
- Takes three completed run folders at a locked `good_ppm` (default: 3):
  - A1–B2 (discovery)
  - A1–B3 (holdout)
  - A2–B3 (third-arm)
- Summarizes locked metrics (no regression, no fitting)
- Writes the signed prereg lock + single FINAL verdict artefacts:
  - `out/particle_specific_final_goodppm3_lock/prereg_lock_and_final_verdict_goodppm3.json`
  - `out/particle_specific_final_goodppm3_lock/FINAL_VERDICT_REPORT_goodppm3.md`

Expected inputs in each run folder
- `alltargets_delta_success_width_pairs.csv`
- `alltargets_bin_success_width_stats.csv`

Run (PowerShell)
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN_finalize_particle_specific_goodppm3_lock_from_runs_v1_0.ps1 `
  -PairB2Dir ".\out\particle_specific_sweep_goodppm_3_A1_B2" `
  -PairB3Dir ".\out\particle_specific_sweep_goodppm_3_A1_B3_holdout" `
  -ThirdArmDir ".\out\particle_specific_cytofull_A2_B3_good3" `
  -TargetsCsv ".\out\particle_specific_cytofull_A1_B2_direct\targets_used.csv" `
  -OutDir ".\out\particle_specific_final_goodppm3_lock"
```

Optional “signing” (MD5) of frozen points CSVs
Pass any/all of:
- `-ModeAPoints`, `-ModeB2Points`, `-ModeB3Points`, `-ModeA2Points`
to record size+MD5 in the JSON artefact.
