import math
from pathlib import Path

import numpy as np
import pandas as pd


class _PDGParams:
    # Matches strong_sigma_tot_energy_scan_v2.py defaults
    P_mb = 33.73
    H_mb = 0.2838
    R1_mb = 13.67
    eta1 = 0.412
    R2_mb = 7.77
    eta2 = 0.5626
    mN_GeV = 0.938
    M_GeV = 2.076

    @property
    def sM_GeV2(self) -> float:
        return (2.0 * self.mN_GeV + self.M_GeV) ** 2


def _sigma_tot_pdg_mb(sqrts_GeV: np.ndarray, channel: str, pars: _PDGParams) -> np.ndarray:
    s = np.asarray(sqrts_GeV, dtype=float) ** 2
    sM = float(pars.sM_GeV2)
    x = np.maximum(s / sM, 1e-30)
    logx = np.log(x)
    base = float(pars.P_mb) + float(pars.H_mb) * (logx**2) + float(pars.R1_mb) * (x ** (-float(pars.eta1)))
    odd = float(pars.R2_mb) * (x ** (-float(pars.eta2)))
    if channel == "pp":
        return base - odd
    return base + odd


def _eikonal_scale(sqrts_GeV: np.ndarray, *, sqrts_ref_GeV: float, sM_GeV2: float) -> np.ndarray:
    sq = np.asarray(sqrts_GeV, dtype=float)
    s = sq**2
    s_ref = float(sqrts_ref_GeV) ** 2
    logx = np.log(np.maximum(s / float(sM_GeV2), 1e-30))
    logx_ref = float(np.log(max(s_ref / float(sM_GeV2), 1e-30)))
    if abs(logx_ref) < 1e-12:
        return np.ones_like(logx)
    return logx / logx_ref


def _sigma_geo_mb(sigma_sm: np.ndarray, *, A_rad: float, delta_geo_ref_rad: float, c1_abs: float, scale: np.ndarray) -> np.ndarray:
    # Golden run uses template=cos
    phase = float(delta_geo_ref_rad) * np.asarray(scale, dtype=float)
    t = np.cos(phase)
    return np.asarray(sigma_sm, dtype=float) * (1.0 + float(A_rad) * float(c1_abs) * t)


def test_strong_sigma_tot_golden_outputs_match_reference_math():
    repo = Path(__file__).resolve().parents[3]
    golden_csv = repo / "integration_artifacts" / "out" / "verdict_golden" / "out_sigmatot_GEO_Aneg003.csv"
    assert golden_csv.exists(), f"Missing golden output: {golden_csv}"

    df = pd.read_csv(golden_csv)
    assert len(df) > 0

    # Constants from the canonical verdict command
    A = -0.003
    env_mode = "eikonal"
    sqrts_ref_GeV = 13000.0
    delta_geo_ref = -1.315523
    c1_abs = 0.725147

    assert env_mode == "eikonal"  # keep the test explicit/intentional

    pars = _PDGParams()

    # Compute SM baseline and env scaling
    sq = df["sqrts_GeV"].to_numpy(dtype=float)
    ch = df["channel"].astype(str).str.lower().to_numpy()

    sigma_sm_ref = np.empty_like(sq)
    for i in range(len(sq)):
        sigma_sm_ref[i] = _sigma_tot_pdg_mb(np.array([sq[i]]), ch[i], pars)[0]

    scale = _eikonal_scale(sq, sqrts_ref_GeV=sqrts_ref_GeV, sM_GeV2=pars.sM_GeV2)
    sigma_geo_ref = _sigma_geo_mb(sigma_sm_ref, A_rad=A, delta_geo_ref_rad=delta_geo_ref, c1_abs=c1_abs, scale=scale)

    # Compare against golden columns
    assert np.allclose(df["sigma_sm_mb"].to_numpy(dtype=float), sigma_sm_ref, atol=1e-10, rtol=0.0)
    assert np.allclose(df["env_scale"].to_numpy(dtype=float), scale, atol=1e-12, rtol=0.0)
    assert np.allclose(df["sigma_geo_mb"].to_numpy(dtype=float), sigma_geo_ref, atol=1e-10, rtol=0.0)

    # Residual columns are deterministic functions of data + prediction
    y = df["sigma_mb"].to_numpy(dtype=float)
    e = df["err_mb"].to_numpy(dtype=float)
    resid_sm = (y - sigma_sm_ref) / e
    resid_geo = (y - sigma_geo_ref) / e
    assert np.allclose(df["resid_sm"].to_numpy(dtype=float), resid_sm, atol=1e-10, rtol=0.0)
    assert np.allclose(df["resid_geo"].to_numpy(dtype=float), resid_geo, atol=1e-10, rtol=0.0)
