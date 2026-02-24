# New Master Equation With Gauge Structure

This repository is a reproducibility workspace for a locked, cross-sector draft:
WEAK / EM / STRONG / DM / GW + mass spectrometry (real Bruker mzML addendum).

Scope note: `PASS` means not falsified under preregistered tests for the specific tested panels; it is not a universal proof.

## GKSL / Lindblad integration validation (evidence)

This branch-local folder contains an isolated GKSL reference implementation and tests under `integration_artifacts/mastereq/`.

What is validated by deterministic pytest checks:

- **WEAK runner ↔ GKSL equivalence (unitary / phase-map):**
  # Integration artifacts

  This folder collects the deterministic, “paper-grade” equivalence evidence suite:

  - GKSL/Lindblad reference implementation + tests under `integration_artifacts/mastereq/`
  - Golden-output artifacts under `integration_artifacts/out/`
  - The golden harness runner under `integration_artifacts/scripts/`

  Start here:

  - `integration_artifacts/README_INTEGRATION.md` (overview + how to run)
  - `integration_artifacts/EQUIVALENCE_CHECKS.md` (what is checked / not checked)
  - `integration_artifacts/GOLDEN_HARNESS.md` (golden regen + strict equality)

  Quick commands (run from repo root):

  ```powershell
  python integration_artifacts/scripts/verdict_golden_harness.py
  python -m pytest -q integration_artifacts/mastereq/tests
  ```

  Note: `integration_artifacts/out/verdict_golden/RUN_SUMMARY.{md,json}` are generated reports and are gitignored because they may include machine-specific absolute paths.
    `integration_artifacts/mastereq/tests/test_microphysics_wiring_equivalence.py`
