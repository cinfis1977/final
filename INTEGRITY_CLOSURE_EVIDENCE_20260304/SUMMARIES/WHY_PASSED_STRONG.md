# Why STRONG is included (integrity/closure evidence)

This is a **reproducibility / anti-fallback / IO-closure** pass: declared packs + covariances are ingested, the amplitude-core path is executed (not PDG shortcuts), and integrity telemetry is emitted.

## Evidence artifacts
### Pack-ingestion paper run
- Report: `../RESULTS/strong_c5a/paper_run_report.md`
- Summaries:
  - `../RESULTS/strong_c5a/sigma_tot_summary.json`
  - `../RESULTS/strong_c5a/rho_summary.json`

Key pass indicators in these JSONs:
- `anti_fallback.pdg_call_poison_active == true` (poison enabled)
- `amplitude_core_used == true` and `pdg_baseline_used == false` (no PDG-baseline fallback)
- `io.data_loaded_from_paths == true` (pack paths resolved)
- `integrity.no_nan_inf == true` plus other domain guards (`sigma_tot_nonnegative`, `rho_finite`, etc.)
- `framing.stability_not_accuracy == true`

### Scan artifacts (Codex commands)
- Chi2 JSONs + CSVs are included under:
  - `../RESULTS/STRONG/`
  - `../RESULTS/STRONG_SCAN/`

These provide the raw materials for the Codex sector metric rule (compute $\Delta\chi^2$ from `*_chi2.json`), with the concrete outputs preserved.

## Runner + command provenance
- Pack-ingestion entrypoint: `../CODE/run_strong_c5a_paper_run.py`
- Amplitude-core runner: `../CODE/strong_amplitude_pack_hepdata_c4.py`
- Scan runners: `../CODE/strong_sigma_tot_energy_scan_v2.py`, `../CODE/strong_rho_energy_scan_v3.py`
- Canonical commands: `../COMMANDS/CODEX_FINAL_RUN_COMMANDS.md` / `../COMMANDS/CODEX_FINAL_RUN_COMMANDS_v3.txt`
