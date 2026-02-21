#!/usr/bin/env python3
"""
strong_rho_from_sigmatot_dispersion_v1.py

Purpose
-------
Compute rho(s) predictions from sigma_tot(s) using a simple high-energy
derivative-dispersion-relation proxy:

    rho(s) ≈ (pi/2) * d ln sigma_tot(s) / d ln s

This tool enforces *dispersive consistency* between sigma_tot and rho,
so you can test whether a given sigma_tot bridge/coupling (SM vs GEO)
moves rho in the right direction WITHOUT introducing an independent
"rho-specific phase knob".

Notes / Scope
-------------
- This is a diagnostic harness, not a full rigorous DDR implementation.
- It uses numerical derivatives on the analytic sigma model (SM or GEO),
  not on the data points, to avoid grid artefacts.
- No fitting/scan is performed; you provide A and env_mode for sigma_geo.

Inputs
------
- sigma_tot dataset csv: pdg_sigma_tot_clean_for_runner.csv
- rho dataset csv: pdg_rho_clean_for_runner.csv

Outputs
-------
- CSV with rho predictions for each rho data point (SM and GEO)
- JSON summary with chi2 (diag) for SM and GEO vs rho data

Example
-------
py -3 .\\strong_rho_from_sigmatot_dispersion_v1.py ^
  --sigma_data .\\data\\hepdata\\pdg_sigma_tot_clean_for_runner.csv ^
  --rho_data   .\\data\\hepdata\\pdg_rho_clean_for_runner.csv ^
  --A -0.003 --env_mode eikonal --template cos ^
  --sqrts_ref_GeV 13000 --delta_geo_ref -1.315523 --c1_abs 0.725147 ^
  --out .\\out_rho_from_sig_disp.csv ^
  --chi2_out .\\out_rho_from_sig_disp_chi2.json
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd

# We reuse the exact sigma_tot baseline + geo bridge implementation
# to stay code-faithful and avoid duplicating formulas.
from strong_sigma_tot_energy_scan_v2 import PDGParams, sigma_tot_pdg_mb, sigma_geo_mb, env_scale_radius_from_sigma, env_scale

def chi2_diag(y: np.ndarray, mu: np.ndarray, err: np.ndarray) -> float:
    z = (y - mu) / err
    return float(np.sum(z * z))

def env_scale_eikonal(sqrts: np.ndarray, sqrts_ref: float, sM_GeV2: float) -> np.ndarray:
    s = np.asarray(sqrts, dtype=float) ** 2
    s_ref = float(sqrts_ref) ** 2
    sM = float(sM_GeV2)
    logx = np.log(np.maximum(s / sM, 1e-30))
    logx_ref = float(np.log(max(s_ref / sM, 1e-30)))
    if abs(logx_ref) < 1e-12:
        return np.ones_like(logx)
    return logx / logx_ref

def sigma_sm_geo(sqrts: float, channel: str, pars: PDGParams, *,
                 A: float, template: str, env_mode: str, sqrts_ref_GeV: float,
                 delta_geo_ref: float, c1_abs: float) -> tuple[float, float]:
    sq = np.array([float(sqrts)], dtype=float)
    sm = float(sigma_tot_pdg_mb(sq, channel, pars)[0])

    if A == 0.0:
        return sm, sm

    # match v2 scaling logic exactly
    if env_mode == "radius":
        sm_ref = float(sigma_tot_pdg_mb(np.array([sqrts_ref_GeV], dtype=float), channel, pars)[0])
        scale = env_scale_radius_from_sigma(np.array([sm]), sm_ref)
    elif env_mode == "eikonal":
        scale = env_scale_eikonal(np.array([sqrts]), sqrts_ref_GeV, pars.sM_GeV2)
    else:
        scale = env_scale(np.array([sqrts]), env_mode, sqrts_ref_GeV)

    geo = float(sigma_geo_mb(
        np.array([sm], dtype=float), np.array([sqrts], dtype=float),
        A_rad=A, delta_geo_ref_rad=delta_geo_ref, c1_abs=c1_abs, template=template,
        env_mode=env_mode, sqrts_ref_GeV=sqrts_ref_GeV, scale_override=scale
    )[0])
    return sm, geo

def rho_from_sigma_model(sqrts: float, channel: str, pars: PDGParams, *,
                         which: str,
                         A: float, template: str, env_mode: str, sqrts_ref_GeV: float,
                         delta_geo_ref: float, c1_abs: float,
                         h: float = 1e-4) -> float:
    """
    Numerical derivative for rho(s) ≈ (pi/2) d ln sigma / d ln s
    using central differences in x = ln s.
    """
    # x = ln s ; s = (sqrts)^2
    s = float(sqrts) ** 2
    x0 = math.log(max(s, 1e-30))

    def sigma_at_x(x: float) -> float:
        s_here = math.exp(x)
        sq_here = math.sqrt(s_here)
        sm, geo = sigma_sm_geo(
            sq_here, channel, pars,
            A=A, template=template, env_mode=env_mode, sqrts_ref_GeV=sqrts_ref_GeV,
            delta_geo_ref=delta_geo_ref, c1_abs=c1_abs
        )
        return sm if which == "SM" else geo

    sig_p = sigma_at_x(x0 + h)
    sig_m = sigma_at_x(x0 - h)
    # derivative of ln sigma wrt ln s:
    dlnsig_dlns = (math.log(sig_p) - math.log(sig_m)) / (2.0 * h)
    return (math.pi / 2.0) * dlnsig_dlns

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sigma_data", required=True, help="sigma_tot csv (for metadata / channel list)")
    ap.add_argument("--rho_data", required=True, help="rho csv to score against")
    ap.add_argument("--A", type=float, default=0.0)
    ap.add_argument("--A_I", type=float, default=None, help="(two-channel) Imag/bulk amplitude. If set, overrides --A for dispersion-from-sigma tests.")
    ap.add_argument("--A_R", type=float, default=None, help="(two-channel) Real/interference amplitude (unused here; accepted for symmetry).")
    ap.add_argument("--template", choices=["cos", "sin"], default="cos")
    ap.add_argument("--env_mode", choices=["none", "debroglie", "log", "radius", "eikonal"], default="none")
    ap.add_argument("--sqrts_ref_GeV", type=float, default=13000.0)
    ap.add_argument("--delta_geo_ref", type=float, default=-1.315523)
    ap.add_argument("--c1_abs", type=float, default=0.725147)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chi2_out", required=True)
    args = ap.parse_args()

    # two-channel amplitude selection (bulk panel): A_eff = A_I if provided else A
    A_eff = float(args.A_I) if args.A_I is not None else float(args.A)

    pars = PDGParams()

    rho_df = pd.read_csv(args.rho_data)
    # normalize columns
    if "sqrts_GeV" not in rho_df.columns and "sqrt_s" in rho_df.columns:
        rho_df = rho_df.rename(columns={"sqrt_s": "sqrts_GeV"})
    if "err" not in rho_df.columns and "err_mb" in rho_df.columns:
        rho_df = rho_df.rename(columns={"err_mb": "err"})
    if "rho" not in rho_df.columns:
        raise SystemExit("rho_data must contain a 'rho' column")
    if "sqrts_GeV" not in rho_df.columns:
        raise SystemExit("rho_data must contain a 'sqrts_GeV' column")
    if "channel" not in rho_df.columns:
        raise SystemExit("rho_data must contain a 'channel' column")
    if "err" not in rho_df.columns:
        raise SystemExit("rho_data must contain an 'err' column")

    preds_sm = []
    preds_geo = []
    for _, r in rho_df.iterrows():
        sq = float(r["sqrts_GeV"])
        ch = str(r["channel"]).strip()
        preds_sm.append(rho_from_sigma_model(
            sq, ch, pars, which="SM",
            A=0.0, template=args.template, env_mode="none", sqrts_ref_GeV=args.sqrts_ref_GeV,
            delta_geo_ref=args.delta_geo_ref, c1_abs=args.c1_abs
        ))
        preds_geo.append(rho_from_sigma_model(
            sq, ch, pars, which="GEO",
            A=float(A_eff), template=args.template, env_mode=args.env_mode, sqrts_ref_GeV=args.sqrts_ref_GeV,
            delta_geo_ref=args.delta_geo_ref, c1_abs=args.c1_abs
        ))

    out = rho_df.copy()
    out["rho_pred_SM_disp"] = np.array(preds_sm, dtype=float)
    out["rho_pred_GEO_disp"] = np.array(preds_geo, dtype=float)
    out["pull_SM"] = (out["rho"] - out["rho_pred_SM_disp"]) / out["err"]
    out["pull_GEO"] = (out["rho"] - out["rho_pred_GEO_disp"]) / out["err"]
    out.to_csv(args.out, index=False)

    y = out["rho"].to_numpy(dtype=float)
    e = out["err"].to_numpy(dtype=float)
    chi_sm = chi2_diag(y, out["rho_pred_SM_disp"].to_numpy(dtype=float), e)
    chi_geo = chi2_diag(y, out["rho_pred_GEO_disp"].to_numpy(dtype=float), e)

    summary = {
        "sigma_data": args.sigma_data,
        "rho_data": args.rho_data,
        "A_rad": float(A_eff),
        "A": float(args.A),
        "A_I": (None if args.A_I is None else float(args.A_I)),
        "A_R": (None if args.A_R is None else float(args.A_R)),
        "template": args.template,
        "env_mode": args.env_mode,
        "sqrts_ref_GeV": float(args.sqrts_ref_GeV),
        "delta_geo_ref": float(args.delta_geo_ref),
        "c1_abs": float(args.c1_abs),
        "n": int(len(out)),
        "chi2_SM_disp": float(chi_sm),
        "chi2_GEO_disp": float(chi_geo),
        "dchi2": float(chi_sm - chi_geo),
        "note": "rho computed from sigma_tot via rho≈(pi/2)d ln sigma/d ln s; diagnostic harness"
    }
    Path(args.chi2_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
