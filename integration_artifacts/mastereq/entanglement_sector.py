"""Entanglement-sector helpers for Unified GKSL integration.

This module mirrors the Bridge-E0 CHSH runner orientation:
- runner-side observable: CHSH S from coincidence outcomes
- GKSL-side hook: off-diagonal dephasing rate gamma (1/km)

The mapping is intentionally minimal and deterministic for equivalence tests.
"""
from __future__ import annotations

import math
import numpy as np
from typing import Callable

from .defaults import DEFAULT_GAMMA_KM_INV
from .microphysics import gamma_km_inv_from_n_sigma_v, sigma_entanglement_reference_cm2


def make_entanglement_dephasing_fn(
    gamma: float | None = None,
    *,
    use_microphysics: bool = False,
    n_cm3: float = 1.0e18,
    E_GeV_ref: float = 1.0,
    visibility: float = 1.0,
    v_cm_s: float = 3.0e10,
) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Return a simple off-diagonal dephasing dissipator for entanglement studies."""
    if gamma is None and use_microphysics:
        sigma = sigma_entanglement_reference_cm2(E_GeV_ref, visibility)
        gamma = gamma_km_inv_from_n_sigma_v(n_cm3, sigma, v_cm_s)
    elif gamma is None:
        gamma = DEFAULT_GAMMA_KM_INV

    gamma = float(gamma)

    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        D = np.zeros_like(rho, dtype=complex)
        D[0, 1] = -gamma * rho[0, 1]
        D[1, 0] = -gamma * rho[1, 0]
        return D

    return Dfn


def chsh_visibility_from_gamma(
    gamma_km_inv: float,
    L_km: float,
    *,
    s0: float = 2.0 * math.sqrt(2.0),
) -> float:
    """Template mapping from dephasing to CHSH magnitude.

    For two-qubit visibility model V(L)=exp(-gamma L), CHSH scales as:
      |S|(L) = S0 * exp(-gamma L), with S0 <= 2*sqrt(2).
    """
    g = max(0.0, float(gamma_km_inv))
    L = max(0.0, float(L_km))
    return float(s0) * math.exp(-g * L)


__all__ = [
    "make_entanglement_dephasing_fn",
    "chsh_visibility_from_gamma",
]
