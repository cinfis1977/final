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
from .defaults import DEFAULT_GAMMA_KM_INV
from .microphysics import electron_density_from_rho_ye, sigma_weak_nue_e_cm2, gamma_km_inv_from_n_sigma_v


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


def make_msw_damping_fn(
    gamma: float | None = None,
    *,
    use_microphysics: bool = False,
    rho_gcm3: float = 3.0,
    Ye: float = 0.5,
    E_GeV_ref: float = 1.0,
    v_cm_s: float = 3.0e10,
) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Return a GKSL Lindblad dissipator implementing pure dephasing in flavor basis.

    We implement the dissipator via a single Hermitian jump operator
    $L=\sqrt{\gamma/2}\,\sigma_z$ (with $\sigma_z=\mathrm{diag}(1,-1)$).

    The GKSL term for a single operator is
    $\mathcal{D}[\rho]=L\rho L^\dagger-\tfrac12\{L^\dagger L,\rho\}$.

    For this Hermitian choice the result simplifies to
    $\mathcal{D}[\rho]=(\gamma/2)(\sigma_z\rho\sigma_z-\rho)$,
    which preserves trace and damps off-diagonal coherences with rate $\gamma$.
    """
    if gamma is None and use_microphysics:
        n_e = electron_density_from_rho_ye(rho_gcm3, Ye)
        sigma = sigma_weak_nue_e_cm2(E_GeV_ref)
        gamma = gamma_km_inv_from_n_sigma_v(n_e, sigma, v_cm_s)
    elif gamma is None:
        gamma = DEFAULT_GAMMA_KM_INV

    gamma = float(gamma)

    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        Lmat = np.sqrt(float(gamma) / 2.0) * sz
        # GKSL: L rho L^dag - 0.5 * (L^dag L rho + rho L^dag L)
        term1 = Lmat @ rho @ Lmat.conj().T
        LdagL = Lmat.conj().T @ Lmat
        term2 = 0.5 * (LdagL @ rho + rho @ LdagL)
        return term1 - term2

    return Dfn


__all__ = ["make_msw_flavor_H_fn", "make_msw_damping_fn"]
