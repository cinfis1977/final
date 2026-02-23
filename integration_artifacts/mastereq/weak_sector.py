"""Simple weak-sector integration helpers for the unified GKSL API.

Provides a flavor-basis matter potential and optional small dephasing.
These are intentionally simple placeholders to demonstrate the integration
pattern; real physical mapping should replace the toy scaling factors.
"""
from __future__ import annotations
import numpy as np
from typing import Callable, Tuple

# A tiny scale to convert electron density (cm^-3) to an effective potential
# in 1/km units for this toy model. This is NOT physical accuracy; it's a tunable
# placeholder so the demo runs with sensible magnitudes.
NE_TO_V_SCALE = 1e-22


def make_weak_flavor_H_fn(ne_cm3: float, scale: float = 1.0) -> Callable[[float, float], np.ndarray]:
    """Return a flavor-basis Hamiltonian term function H_weak(L,E) = diag(V,0).

    V = scale * NE_TO_V_SCALE * ne_cm3 (units 1/km in this toy mapping).
    """
    V = float(scale) * NE_TO_V_SCALE * float(ne_cm3)

    def Hfn(L_km: float, E_GeV: float) -> np.ndarray:
        return np.array([[V, 0.0], [0.0, 0.0]], dtype=complex)

    return Hfn


def make_weak_damping_fn(gamma: float) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Return a simple off-diagonal damping function for weak-sector environmental effects."""
    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        D = np.zeros_like(rho, dtype=complex)
        D[0, 1] = -gamma * rho[0, 1]
        D[1, 0] = -gamma * rho[1, 0]
        return D
    return Dfn


# --- Conversion helpers ---
# Practical numerical constants
VE_COEFF = 7.63e-14  # V_e [eV] ≈ VE_COEFF * Y_e * rho[g/cm^3]
EV_TO_KM_INV = 5.0677307e3  # 1 eV = 5.0677e3 km^{-1}
KCONST = 1.267  # same as solver constant


def ve_from_rho(rho_gcm3: float, Ye: float = 0.5) -> float:
    """Compute V_e in eV from mass density (g/cm^3) and electron fraction Y_e."""
    return float(VE_COEFF) * float(Ye) * float(rho_gcm3)


def ve_to_H_km_inv(Ve_eV: float) -> float:
    """Convert V_e [eV] to Hamiltonian units [1/km]."""
    return float(Ve_eV) * float(EV_TO_KM_INV)


def ve_to_delta_m2_equiv(Ve_eV: float, E_GeV: float, K: float = KCONST) -> float:
    """Return equivalent Δm^2 [eV^2] such that K Δm^2 / (2E) = H_from_V.

    Uses H_from_V = Ve_eV * EV_TO_KM_INV (1/km), and Δm^2_equiv = (2 E / K) * H_from_V.
    """
    H = ve_to_H_km_inv(Ve_eV)
    return (2.0 * float(E_GeV) / float(K)) * H


def delta_m2_from_rho(rho_gcm3: float, Ye: float, E_GeV: float, K: float = KCONST) -> float:
    """Convenience: compute Δm^2_equiv from density and energy."""
    Ve = ve_from_rho(rho_gcm3, Ye)
    return ve_to_delta_m2_equiv(Ve, E_GeV, K)


__all__ = ["make_weak_flavor_H_fn", "make_weak_damping_fn", "ve_from_rho", "ve_to_H_km_inv", "ve_to_delta_m2_equiv", "delta_m2_from_rho"]


__all__ = ["make_weak_flavor_H_fn", "make_weak_damping_fn"]
