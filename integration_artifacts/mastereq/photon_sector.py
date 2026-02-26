"""Photon/birefringence-sector helpers for Unified GKSL integration.

Contains:
- deterministic formulas mirroring prereg runners in entanglement_photon_bridge
- an optional dephasing hook for the GKSL scaffolding
"""
from __future__ import annotations

import math
import numpy as np
from typing import Callable

from .defaults import DEFAULT_GAMMA_KM_INV
from .microphysics import gamma_km_inv_from_n_sigma_v, sigma_photon_birefringence_reference_cm2


def make_photon_birefringence_damping_fn(
    gamma: float | None = None,
    *,
    use_microphysics: bool = False,
    n_cm3: float = 1.0e16,
    E_GeV_ref: float = 1.0,
    coupling_x: float = 1.0,
    v_cm_s: float = 3.0e10,
) -> Callable[[float, float, np.ndarray], np.ndarray]:
    """Return off-diagonal dephasing dissipator for photon-sector templates."""
    if gamma is None and use_microphysics:
        sigma = sigma_photon_birefringence_reference_cm2(E_GeV_ref, coupling_x)
        gamma = gamma_km_inv_from_n_sigma_v(n_cm3, sigma, v_cm_s)
    elif gamma is None:
        gamma = DEFAULT_GAMMA_KM_INV

    gamma = float(gamma)

    def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
        D = np.zeros_like(rho, dtype=complex)
        D[0, 1] = -gamma * rho[0, 1]
        D[1, 0] = -gamma * rho[1, 0]
        return D

    return Dfn


def cmb_prereg_locked_check(
    beta_cal_deg: float,
    sigma_cal_deg: float,
    beta_hold_deg: float,
    sigma_hold_deg: float,
    *,
    k_sigma: float = 2.0,
) -> dict[str, float | str]:
    """Mirror prereg_cmb_birefringence_v1_DROPIN.py math exactly."""
    C_beta = float(beta_cal_deg)
    sig = math.sqrt(float(sigma_cal_deg) ** 2 + float(sigma_hold_deg) ** 2)
    diff = float(beta_hold_deg) - C_beta
    z = diff / sig if sig > 0.0 else float("inf")
    verdict = "PASS" if abs(z) <= float(k_sigma) else "FAIL"
    sign_ok = (C_beta == 0.0) or (float(beta_hold_deg) == 0.0) or (
        math.copysign(1.0, C_beta) == math.copysign(1.0, float(beta_hold_deg))
    )
    sign_verdict = "OK" if sign_ok else "MISMATCH"
    return {
        "C_beta_locked_deg": C_beta,
        "diff_deg": diff,
        "sigma_comb_deg": sig,
        "z_score": z,
        "k_sigma": float(k_sigma),
        "verdict": verdict,
        "sign_verdict": sign_verdict,
    }


def frw_E(z: float, Om: float, Ol: float, Or: float) -> float:
    """Mirror E(z) definition in prereg_birefringence_accumulation_v1_DROPIN.py."""
    return math.sqrt(float(Or) * (1.0 + z) ** 4 + float(Om) * (1.0 + z) ** 3 + float(Ol))


def frw_I(z: float, Om: float, Ol: float, Or: float, n_steps: int = 20000) -> float:
    """Mirror Simpson integration used in prereg_birefringence_accumulation runner."""
    z = float(z)
    if z <= 0.0:
        return 0.0
    n = max(200, int(n_steps))
    if n % 2 == 1:
        n += 1
    a = 0.0
    b = z
    h = (b - a) / n
    s = 0.0
    for i in range(n + 1):
        zz = a + i * h
        denom = (1.0 + zz) * frw_E(zz, Om, Ol, Or)
        term = 1.0 / denom
        if i == 0 or i == n:
            w = 1.0
        elif i % 2 == 1:
            w = 4.0
        else:
            w = 2.0
        s += w * term
    return s * h / 3.0


def accumulation_prereg_locked_check(
    *,
    z_cal: float,
    beta_cal_deg: float,
    sigma_cal_deg: float,
    z_hold: float,
    beta_hold_deg: float,
    sigma_hold_deg: float,
    Om: float = 0.315,
    Ol: float = 0.685,
    Or: float = 0.0,
    k_sigma: float = 2.0,
    abs_test: bool = False,
) -> dict[str, float | str | int]:
    """Mirror prereg_birefringence_accumulation_v1_DROPIN.py math exactly."""
    I_cal = frw_I(z_cal, Om, Ol, Or)
    I_hold = frw_I(z_hold, Om, Ol, Or)
    if I_cal <= 0.0:
        raise ValueError("I(z_cal) <= 0; invalid calibration input")

    beta_cal = float(beta_cal_deg)
    sig_cal = float(sigma_cal_deg)
    beta_hold = float(beta_hold_deg)
    sig_hold = float(sigma_hold_deg)

    C_beta = beta_cal / I_cal
    beta_pred = C_beta * I_hold

    if bool(abs_test):
        diff = abs(beta_hold) - abs(beta_pred)
        metric = "abs(|beta|)"
    else:
        diff = beta_hold - beta_pred
        metric = "signed(beta)"

    sig = math.sqrt(sig_cal ** 2 + sig_hold ** 2)
    zscore = diff / sig if sig > 0.0 else float("inf")
    verdict = "PASS" if abs(zscore) <= float(k_sigma) else "FAIL"

    return {
        "I_cal": I_cal,
        "I_hold": I_hold,
        "C_beta_locked_per_I": C_beta,
        "beta_pred_hold_deg": beta_pred,
        "diff_deg": diff,
        "sigma_comb_deg": sig,
        "z_score": zscore,
        "k_sigma": float(k_sigma),
        "abs_test": int(bool(abs_test)),
        "metric": metric,
        "verdict": verdict,
    }


__all__ = [
    "make_photon_birefringence_damping_fn",
    "cmb_prereg_locked_check",
    "frw_E",
    "frw_I",
    "accumulation_prereg_locked_check",
]
