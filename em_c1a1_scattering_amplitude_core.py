from __future__ import annotations

import math
from typing import Callable, Iterable, Optional

import numpy as np


def evolve_A_over_scan_c1a1(
    s_values: Iterable[float],
    *,
    s0: float,
    A0: complex,
    beta_fn: Callable[[float], float],
    gamma_fn: Callable[[float], float],
    m_hol_fn: Optional[Callable[[float, complex], complex]] = None,
    dt_max: float,
) -> np.ndarray:
    """Evolve complex amplitude A over scan with optional holomorphic term.

    Coordinate: t = ln(s/s0)

    C1a.1 law:
      dA/dt = (i*beta(t) - gamma(t) + m_hol(t, A)) * A

    If m_hol_fn is None, this reduces to C1a.

    Implementation: substep RK4 with step size <= dt_max.

    Notes:
    - We keep this solver explicit and deterministic.
    - dt refinement tests are expected to show small changes when dt_max is halved.
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

    def deriv(ti: float, Ai: complex) -> complex:
        beta = float(beta_fn(float(ti)))
        gamma = float(gamma_fn(float(ti)))
        if not (math.isfinite(beta) and math.isfinite(gamma)):
            raise ValueError("beta/gamma must be finite")
        m = 0.0 + 0.0j
        if m_hol_fn is not None:
            m = complex(m_hol_fn(float(ti), complex(Ai)))
            if not (math.isfinite(m.real) and math.isfinite(m.imag)):
                raise ValueError("m_hol must be finite")
        coef = (1j * beta - gamma + m)
        return coef * complex(Ai)

    A = np.zeros(s_arr.size, dtype=np.complex128)
    A[0] = complex(A0)

    for i in range(s_arr.size - 1):
        t0 = float(t[i])
        t1 = float(t[i + 1])
        dt = t1 - t0
        if dt == 0.0:
            A[i + 1] = A[i]
            continue

        n_sub = int(math.ceil(abs(dt) / dt_max))
        n_sub = max(n_sub, 1)
        h = dt / float(n_sub)

        a = complex(A[i])
        for k in range(n_sub):
            tk = t0 + k * h
            k1 = deriv(tk, a)
            k2 = deriv(tk + 0.5 * h, a + 0.5 * h * k1)
            k3 = deriv(tk + 0.5 * h, a + 0.5 * h * k2)
            k4 = deriv(tk + h, a + h * k3)
            a = a + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        A[i + 1] = a

    return A
