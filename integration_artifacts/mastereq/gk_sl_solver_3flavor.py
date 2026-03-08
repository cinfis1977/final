"""3-flavor GKSL (Lindblad) density-matrix solver.

This is a generalization of the repo's existing 2-flavor toy solver.
It integrates

  d rho / dL = -i [H(L,E), rho] + D(L,E,rho)

where L is baseline in km, H has units 1/km, and E is in GeV.

Conventions:
- Uses the same KCONST=1.267 scaling as the 2-flavor code:
    H_vac = KCONST * U * (M^2/(2E)) * U^†
  with M^2 = diag(0, dm21, dm31) in eV^2 and E in GeV.

- Matter potential, when provided, is added directly in flavor basis in 1/km.

This module is intended to enable genuinely dynamical WEAK runners (3-flavor
vacuum/MSW), while keeping 2-flavor paths intact for legacy golden comparisons.
"""

from __future__ import annotations

import math
from typing import Callable, Literal

import numpy as np

# Keep the same conversion constant used throughout this repo.
KCONST = 1.267

Rho = np.ndarray  # 3x3 complex
HFn3 = Callable[[float, float], np.ndarray]  # (L_km, E_GeV) -> 3x3 Hermitian
DampingFn3 = Callable[[float, float, Rho], np.ndarray]


Flavor = Literal["e", "mu", "tau"]


def commutator(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return A @ B - B @ A


def pmns_matrix(theta12: float, theta13: float, theta23: float, delta_cp: float) -> np.ndarray:
    """PDG parameterization of the PMNS matrix (no Majorana phases)."""
    s12, c12 = math.sin(theta12), math.cos(theta12)
    s13, c13 = math.sin(theta13), math.cos(theta13)
    s23, c23 = math.sin(theta23), math.cos(theta23)

    e_minus = math.cos(delta_cp) - 1j * math.sin(delta_cp)
    e_plus = math.cos(delta_cp) + 1j * math.sin(delta_cp)

    U = np.zeros((3, 3), dtype=complex)

    # First row
    U[0, 0] = c12 * c13
    U[0, 1] = s12 * c13
    U[0, 2] = s13 * e_minus

    # Second row
    U[1, 0] = -s12 * c23 - c12 * s23 * s13 * e_plus
    U[1, 1] = c12 * c23 - s12 * s23 * s13 * e_plus
    U[1, 2] = s23 * c13

    # Third row
    U[2, 0] = s12 * s23 - c12 * c23 * s13 * e_plus
    U[2, 1] = -c12 * s23 - s12 * c23 * s13 * e_plus
    U[2, 2] = c23 * c13

    return U


def vacuum_hamiltonian_3flavor(
    dm21: float,
    dm31: float,
    theta12: float,
    theta13: float,
    theta23: float,
    delta_cp: float,
    E_GeV: float,
) -> np.ndarray:
    """Return 3x3 vacuum Hamiltonian in flavor basis in units of 1/km."""
    U = pmns_matrix(theta12, theta13, theta23, delta_cp)
    M2 = np.diag([0.0, float(dm21), float(dm31)]).astype(float)
    H_mass = M2 / (2.0 * max(float(E_GeV), 1e-12))
    H_flav = U @ H_mass @ U.conj().T
    H_flav *= KCONST
    return H_flav


def flavor_projector(flavor: Flavor) -> np.ndarray:
    idx = {"e": 0, "mu": 1, "tau": 2}[flavor]
    P = np.zeros((3, 3), dtype=complex)
    P[idx, idx] = 1.0 + 0j
    return P


def initial_rho(flavor_in: Flavor) -> Rho:
    P = flavor_projector(flavor_in)
    return P.copy()


def lindblad_dephasing_offdiag(rho: Rho, gamma_offdiag: float) -> np.ndarray:
    """Pure dephasing: damp all off-diagonal elements equally."""
    D = np.zeros_like(rho, dtype=complex)
    g = float(gamma_offdiag)
    if g == 0.0:
        return D
    for i in range(3):
        for j in range(3):
            if i != j:
                D[i, j] = -g * rho[i, j]
    return D


def rk4_step(rho: Rho, L: float, h: float, E_GeV: float, Hfn: HFn3, Dfn: DampingFn3) -> Rho:
    def drho(Lloc: float, rloc: Rho) -> Rho:
        H = Hfn(Lloc, E_GeV)
        D = Dfn(Lloc, E_GeV, rloc)
        return -1j * commutator(H, rloc) + D

    k1 = drho(L, rho)
    k2 = drho(L + 0.5 * h, rho + 0.5 * h * k1)
    k3 = drho(L + 0.5 * h, rho + 0.5 * h * k2)
    k4 = drho(L + h, rho + h * k3)
    return rho + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def integrate_rho_3flavor(
    L_km: float,
    E_GeV: float,
    Hfn: HFn3,
    Dfn: DampingFn3,
    *,
    steps: int = 1000,
    flavor_in: Flavor = "mu",
) -> Rho:
    rho = initial_rho(flavor_in)

    L_km = float(L_km)
    steps = int(steps)
    h = max(L_km / max(steps, 1), 1e-8)
    L = 0.0

    for _ in range(steps):
        if L + h > L_km:
            h = L_km - L
            if h <= 0:
                break
        rho = rk4_step(rho, L, h, float(E_GeV), Hfn, Dfn)
        L += h

    # numeric stabilization
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho)
    if tr != 0 and abs(tr - 1.0) > 1e-10:
        rho = rho / tr
    return rho


def prob_from_rho(rho: Rho, flavor_out: Flavor) -> float:
    idx = {"e": 0, "mu": 1, "tau": 2}[flavor_out]
    return float(np.real(rho[idx, idx]))


__all__ = [
    "KCONST",
    "Flavor",
    "pmns_matrix",
    "vacuum_hamiltonian_3flavor",
    "lindblad_dephasing_offdiag",
    "integrate_rho_3flavor",
    "prob_from_rho",
]
