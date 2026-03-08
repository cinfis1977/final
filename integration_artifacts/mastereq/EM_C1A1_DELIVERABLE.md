# EM-C1a.1 Deliverable (Holomorphic-Term Extension)

This deliverable extends EM-C1a with an optional **holomorphic term** in the evolution law and locks it with an end-to-end test.

Scope: **EM-C1a.1 (scattering amplitude scan + M_hol)**
- Internal state: complex amplitude $A(t)$ along $t = \ln(s/s_0)$
- Evolution law:
  $$\frac{dA}{dt} = (i\,\beta(t) - \Gamma(t) + M_{\rm hol}(t, A))\,A$$
- Observable-from-state:
  $$\sigma(s) = \sigma_{\rm norm}\,|A(s)|^2$$
- No baseline overlay, no post-hoc multiplication.

## What the test proves

- Holomorphic term is *actually used* (telemetry lock)
- Closure: synthetic pack uses `data = pred` so $\chi^2 \approx 0$
- Integrity: finite outputs, non-negative $\sigma$, refinement stability under `dt_max` halving
- Anti-fallback: baseline call-poison enabled and still passes

Explicit framing: **stability lock, not physical accuracy**.

## Run the evidence test

From repo root (Windows):

- `./.venv/Scripts/python.exe -m pytest -q integration_artifacts/mastereq/tests/test_e2e_em_c1a1_holomorphic_term_refinement_and_antifallback.py -s`

## Files

- Core: `em_c1a1_scattering_amplitude_core.py`
- Runner: `em_scattering_pack_chi2_c1a1.py`
- Test: `integration_artifacts/mastereq/tests/test_e2e_em_c1a1_holomorphic_term_refinement_and_antifallback.py`
