"""
Simple GKSL (Lindblad) density-matrix solver for a 2-flavor neutrino toy.
Provides utilities to build vacuum Hamiltonian, add a geometric delta-M^2 term,
and integrate d rho / dL = -i [H, rho] + D(rho) using RK4 over baseline L.

This is intentionally minimal and dependency-free (numpy only) to serve as
an executable toy for comparing with phase-shift approximations used in the
existing runners.

Author: GitHub Copilot (assistant)
"""
from __future__ import annotations
import math
import numpy as np
from typing import Callable, Tuple

# Physical conversion constants
# Use same conversion as code and notes: Delta = 1.267 * dm2 (eV^2) * L(km) / E(GeV)
KCONST = 1.267

# Type aliases
Rho = np.ndarray  # 2x2 complex
HFn = Callable[[float, float], np.ndarray]  # H(L_km, E_GeV) -> 2x2 Hermitian
DampingFn = Callable[[float, float, Rho], np.ndarray]  # D(rho) term


def pauli_matrices() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    sx = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    sy = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    return sx, sy, sz


def vacuum_hamiltonian_2flavor(dm2: float, theta: float, E_GeV: float) -> np.ndarray:
    """Return 2x2 vacuum Hamiltonian in flavor basis in units of 1/km.
    We construct H = (1/(2E)) U diag(m1^2, m2^2) U^\\u2020 and multiply by KCONST to
    convert to phase units consistent with Delta = 1.267 dm2 L/E.

    For two flavors, with m1^2 = 0, m2^2 = dm2.
    """
    # Mixing matrix
    c = math.cos(theta)
    s = math.sin(theta)
    U = np.array([[c, s], [-s, c]], dtype=complex)
    M2 = np.array([[0.0, 0.0], [0.0, dm2]], dtype=float)
    # H (in eV^2 / GeV) -> convert to phase per km by multiplication with KCONST/E
    H_mass = M2 / (2.0 * max(E_GeV, 1e-12))
    H_flav = U @ H_mass @ U.conj().T
    # Convert to units used in Delta: multiply by KCONST (1/km units)
    H_flav *= KCONST
    return H_flav


def geometric_delta_m2_2flavor(base_dphi_dL: float, E_GeV: float, scale_factor: float = 1.0) -> np.ndarray:
    """Return an effective 2x2 mass-squared correction matrix in flavor basis.

    For toy: place δM^2_geo proportional to sigma * base_dphi_dL times a Pauli-x structure
    in the mass basis rotated to flavor. This mimics an off-diagonal generator G.
    """
    # For 2-flavor toy, choose G = sigma_x in mass basis -> off-diagonal coupling
    sx, sy, sz = pauli_matrices()
    G_mass = sx  # off-diagonal generator in mass basis
    # scale conversion: as in notes, use Delta m^2_scale ~ E/2.534 to convert phase-gradient to eV^2
    # Here we accept a user-specified scale_factor to tune mapping; default 1.0
    dm2_geo = scale_factor * base_dphi_dL
    # Put into matrix form (mass basis) and rotate to flavor via U (same as vacuum diag)
    # For simplicity, assume mass-basis==flavor-basis mix angle handled externally; return mass-basis matrix
    # We'll return a flavor-basis δM2 by transforming with the same mixing as vacuum if needed by caller.
    return dm2_geo * G_mass


def lindblad_dephasing(rho: Rho, gamma_offdiag: float) -> np.ndarray:
    """Simple dephasing that damps off-diagonal elements: D(rho)_{ij} = -gamma_ij * rho_{ij} for i!=j.
    We keep populations unchanged (pure dephasing).
    """
    D = np.zeros_like(rho, dtype=complex)
    D[0, 1] = -gamma_offdiag * rho[0, 1]
    D[1, 0] = -gamma_offdiag * rho[1, 0]
    return D


def commutator(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return A @ B - B @ A


def rk4_step(rho: Rho, L: float, h: float, E_GeV: float, Hfn: HFn, Dfn: DampingFn) -> Rho:
    """Single RK4 step integrating d rho / dL = -i [H, rho] + D(rho)."""
    def drho(Lloc, rloc):
        H = Hfn(Lloc, E_GeV)
        D = Dfn(Lloc, E_GeV, rloc)
        return -1j * commutator(H, rloc) + D

    k1 = drho(L, rho)
    k2 = drho(L + 0.5 * h, rho + 0.5 * h * k1)
    k3 = drho(L + 0.5 * h, rho + 0.5 * h * k2)
    k4 = drho(L + h, rho + h * k3)
    return rho + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def integrate_rho(L_km: float, E_GeV: float, Hfn: HFn, Dfn: DampingFn, steps: int = 1000) -> Rho:
    """Integrate rho from L=0 to L=L_km.
    Initial state: pure flavor state |nu_mu><nu_mu| (second flavor as example).
    Returns density matrix at L=L_km.
    """
    # initial flavor state (mu) as basis vector e.g. |nu_mu> = [0,1]
    psi0 = np.array([0.0 + 0j, 1.0 + 0j], dtype=complex)
    rho = np.outer(psi0, psi0.conj())
    h = max(L_km / max(steps, 1), 1e-8)
    L = 0.0
    for i in range(steps):
        if L + h > L_km:
            h = L_km - L
            if h <= 0:
                break
        rho = rk4_step(rho, L, h, E_GeV, Hfn, Dfn)
        L += h
    # enforce Hermiticity / trace to mitigate numeric drift
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho)
    if abs(tr - 1.0) > 1e-12 and tr != 0:
        rho /= tr
    return rho


# --- Example H and D builder helpers ---

def build_Hfn_2flavor(dm2: float, theta: float, extra_dm2_fn: Callable[[float, float], np.ndarray]) -> HFn:
    """Return Hfn(L,E) that includes vacuum + extra (mass-basis) term transformed to flavor.
    extra_dm2_fn(L_km, E_GeV) -> 2x2 mass-basis delta M^2 matrix.
    """
    def Hfn(L_km, E_GeV):
        Hvac = vacuum_hamiltonian_2flavor(dm2, theta, E_GeV)
        # get extra delta M^2 in mass basis
        deltaM2_mass = extra_dm2_fn(L_km, E_GeV)
        # rotate deltaM2_mass to flavor basis using same U as vacuum
        c = math.cos(theta)
        s = math.sin(theta)
        U = np.array([[c, s], [-s, c]], dtype=complex)
        delta_mass_over_2E = deltaM2_mass / (2.0 * max(E_GeV, 1e-12))
        delta_flav = U @ delta_mass_over_2E @ U.conj().T
        # convert to KCONST units
        delta_flav *= KCONST
        Htot = Hvac + delta_flav
        return Htot
    return Hfn


def build_Dfn_simple(gamma0: float, junction_scale_fn: Callable[[float, float], float]) -> DampingFn:
    """Return a Dfn that applies off-diagonal dephasing with gamma = gamma0 * junction_scale(L,E).
    junction_scale_fn(L,E) should be in [0,1].
    """
    def Dfn(L_km, E_GeV, rho):
        gamma = float(gamma0) * float(junction_scale_fn(L_km, E_GeV))
        return lindblad_dephasing(rho, gamma)
    return Dfn


if __name__ == "__main__":
    # quick sanity self-test (very small)
    def zero_extra(L, E):
        return np.zeros((2,2), dtype=float)
    Hfn = build_Hfn_2flavor(dm2=2.5e-3, theta=math.radians(45.0), extra_dm2_fn=zero_extra)
    Dfn = build_Dfn_simple(0.0, lambda L, E: 1.0)
    rhoL = integrate_rho(295.0, 1.0, Hfn, Dfn, steps=200)
    print("rho at L=295 km:\n", rhoL)
