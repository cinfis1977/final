"""MSW (matter) sector helpers for the unified GKSL API.

Provides a flavor-basis matter potential H_ms(L,E) built from a local
mass density `rho_gcm3` and electron fraction `Ye`, plus a small
toy damping function. This module re-uses the conversion helpers from
the `weak_sector` so the numerical conventions remain consistent with
the existing integration artifacts.
"""
from __future__ import annotations
import numpy as np
from typing import Callable

from .weak_sector import ve_from_rho, ve_to_H_km_inv


def make_msw_flavor_H_fn(rho_gcm3: float, Ye: float = 0.5) -> Callable[[float, float], np.ndarray]:
    """Return a flavor-basis Hamiltonian function implementing the MSW potential.

    The produced Hfn(L_km, E_GeV) returns a 2x2 complex matrix `diag(V, 0)` where
    V is the matter potential converted to the solver units (1/km) using the
    helper conversions from `weak_sector`.
    """
    Ve_eV = ve_from_rho(float(rho_gcm3), float(Ye))
    V_km_inv = ve_to_H_km_inv(Ve_eV)

    def Hfn(L_km: float, E_GeV: float) -> np.ndarray:
        return np.array([[V_km_inv, 0.0], [0.0, 0.0]], dtype=complex)

    return Hfn


def make_msw_damping_fn(gamma: float = 1e-4) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Simple decoherence acting to damp off-diagonal coherences in flavor basis."""
    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        D = np.zeros_like(rho, dtype=complex)
        D[0, 1] = -gamma * rho[0, 1]
        D[1, 0] = -gamma * rho[1, 0]
        return D

    return Dfn


__all__ = ["make_msw_flavor_H_fn", "make_msw_damping_fn"]
