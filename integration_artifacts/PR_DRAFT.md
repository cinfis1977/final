PR Draft: GKSL Integration (Weak / Strong / EM / DM)

Overview
- This draft adds a self-contained GKSL/Lindblad-style two-flavor integration reference under `integration_artifacts/` for validation and comparison with the repository's existing approximate runners.

Scope of changes
- Solver: `integration_artifacts/mastereq/gk_sl_solver_clean.py` (RK4 density-matrix integrator, hermiticity/trace safeguards).
- Orchestration: `integration_artifacts/mastereq/unified_gksl.py` (API to register mass-basis and flavor-basis sector contributions and dissipators).
- Sectors: toy adapters `weak_sector.py`, `strong_sector.py`, `em_sector.py`, `dm_sector.py` with conversion helpers and parametric dissipators.
- Sectors: toy adapters `weak_sector.py`, `strong_sector.py`, `em_sector.py`, `dm_sector.py` with conversion helpers and parametric dissipators.
- LIGO: a toy gravitational-sector adapter `ligo_sector.py` implementing a small mass-basis modulation and a population-relaxation dissipator; unit tests added under `integration_artifacts/mastereq/tests/test_ligo_integration.py`.
- Tests & demo: per-sector unit tests under `integration_artifacts/mastereq/tests/` and an isolated demo runner `integration_artifacts/run_integration_demo.py` that writes outputs to `integration_artifacts/out/`.
- Documentation: `integration_artifacts/mastereq/derivation_mastereq.md` consolidates mappings, unit conversions and integration contracts.

Why this is isolated
- All new code is intentionally placed inside `integration_artifacts/` and committed on the feature branch to avoid modifying any existing project files or behavior on `main`.

Testing performed here
- Demo run produced `integration_artifacts/out/out_demo.csv`.
- Per-sector tests (Weak/Strong/EM/DM) pass when executed directly with `integration_artifacts` on `PYTHONPATH`.
- Added safety: `dm_density_to_amplitude` uses a physically motivated conversion (1 GeV/cm^3 ≈ 1.7827e-6 eV^4) and the DM test accepts an environment override `DM_TEST_COUPLING` to avoid accidental overflow during quick checks.

How to run locally
1. Run the isolated demo + tests (preferred):

```powershell
python integration_artifacts/run_integration_demo.py
```

2. If you prefer direct tests without pytest:

```powershell
set PYTHONPATH=integration_artifacts
python integration_artifacts/mastereq/tests/test_weak_integration.py
python integration_artifacts/mastereq/tests/test_strong_integration.py
python integration_artifacts/mastereq/tests/test_em_integration.py
python integration_artifacts/mastereq/tests/test_dm_integration.py
```

3. To reproduce the original DM holdout run (non-GKSL runner) without overwriting files, use the documented command in `repro/logs/014_UNSPECIFIED_dm_holdout_cv_thread_STIFFGATE.log` and pass a unique `--out_csv` filename.

Review & merging notes
- This PR is a reference implementation for validation and benchmarking; it is not intended to replace the existing runners automatically.
- Suggested reviewers: authors of the master-equation experiments and maintainers familiar with `nova`/`dm` runners.

Follow-ups (optional)
- Add LIGO / MS sectors and map their physics into the `UnifiedGKSL` contract.
- Replace parametric dissipators with explicit Lindblad operators where microphysical jump operators and rates are known.
- Add CI job to run the isolated integration tests on a dedicated runner with `pytest` installed.

Checklist before pushing
- [ ] Confirm review text is satisfactory
- [ ] Decide whether to push `gksl-pr-draft` to origin and open a GitHub PR
- [ ] (Optional) Squash or rebase commits if you want a cleaner history


