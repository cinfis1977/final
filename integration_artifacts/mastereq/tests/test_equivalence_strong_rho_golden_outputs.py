import math
from pathlib import Path

import numpy as np
import pandas as pd


class _PDGParams:
    # Matches strong_rho_energy_scan_v3.py defaults
    sM_GeV2 = 1.0
    P_mb = 33.73
    H_mb = 0.283
    R1_mb = 13.67
    eta1 = 0.412
    R2_mb = 7.77
    eta2 = 0.562


def _sigma_tot_pdg_mb(sqrts_GeV: np.ndarray, channel: str, pars: _PDGParams) -> np.ndarray:
    s = np.asarray(sqrts_GeV, dtype=float) ** 2
    x = np.maximum(s / float(pars.sM_GeV2), 1e-30)
    logx = np.log(x)
    base = float(pars.P_mb) + float(pars.H_mb) * (logx**2) + float(pars.R1_mb) * (x ** (-float(pars.eta1)))
    odd = float(pars.R2_mb) * (x ** (-float(pars.eta2)))
    return base - odd if channel == "pp" else base + odd


def _dsigma_dlns_pdg_mb(sqrts_GeV: np.ndarray, channel: str, pars: _PDGParams) -> np.ndarray:
    s = np.asarray(sqrts_GeV, dtype=float) ** 2
    x = np.maximum(s / float(pars.sM_GeV2), 1e-30)
    logx = np.log(x)

    term_log = 2.0 * float(pars.H_mb) * logx
    term_r1 = -float(pars.eta1) * float(pars.R1_mb) * (x ** (-float(pars.eta1)))
    term_r2 = -float(pars.eta2) * float(pars.R2_mb) * (x ** (-float(pars.eta2)))

    if channel == "pp":
        return term_log + term_r1 - term_r2
    return term_log + term_r1 + term_r2


def _rho_sm_proxy(sqrts_GeV: np.ndarray, channel: str, pars: _PDGParams) -> np.ndarray:
    sig = np.maximum(_sigma_tot_pdg_mb(sqrts_GeV, channel, pars), 1e-30)
    ds = _dsigma_dlns_pdg_mb(sqrts_GeV, channel, pars)
    return (math.pi / 2.0) * (ds / sig)


def _eikonal_scale(sqrts_GeV: np.ndarray, *, sqrts_ref_GeV: float, sM_GeV2: float) -> np.ndarray:
    sq = np.asarray(sqrts_GeV, dtype=float)
    s = sq**2
    s_ref = float(sqrts_ref_GeV) ** 2
    logx = np.log(np.maximum(s / float(sM_GeV2), 1e-30))
    logx_ref = float(np.log(max(s_ref / float(sM_GeV2), 1e-30)))
    if abs(logx_ref) < 1e-12:
        return np.ones_like(logx)
    return logx / logx_ref


def _phi_geo(sqrts_GeV: np.ndarray, *, A: float, delta_geo_ref: float, c1_abs: float, scale: np.ndarray) -> np.ndarray:
    # Golden run uses template=cos and env_mode=eikonal (argument scaling)
    phase_arg = float(delta_geo_ref) * np.asarray(scale, dtype=float)
    mod = np.cos(phase_arg)
    return float(A) * float(c1_abs) * mod


def _rotate_rho_sigma(rho_sm: np.ndarray, sigma_sm: np.ndarray, phi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rho = np.asarray(rho_sm, dtype=float)
    sig = np.asarray(sigma_sm, dtype=float)
    ph = np.asarray(phi, dtype=float)

    c = np.cos(ph)
    s = np.sin(ph)

    re = rho * c - 1.0 * s
    im = rho * s + 1.0 * c

    im_safe = np.where(np.abs(im) < 1e-30, np.sign(im) * 1e-30 + 1e-30, im)
    rho_geo = re / im_safe
    sigma_geo = sig * im
    return rho_geo, sigma_geo


def test_strong_rho_golden_outputs_match_reference_math():
    repo = Path(__file__).resolve().parents[3]
    golden_csv = repo / "integration_artifacts" / "out" / "verdict_golden" / "out_rho_GEO_eikonal_Aneg003.csv"
    assert golden_csv.exists(), f"Missing golden output: {golden_csv}"

    df = pd.read_csv(golden_csv)
    assert len(df) > 0

    # Constants from the canonical verdict command
    A = -0.003
    sqrts_ref_GeV = 13000.0
    delta_geo_ref = -1.315523
    c1_abs = 0.725147

    pars = _PDGParams()

    sq = df["sqrts_GeV"].to_numpy(dtype=float)
    ch = df["channel"].astype(str).str.lower().to_numpy()

    sigma_sm_ref = np.empty_like(sq)
    rho_sm_ref = np.empty_like(sq)
    for i in range(len(sq)):
        sigma_sm_ref[i] = _sigma_tot_pdg_mb(np.array([sq[i]]), ch[i], pars)[0]
        rho_sm_ref[i] = _rho_sm_proxy(np.array([sq[i]]), ch[i], pars)[0]

    scale = _eikonal_scale(sq, sqrts_ref_GeV=sqrts_ref_GeV, sM_GeV2=pars.sM_GeV2)
    phi = _phi_geo(sq, A=A, delta_geo_ref=delta_geo_ref, c1_abs=c1_abs, scale=scale)

    rho_geo_ref, sigma_geo_ref = _rotate_rho_sigma(rho_sm_ref, sigma_sm_ref, phi)

    assert np.allclose(df["sigma_sm_mb"].to_numpy(dtype=float), sigma_sm_ref, atol=1e-10, rtol=0.0)
    assert np.allclose(df["rho_sm"].to_numpy(dtype=float), rho_sm_ref, atol=1e-10, rtol=0.0)
    assert np.allclose(df["phi_geo_rad"].to_numpy(dtype=float), phi, atol=1e-12, rtol=0.0)

    assert np.allclose(df["sigma_geo_mb"].to_numpy(dtype=float), sigma_geo_ref, atol=1e-10, rtol=0.0)
    assert np.allclose(df["rho_geo"].to_numpy(dtype=float), rho_geo_ref, atol=1e-10, rtol=0.0)
