PR Draft: GKSL Integration (Weak/Strong/EM/DM)

Summary
- Adds a self-contained GKSL/Lindblad-style 2-flavor integration reference under `integration_artifacts/`.
- Implements sector adapters for Weak, Strong, EM, and DM sectors, with conversion helpers and toy dissipators.
- Provides a cleaned RK4 solver, a `UnifiedGKSL` wrapper, demo runner, per-sector unit tests, and a derivation note.

Key files
- `integration_artifacts/mastereq/gk_sl_solver_clean.py` — cleaned RK4 density-matrix solver
- `integration_artifacts/mastereq/unified_gksl.py` — unified wrapper that composes sectors
- `integration_artifacts/mastereq/{weak,strong,em,dm}_sector.py` — sector helpers and mappings
- `integration_artifacts/mastereq/tests/*.py` — unit tests for each sector and basic solver
- `integration_artifacts/run_integration_demo.py` — isolated demo + test harness
- `integration_artifacts/mastereq/derivation_mastereq.md` — derivations and unit mappings

Testing & usage
1. From repo root, run the isolated demo harness (adds `integration_artifacts` to `PYTHONPATH` automatically):

```powershell
python integration_artifacts/run_integration_demo.py
```

2. If `pytest` is not installed the harness falls back to direct test execution; to use pytest you can install requirements: `pip install -r integration_artifacts/requirements.txt`.

3. To run an individual sector test without `pytest`:

```powershell
set PYTHONPATH=integration_artifacts
python integration_artifacts/mastereq/tests/test_dm_integration.py
```

Notes & rationale
- All new code is placed in `integration_artifacts/` to avoid changing existing repository files.
- The DM mapping is a toy linear mapping from local DM density to an effective mass-squared amplitude; a physically-motivated scaling was added to avoid numerical overflow in typical tests.

Requested next steps
- Review the PR draft and confirm whether to push the branch and open a GitHub PR.
- Optionally add LIGO/MS sectors and explicit Lindblad jump-operator implementations.
