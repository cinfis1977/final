"""Toy EM-sector helpers for the unified GKSL API.

Provides a flavor-basis Hamiltonian from a neutrino magnetic moment coupling
to an external magnetic field. This is a demo mapping (not intended as a
precision physics module) to illustrate how an EM term can be added.
"""
from __future__ import annotations
import numpy as np
from typing import Callable

# Physical constants / conversion
MU_B_EV_PER_T = 5.7883818060e-5  # Bohr magneton in eV/T
EV_TO_KM_INV = 5.0677307e3       # 1 eV = 5.0677e3 km^{-1}


def make_em_flavor_H_fn(mu_nu_muB: float, B_field_T_fn: Callable[[float], float]) -> Callable[[float, float], np.ndarray]:
    """Return a flavor-basis off-diagonal Hamiltonian term from magnetic coupling.

    mu_nu_muB: neutrino magnetic moment in units of Bohr magneton (μ_B)
    B_field_T_fn: function B_field_T_fn(L_km) -> B in Tesla along baseline

    The toy mapping creates an off-diagonal coupling proportional to mu * B,
    placed as sigma_x in flavor basis (transition coupling).
    """
    mu_nu = float(mu_nu_muB) * MU_B_EV_PER_T

    def Hfn(L_km: float, E_GeV: float) -> np.ndarray:
        B = float(B_field_T_fn(L_km))
        # energy scale in eV
        delta_eV = mu_nu * B
        # convert to 1/km
        Hval = delta_eV * EV_TO_KM_INV
        return np.array([[0.0, Hval], [Hval, 0.0]], dtype=complex)

    return Hfn


def make_em_damping_from_radiation(gamma: float) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Toy damping: small off-diagonal damping due to EM interactions."""
    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        D = np.zeros_like(rho, dtype=complex)
        D[0, 1] = -gamma * rho[0, 1]
        D[1, 0] = -gamma * rho[1, 0]
        return D
    return Dfn


__all__ = ["make_em_flavor_H_fn", "make_em_damping_from_radiation"]
