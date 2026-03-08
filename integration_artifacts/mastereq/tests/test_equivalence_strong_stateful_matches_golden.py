from pathlib import Path

import numpy as np
import pandas as pd

from integration_artifacts.mastereq.strong_pdg_stateful_dynamics import (
    PDGParamsSigmaTot,
    PDGParamsRho,
    scan_sigma_tot_stateful,
    scan_rho_stateful,
)


def test_strong_sigma_tot_stateful_matches_golden_output_columns():
    repo = Path(__file__).resolve().parents[3]
    golden_csv = repo / "integration_artifacts" / "out" / "verdict_golden" / "out_sigmatot_GEO_Aneg003.csv"
    assert golden_csv.exists(), f"Missing golden output: {golden_csv}"

    df = pd.read_csv(golden_csv)
    assert len(df) > 0

    A = -0.003
    env_mode = "eikonal"
    sqrts_ref_GeV = 13000.0
    delta_geo_ref = -1.315523
    c1_abs = 0.725147

    pars = PDGParamsSigmaTot()

    sq = df["sqrts_GeV"].to_numpy(dtype=float)
    ch = df["channel"].astype(str).str.lower().to_numpy()

    sigma_sm = np.empty_like(sq)
    scale = np.empty_like(sq)
    sigma_geo = np.empty_like(sq)
    for channel in ("pp", "pbarp"):
        mask = ch == channel
        if not np.any(mask):
            continue
        sm, sc, geo = scan_sigma_tot_stateful(
            sq[mask],
            channel,  # type: ignore[arg-type]
            pars,
            A_rad=A,
            delta_geo_ref_rad=delta_geo_ref,
            c1_abs=c1_abs,
            template="cos",
            env_mode=env_mode,
            sqrts_ref_GeV=sqrts_ref_GeV,
        )
        sigma_sm[mask] = sm
        scale[mask] = sc
        sigma_geo[mask] = geo

    assert np.allclose(df["sigma_sm_mb"].to_numpy(dtype=float), sigma_sm, atol=1e-10, rtol=0.0)
    assert np.allclose(df["env_scale"].to_numpy(dtype=float), scale, atol=1e-12, rtol=0.0)
    assert np.allclose(df["sigma_geo_mb"].to_numpy(dtype=float), sigma_geo, atol=1e-10, rtol=0.0)


def test_strong_rho_stateful_matches_golden_output_columns():
    repo = Path(__file__).resolve().parents[3]
    golden_csv = repo / "integration_artifacts" / "out" / "verdict_golden" / "out_rho_GEO_eikonal_Aneg003.csv"
    assert golden_csv.exists(), f"Missing golden output: {golden_csv}"

    df = pd.read_csv(golden_csv)
    assert len(df) > 0

    A = -0.003
    sqrts_ref_GeV = 13000.0
    delta_geo_ref = -1.315523
    c1_abs = 0.725147

    pars = PDGParamsRho()

    sq = df["sqrts_GeV"].to_numpy(dtype=float)
    ch = df["channel"].astype(str).str.lower().to_numpy()

    sigma_sm = np.empty_like(sq)
    rho_sm = np.empty_like(sq)
    phi = np.empty_like(sq)
    sigma_geo = np.empty_like(sq)
    rho_geo = np.empty_like(sq)

    for channel in ("pp", "pbarp"):
        mask = ch == channel
        if not np.any(mask):
            continue
        sm, rsm, ph, sgeo, rgeo = scan_rho_stateful(
            sq[mask],
            channel,  # type: ignore[arg-type]
            pars,
            A=A,
            delta_geo_ref=delta_geo_ref,
            c1_abs=c1_abs,
            template="cos",
            env_mode="eikonal",
            sqrts_ref_GeV=sqrts_ref_GeV,
        )
        sigma_sm[mask] = sm
        rho_sm[mask] = rsm
        phi[mask] = ph
        sigma_geo[mask] = sgeo
        rho_geo[mask] = rgeo

    assert np.allclose(df["sigma_sm_mb"].to_numpy(dtype=float), sigma_sm, atol=1e-10, rtol=0.0)
    assert np.allclose(df["rho_sm"].to_numpy(dtype=float), rho_sm, atol=1e-10, rtol=0.0)
    assert np.allclose(df["phi_geo_rad"].to_numpy(dtype=float), phi, atol=1e-12, rtol=0.0)

    assert np.allclose(df["sigma_geo_mb"].to_numpy(dtype=float), sigma_geo, atol=1e-10, rtol=0.0)
    assert np.allclose(df["rho_geo"].to_numpy(dtype=float), rho_geo, atol=1e-10, rtol=0.0)
