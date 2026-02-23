"""Toy LIGO / gravitational-sector helpers for the unified GKSL API.

This module provides a simple mapping that converts a local gravitational
strain/potential effect into a mass-basis modulation for the master equation.
It is intentionally minimal and designed to be a placeholder for more detailed
physics mappings later.
"""
from __future__ import annotations
import numpy as np
from typing import Callable


def make_ligo_mass_modulation(amplitude_eV2: float, omega_km_inv: float = 0.0, phase: float = 0.0) -> Callable[[float, float], np.ndarray]:
    """Return a mass-basis deltaM2 function modeling a gravitational modulation.

    amplitude_eV2: amplitude of the mass-squared modulation (eV^2)
    omega_km_inv: spatial frequency in 1/km (0 for constant amplitude)
    phase: phase offset

    The function returns a 2x2 real mass-basis matrix in eV^2 units.
    """
    def f(L_km: float, E_GeV: float) -> np.ndarray:
        factor = 1.0
        if omega_km_inv != 0.0:
            factor = np.cos(omega_km_inv * L_km + phase)
        return float(amplitude_eV2) * float(factor) * np.array([[1.0, 0.0], [0.0, -1.0]], dtype=float)

    return f


def make_ligo_damping(gamma_g: float) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Return a trivial damping function for LIGO-sector scattering/relaxation.

    The toy model applies population relaxation toward equal-split at rate gamma_g.
    """
    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        D = np.zeros_like(rho, dtype=complex)
        tr = np.trace(rho)
        target = 0.5 * tr
        D[0, 0] = -gamma_g * (rho[0, 0] - target)
        D[1, 1] = -gamma_g * (rho[1, 1] - target)
        return D

    return Dfn


__all__ = ["make_ligo_mass_modulation", "make_ligo_damping"]
