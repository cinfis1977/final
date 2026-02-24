"""Toy LIGO / gravitational-sector helpers for the unified GKSL API.

This module provides a simple mapping that converts a local gravitational
strain/potential effect into a mass-basis modulation for the master equation.
It is intentionally minimal and designed to be a placeholder for more detailed
physics mappings later.
"""
from __future__ import annotations
import numpy as np
from typing import Callable
from .defaults import DEFAULT_GAMMA_KM_INV


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


def make_ligo_damping(gamma_g: float | None = None, mode: str = "lindblad", equilibrium: float | None = None) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Return a damping function for the LIGO sector.

    Parameters
    - gamma_g: nominal overall rate scale (1/km).
    - mode: 'lindblad' (default) to use explicit GKSL jump operators, or 'toy' to
      return the previous simple population-relaxation form.
    - equilibrium: optional target population for state |0> (between 0 and 1).
      If None, the default equal-mix (0.5) is used. When provided, the Lindblad
      jump rates are chosen to relax populations toward this target.
    """
    mode = str(mode).lower()
    if gamma_g is None:
        gamma_g = DEFAULT_GAMMA_KM_INV

    if mode == "toy":
        def Dfn_toy(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
            D = np.zeros_like(rho, dtype=complex)
            tr = np.trace(rho)
            target = 0.5 * tr
            D[0, 0] = -gamma_g * (rho[0, 0] - target)
            D[1, 1] = -gamma_g * (rho[1, 1] - target)
            return D

        return Dfn_toy

    # Default to Lindblad pair construction
    eq = 0.5 if equilibrium is None else float(equilibrium)
    if not (0.0 <= eq <= 1.0):
        raise ValueError("equilibrium must be between 0 and 1")

    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        # Choose forward/back rates r01 (0<-1) and r10 (1<-0) so that steady-state
        # population for |0> is r10/(r01+r10) = eq. Use gamma_g to set overall scale.
        r10 = gamma_g * float(eq)
        r01 = gamma_g * (1.0 - float(eq))

        s1 = np.sqrt(max(r10, 0.0))
        s2 = np.sqrt(max(r01, 0.0))

        L1 = s1 * np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)  # moves 1->0
        L2 = s2 * np.array([[0.0, 0.0], [1.0, 0.0]], dtype=complex)  # moves 0->1

        def single_gksl(Lmat: np.ndarray, r: np.ndarray) -> np.ndarray:
            term1 = Lmat @ r @ Lmat.conj().T
            LdagL = Lmat.conj().T @ Lmat
            term2 = 0.5 * (LdagL @ r + r @ LdagL)
            return term1 - term2

        return single_gksl(L1, rho) + single_gksl(L2, rho)

    return Dfn


__all__ = ["make_ligo_mass_modulation", "make_ligo_damping"]
