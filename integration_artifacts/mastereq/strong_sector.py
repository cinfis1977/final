"""Toy strong-sector integration helpers for the unified GKSL API.

Provides a mass-basis delta-m^2 correction (diagonal in mass basis) and an
optional population-damping Lindblad term to model strong-interaction induced
environmental effects in a toy fashion.

This is intentionally simple and tunable for demos and tests.
"""
from __future__ import annotations
import numpy as np


def make_strong_mass_fn(amplitude: float, k_km: float = 0.0) -> callable:
    """Return a mass-basis deltaM2 function: amplitude * cos(k*L) * sigma_z.

    amplitude: float (eV^2 scale in this toy mapping)
    k_km: spatial frequency in 1/km
    """
    def f(L_km: float, E_GeV: float) -> np.ndarray:
        phase = 1.0
        if k_km != 0.0:
            phase = np.cos(k_km * L_km)
        return amplitude * phase * np.array([[1.0, 0.0], [0.0, -1.0]], dtype=float)

    return f


def make_strong_population_damping(gamma_pop: float) -> callable:
    """Return a damping function that relaxes populations toward equal mixture.

    D(rho) = -gamma_pop * (rho - 0.5 * I * trace(rho))
    """
    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        tr = np.trace(rho)
        target = 0.5 * tr * np.eye(2, dtype=complex)
        return -float(gamma_pop) * (rho - target)

    return Dfn


__all__ = ["make_strong_mass_fn", "make_strong_population_damping"]

# --- Conversion helpers ---
KCONST = 1.267  # same constant used by solver
EV_TO_KM_INV = 5.0677307e3


def mass_amp_to_H(amplitude_eV2: float, E_GeV: float, K: float = KCONST) -> float:
    """Convert a mass-basis amplitude (eV^2) into Hamiltonian units [1/km].

    H = K * amplitude / (2 E)
    """
    return float(K) * float(amplitude_eV2) / (2.0 * float(E_GeV))


def H_to_mass_amp(H_km_inv: float, E_GeV: float, K: float = KCONST) -> float:
    """Inverse: convert H (1/km) to equivalent mass-basis amplitude (eV^2)."""
    return (2.0 * float(E_GeV) / float(K)) * float(H_km_inv)


__all__ = ["make_strong_mass_fn", "make_strong_population_damping", "mass_amp_to_H", "H_to_mass_amp"]
