from __future__ import annotations

import math
from typing import Callable, Iterable

import numpy as np


def evolve_A_over_scan(
    s_values: Iterable[float],
    *,
    s0: float,
    A0: complex,
    beta_fn: Callable[[float], float],
    gamma_fn: Callable[[float], float],
    dt_max: float,
) -> np.ndarray:
    """Evolve a complex scattering amplitude A over an energy scan.

    We use t = ln(s/s0) as the evolution coordinate.

    Minimal C1a law (no M_hol):
      dA/dt = (i*beta(t) - gamma(t)) * A

    Integration is performed by splitting each scan interval into substeps of size <= dt_max.
    For each substep we apply an exponential update with coefficient evaluated at the midpoint.

    Args:
        s_values: scan points in Mandelstam s (must be positive)
        s0: reference s0 used in t = ln(s/s0) (must be positive)
        A0: complex initial amplitude at first scan point
        beta_fn: beta(t) real phase-flow function
        gamma_fn: gamma(t) real damping function (>=0 recommended)
        dt_max: maximum step size in t

    Returns:
        A_values: complex ndarray aligned with s_values
    """

    s_arr = np.asarray(list(s_values), dtype=float)
    if s_arr.ndim != 1 or s_arr.size < 1:
        raise ValueError("s_values must be a non-empty 1D sequence")
    if not np.all(np.isfinite(s_arr)) or np.any(s_arr <= 0):
        raise ValueError("s_values must be finite and strictly positive")
    s0 = float(s0)
    if not math.isfinite(s0) or s0 <= 0:
        raise ValueError("s0 must be finite and strictly positive")

    dt_max = float(dt_max)
    if not math.isfinite(dt_max) or dt_max <= 0:
        raise ValueError("dt_max must be finite and > 0")

    t = np.log(s_arr / s0)

    A = np.zeros(s_arr.size, dtype=np.complex128)
    A[0] = complex(A0)

    for i in range(s_arr.size - 1):
        t0 = float(t[i])
        t1 = float(t[i + 1])
        if not (math.isfinite(t0) and math.isfinite(t1)):
            raise ValueError("non-finite t encountered")

        dt = t1 - t0
        if dt == 0.0:
            A[i + 1] = A[i]
            continue

        n_sub = int(math.ceil(abs(dt) / dt_max))
        n_sub = max(n_sub, 1)
        dt_sub = dt / float(n_sub)

        a = complex(A[i])
        for k in range(n_sub):
            t_mid = t0 + (k + 0.5) * dt_sub
            beta = float(beta_fn(float(t_mid)))
            gamma = float(gamma_fn(float(t_mid)))
            if not (math.isfinite(beta) and math.isfinite(gamma)):
                raise ValueError("beta/gamma must be finite")
            coef = (1j * beta - gamma) * dt_sub
            a = a * complex(np.exp(coef))
        A[i + 1] = a

    return A
