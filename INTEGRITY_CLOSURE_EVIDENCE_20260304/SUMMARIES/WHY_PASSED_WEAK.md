# Why WEAK is included (integrity/closure evidence)

WEAK is bundled here as **commanded pipeline closure**: the declared kernels/packs/profiles exist, load, and emit the expected artifacts.

This is **Integrity_OK/Closure_OK evidence**, not a physics-performance claim. Unlike MS, WEAK currently has no single built-in `final_verdict` JSON gate.

## Evidence artifacts
- Main evidence CSV (per-channel predictions + phase decomposition fields):
  - `../RESULTS/WEAK/out_weak_t2k_oneforall.csv`
- Additional captured CSVs (phase maps / dynamics views):
  - `../RESULTS/2026-03-03_run02/weak/t2k_phase_map.csv`
  - `../RESULTS/2026-03-03_run02/weak/t2k_gksl_dynamics.csv`

## Inputs + runners (closure evidence)
- T2K official frequentist profiles are included at:
  - `../INPUTS/t2k_release_extract/t2k_frequentist_profiles.json`
- Runner code copied under `../CODE/`:
  - `score_nova_minos_t2k_penalty.py` (composite scoring driver)
  - `t2k_penalty_cli.py` (profiles-based penalty)
  - `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py` (forward kernel)
  - `nova_channels.json`, `minos_channels.json` (packs)

## Command provenance
- Canonical commands are captured in:
  - `../COMMANDS/CODEX_FINAL_RUN_COMMANDS.md`
  - `../COMMANDS/CODEX_FINAL_RUN_COMMANDS_v3.txt`

If you want a strict numeric gate for WEAK in the same style as MS (a single machine-readable `final_verdict` JSON), we can add a tiny wrapper that runs the command and writes a verdict.
