"""Toy Dark Matter (DM) sector helpers for the unified GKSL API.

This module provides a simple mapping from an oscillating background scalar
field (axion-like) or local DM density into a mass-basis modulation and an
optional scattering-induced damping. The goal is to illustrate how DM-driven
terms enter the master equation and provide conversion helpers.
"""
from __future__ import annotations
import numpy as np
from typing import Callable

# Conversion constants
EV_TO_KM_INV = 5.0677307e3
KCONST = 1.267


def make_dm_mass_modulation(amplitude_eV2: float, omega_km_inv: float = 0.0, phase: float = 0.0) -> Callable[[float, float], np.ndarray]:
    """Return a mass-basis deltaM2 function modeling oscillating DM background.

    amplitude_eV2: amplitude of the mass-squared modulation (eV^2)
    omega_km_inv: spatial frequency in 1/km (set 0 for constant amplitude)
    phase: phase offset
    The returned function f(L_km, E_GeV) -> 2x2 real mass-basis matrix.
    """
    def f(L_km: float, E_GeV: float) -> np.ndarray:
        factor = 1.0
        if omega_km_inv != 0.0:
            factor = np.cos(omega_km_inv * L_km + phase)
        return float(amplitude_eV2) * float(factor) * np.array([[1.0, 0.0], [0.0, -1.0]], dtype=float)

    return f


def make_dm_scattering_damping(gamma_s: float) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Return a damping function modeling DM-induced scattering (population damping).

    gamma_s: rate in 1/km units applied to populations
    D(rho) = -gamma_s * diag(rho - target_pop)
    """
    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        D = np.zeros_like(rho, dtype=complex)
        tr = np.trace(rho)
        # simple model: relax populations toward trace-weighted split
        target = 0.5 * tr
        D[0, 0] = -gamma_s * (rho[0, 0] - target)
        D[1, 1] = -gamma_s * (rho[1, 1] - target)
        return D

    return Dfn


def dm_density_to_amplitude(rho_DM_GeV_cm3: float, coupling_g: float, E_GeV: float) -> float:
    """Estimate an effective mass-squared amplitude (eV^2) from local DM density.

    This is a toy linear mapping: amplitude ~ g * rho_DM / E (units chosen for demo).
    Users should replace with a physically derived mapping for specific models.
    """
    # Physical scaling: 1 GeV/cm^3 ~ 1.7827e-6 eV^4, so amplitude ~ g * rho_DM * 1.7827e-6 / E
    # This keeps the amplitude in a physically reasonable range for typical g, rho_DM, E.
    return float(coupling_g) * float(rho_DM_GeV_cm3) * 1.7827e-6 / max(1e-12, float(E_GeV))


__all__ = [
    "make_dm_mass_modulation",
    "make_dm_scattering_damping",
    "dm_density_to_amplitude",
]
