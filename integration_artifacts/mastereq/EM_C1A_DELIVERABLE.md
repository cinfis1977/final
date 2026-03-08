# EM-C1a Deliverable (Scattering Amplitude Dynamics)

This deliverable introduces a minimal *internal-state* EM scattering dynamics path and locks it with an end-to-end test.

Scope: **EM-C1a (Bhabha/μμ-like scattering amplitude scan)**
- Internal state: complex amplitude $A(t)$ along scan coordinate $t = \ln(s/s_0)$
- Evolution law (minimal):
  $$\frac{dA}{dt} = (i\,\beta(t) - \Gamma(t))\,A$$
- Observable-from-state:
  $$\sigma(s) = \sigma_{\rm norm}\,|A(s)|^2$$
- No baseline overlay, no post-hoc multiplication.

## What the test proves

- Dynamics is present (state evolves under an explicit update law)
- Observable is derived from state (not baseline×(1+δ))
- Integrity: finite outputs, non-negative $\sigma$, refinement stability
- Anti-fallback: with baseline/overlay call-poison enabled, still passes

Explicit framing: **stability lock, not physical accuracy**.

## Run the evidence test

From repo root (Windows):

- `./.venv/Scripts/python.exe -m pytest -q integration_artifacts/mastereq/tests/test_e2e_em_c1a_scattering_dynamics_integrity_and_antifallback.py`

## Files

- Core: `em_c1a_scattering_amplitude_core.py`
- Runner: `em_scattering_pack_chi2_c1a.py`
- Test: `integration_artifacts/mastereq/tests/test_e2e_em_c1a_scattering_dynamics_integrity_and_antifallback.py`
