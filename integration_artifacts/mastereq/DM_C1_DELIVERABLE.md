# DM-C1 deliverable: dynamics core + integrity locks

This deliverable upgrades DM from a static/proxy overlay into a *genuine internal-state dynamics* runner, at the same evidence standard used elsewhere in this repo (WEAK/STRONG/EM): closure, integrity, refinement stability, and anti-fallback.

This is a **stability / IO-closure / schema-stability** deliverable, not a physical-accuracy claim.

## What is implemented

- `dm_dynamics_core_c1.py`
  - Multi-component internal state $X(t)=(r,v,\theta,\omega,\epsilon,g)$.
  - Evolution law with continuous gate $g(t)$ and mismatch load $\epsilon(t)$.
  - Observable derived from state via
    $$V_{pred}(r)=\sqrt{r\,a_{tot}(r)}$$
    where $a_{tot}=a_{bary}+a_{dm}(r;X)$.

- `dm_dynamics_runner_c1.py`
  - Pack → simulate → CSV prediction + JSON telemetry/summary.

- `integration_artifacts/mastereq/tests/test_e2e_dm_c1_dynamics_integrity_and_antifallback.py`
  - **Closure**: synthetic pack generated from the same core yields $\chi^2\approx 0$.
  - **Integrity**: boundedness/finite checks: $g\in[0,1]$, $\epsilon\ge 0$, no NaN/inf.
  - **Refinement stability**: halving `dt` (doubling steps) changes predictions by ≤ 5%.
  - **Order sensitivity**: `order_mode=forward` vs `reverse` produces a real, deterministic difference.
  - **Anti-fallback**: with `DM_POISON_PROXY_CALLS=1`, legacy/proxy imports are poisoned (test asserts that importing `dm_thread_env_dropin` fails), while DM-C1 runner continues to pass.

## How to run

- E2E test:

`python -m pytest -q integration_artifacts/mastereq/tests/test_e2e_dm_c1_dynamics_integrity_and_antifallback.py`

- Runner example:

`python dm_dynamics_runner_c1.py --pack path/to/pack.json --out_csv out.csv --out_json out.json --dt 0.2 --n_steps 200 --order_mode forward`

## Telemetry contract (high-level)

Runner JSON includes:

- `telemetry.dm_dynamics_core_used: true`
- `telemetry.proxy_overlay_used: false`
- `telemetry.stiffgate_in_evolution: true`
- `telemetry.boundedness.{g_in_0_1,epsilon_nonneg,finite_all}`
- `framing.stability_not_accuracy: true`

## Notes

- DM-C1 is intended as the first “real dynamics” layer. Real-data packs + holdout/CV + paper-run mode are the next step (DM-C2).
