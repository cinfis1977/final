#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EM/EW leptonic null test (OPAL LEP2 e+e- -> mu+mu- angular distribution).

Baseline (SM Born-level, gamma+Z, massless) from PDG e+e- -> f fbar formula:
dσ/dΩ = Nc * α^2/(4s) * [ (1+cos^2θ) * (...) + 2cosθ*(...) ]
(See PDG e+e- cross section formulas; this script uses the standard χ1/χ2 form.)

GEO: multiplicative modulation on top of the baseline, sharing the same (A, alpha, phi, gen, structure)
parameter family as your other sectors.

Important:
- This is a *self-contained* baseline for mu+mu- (s-channel only). It is much cleaner than Bhabha (which needs ISR/FSR + cuts).
- Covariance: expects CSV matrix (no header) from pack.
- Nuisances: fits one normalization per energy-group (beta_g) by GLS each run.

Usage (PowerShell):
py -3 .\em_mumu_forward_dropin.py `
  --pack .\data\hepdata\lep_mumu_pack.json `
  --cov total `
  --A 0.0085 --alpha 7.5e-05 --phi 1.57079632679 `
  --geo_structure offdiag --geo_gen lam2 `
  --omega0_geom fixed --L0_km 810 `
  --zeta 0.05 --R_max 10 --t_ref_GeV 0.02 `
  --aic_k 2 `
  --out .\out_em_mumu_debug.csv
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

GEV2_TO_PB = 0.389379338e9  # 1 GeV^-2 = 0.389379338 mb = 0.389379338e9 pb

# --- EW constants (Born-level) ---
S_W2 = 0.23126
C_W2 = 1.0 - S_W2
MZ_GEV = 91.1876
GAMMAZ_GEV = 2.4952
ALPHA0 = 1.0 / 137.035999084

# PDG coupling convention:
# a_f = 2 T3_f ; v_f = 2 T3_f - 4 Q_f sin^2θW
# For charged leptons: Q=-1, T3=-1/2 -> a=-1, v=-1+4 sW2
A_E = -1.0
V_E = -1.0 + 4.0 * S_W2

A_MU = -1.0
V_MU = -1.0 + 4.0 * S_W2
Q_MU = -1.0
N_C = 1.0


def _chis(s: float) -> Tuple[float, float]:
    """Return (chi1, chi2) in the PDG χ1/χ2 notation."""
    denom = (s - MZ_GEV**2) ** 2 + (MZ_GEV * GAMMAZ_GEV) ** 2
    chi1 = (1.0 / (16.0 * S_W2 * C_W2)) * (s * (s - MZ_GEV**2)) / denom
    chi2 = (1.0 / (256.0 * (S_W2**2) * (C_W2**2))) * (s**2) / denom
    return chi1, chi2


def dsigma_dOmega_mumu(c: float, sqrt_s: float) -> float:
    """Born-level dσ/dΩ in GeV^-2 sr^-1 for e+e- -> mu+mu-."""
    s = sqrt_s * sqrt_s
    chi1, chi2 = _chis(s)

    term1 = (1.0 + c * c) * (
        (Q_MU**2)
        - 2.0 * chi1 * V_E * V_MU * Q_MU
        + chi2 * (A_E * A_E + V_E * V_E) * (A_MU * A_MU + V_MU * V_MU)
    )
    term2 = 2.0 * c * (
        -2.0 * chi1 * A_E * A_MU * Q_MU
        + 4.0 * chi2 * A_E * A_MU * V_E * V_MU
    )

    return N_C * (ALPHA0**2) / (4.0 * s) * (term1 + term2)


def dsigma_dcos_mumu(c: float, sqrt_s: float) -> float:
    """Born-level dσ/dcosθ in pb (already integrated over φ)."""
    return (2.0 * math.pi) * dsigma_dOmega_mumu(c, sqrt_s) * GEV2_TO_PB


def bin_avg(func, lo: float, hi: float, n: int = 400) -> float:
    xs = np.linspace(lo, hi, n)
    vals = np.array([func(float(x)) for x in xs], dtype=float)
    return float(vals.mean())


def generator_factor(gen: str) -> float:
    gen = (gen or "").lower().strip()
    if gen.startswith("lam"):
        try:
            return float(gen.replace("lam", ""))
        except Exception:
            return 1.0
    if gen in ("one", "unit"):
        return 1.0
    return 1.0


def structure_factor(structure: str) -> float:
    structure = (structure or "").lower().strip()
    # Keep convention compatible with your other drop-ins:
    # diag = +1, offdiag = -1
    if structure.startswith("off"):
        return -1.0
    return 1.0


def mech_response(t_proxy: float, omega0: float, zeta: float, r_max: float, t_ref: float) -> float:
    """
    Simple, transparent response:
    - Use a bounded, smooth function of |t| that can be shared across sectors.
    - This is NOT a claim of full mechanics; it is the same kind of universal response scalar you used in other drop-ins.
    """
    x = max(t_proxy / max(t_ref, 1e-12), 0.0)
    # Mild roll-off + cap
    r = 1.0 / math.sqrt(1.0 + (2.0 * zeta * x) ** 2)
    return min(r_max, r)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True)
    ap.add_argument("--cov", choices=["total", "stat", "sys_corr", "diag_total"], default="total")
    ap.add_argument("--A", type=float, default=0.0)
    ap.add_argument(
        "--alpha",
        type=float,
        default=0.0,
        help="DEPRECATED (EM only): use --em_alpha_tshape. Kept for backward compatibility.",
    )
    ap.add_argument(
        "--em_alpha_tshape",
        type=float,
        default=None,
        help="EM |t|-shape exponent for f(|t|) = (|t|/t_ref)**em_alpha_tshape; overrides --alpha if provided.",
    )
    ap.add_argument("--phi", type=float, default=math.pi / 2.0)
    ap.add_argument("--geo_structure", type=str, default="diag")
    ap.add_argument("--geo_gen", type=str, default="lam1")
    ap.add_argument("--omega0_geom", type=str, default="fixed")
    ap.add_argument("--L0_km", type=float, default=810.0)
    ap.add_argument("--zeta", type=float, default=0.05)
    ap.add_argument("--R_max", type=float, default=10.0)
    ap.add_argument("--t_ref_GeV", type=float, default=0.02)
    ap.add_argument("--aic_k", type=int, default=2)
    ap.add_argument("--out", type=str, default="out_em_mumu_debug.csv")
    return ap.parse_args()


def load_pack(pack_path: str) -> Tuple[dict, pd.DataFrame]:
    pack = json.load(open(pack_path, "r", encoding="utf-8"))
    base_dir = os.path.dirname(os.path.abspath(pack_path))
    data_csv = pack["data_csv"]
    data_csv_path = data_csv if os.path.isabs(data_csv) else os.path.join(base_dir, data_csv)
    df = pd.read_csv(data_csv_path)
    return pack, df


def load_cov(pack: dict, pack_path: str, which: str) -> np.ndarray:
    base_dir = os.path.dirname(os.path.abspath(pack_path))
    cov_rel = pack["cov_files"][which]
    cov_path = cov_rel if os.path.isabs(cov_rel) else os.path.join(base_dir, cov_rel)
    cov = pd.read_csv(cov_path, header=None).values.astype(float)
    cov = 0.5 * (cov + cov.T)  # symmetrize
    return cov


def gls_fit_betas(A: np.ndarray, y: np.ndarray, C: np.ndarray) -> np.ndarray:
    # Solve beta = (A^T C^-1 A)^-1 A^T C^-1 y using stable linear solves
    Ci_y = np.linalg.solve(C, y)
    Ci_A = np.linalg.solve(C, A)
    M = A.T @ Ci_A
    b = A.T @ Ci_y
    return np.linalg.solve(M, b)


def main() -> None:
    args = parse_args()
    pack, df = load_pack(args.pack)

    em_alpha_tshape = float(args.alpha) if args.em_alpha_tshape is None else float(args.em_alpha_tshape)

    cov_key_map = {
        "total": "total",
        "stat": "stat",
        "sys_corr": "sys_corr",
        "diag_total": "diag_total",
    }
    C = load_cov(pack, args.pack, cov_key_map[args.cov])

    # Determine group structure (energy groups)
    groups = sorted(df["group"].unique().tolist())
    G = len(groups)

    # Baseline per bin (Born-level gamma+Z)
    pred0 = np.zeros(len(df), dtype=float)
    t_proxy = np.zeros(len(df), dtype=float)

    for i, row in df.iterrows():
        sqrt_s = float(row["sqrt_s_GeV"])
        lo = float(row["cos_lo"])
        hi = float(row["cos_hi"])
        ctr = float(row["cos_ctr"])
        pred0[i] = bin_avg(lambda c: dsigma_dcos_mumu(c, sqrt_s), lo, hi, n=500)
        # |t| proxy in GeV^2 for response shaping (massless kinematics)
        s = sqrt_s * sqrt_s
        t_proxy[i] = max(0.0, 0.5 * s * (1.0 - ctr))

    y = df["obs_pb"].values.astype(float)

    # Nuisance design matrix: one normalization per energy group
    A_mat = np.zeros((len(df), G), dtype=float)
    for i, g in enumerate(df["group"].values.astype(int)):
        A_mat[i, groups.index(g)] = pred0[i]

    # SM fit (betas only)
    beta_sm = gls_fit_betas(A_mat, y, C)
    pred_sm = A_mat @ beta_sm
    res_sm = y - pred_sm
    chi2_sm = float(res_sm.T @ np.linalg.solve(C, res_sm))

    # GEO modulation (shared kernel)
    g_fac = generator_factor(args.geo_gen)
    s_fac = structure_factor(args.geo_structure)

    if args.omega0_geom.lower().strip() == "fixed":
        omega0 = math.pi / max(args.L0_km, 1e-9)  # 1/km
    else:
        omega0 = math.pi / max(args.L0_km, 1e-9)

    # Shape factor f(|t|) with alpha control (alpha small -> near-constant)
    f_shape = np.power(np.maximum(t_proxy / max(args.t_ref_GeV, 1e-12), 1e-12), em_alpha_tshape)

    R = np.array([mech_response(tp, omega0, args.zeta, args.R_max, args.t_ref_GeV) for tp in t_proxy], dtype=float)
    delta = args.A * s_fac * g_fac * R * math.sin(args.phi) * f_shape

    pred0_geo = pred0 * (1.0 + delta)

    A_geo = np.zeros((len(df), G), dtype=float)
    for i, g in enumerate(df["group"].values.astype(int)):
        A_geo[i, groups.index(g)] = pred0_geo[i]

    beta_geo = gls_fit_betas(A_geo, y, C)
    pred_geo = A_geo @ beta_geo
    res_geo = y - pred_geo
    chi2_geo = float(res_geo.T @ np.linalg.solve(C, res_geo))

    dchi2 = chi2_sm - chi2_geo
    N = len(y)
    k_extra = int(args.aic_k)
    dAIC = dchi2 - 2.0 * k_extra
    dBIC = dchi2 - k_extra * math.log(max(N, 1))

    print("\n========================")
    print("REAL-DATA EM (mu+mu-) FORWARD SUMMARY")
    print("========================")
    print(f"pack      : {args.pack}")
    print(f"data_csv  : {pack['data_csv']}")
    print(f"cov       : {args.cov}")
    print(f"bins      : {N}  (groups={G})")
    print("baseline  : Born (gamma+Z) PDG χ1/χ2, massless; betas fitted per energy group")
    print(f"SM fit    : betas={beta_sm}  chi2_SM={chi2_sm:.6f}")
    print(f"mech      : omega0={omega0:.10f} (1/km) omega0_geom={args.omega0_geom} L0_km={args.L0_km} zeta={args.zeta} R_max={args.R_max} t_ref_GeV={args.t_ref_GeV}")
    print(f"geo       : A={args.A} em_alpha_tshape={em_alpha_tshape} phi={args.phi} structure={args.geo_structure} gen={args.geo_gen}")
    print(f"GEO fit   : betas={beta_geo}  chi2_GEO={chi2_geo:.6f}")
    print("\n------------------------")
    print(f"TOTAL chi2_SM  = {chi2_sm:.6f}")
    print(f"TOTAL chi2_GEO = {chi2_geo:.6f}")
    print(f"Delta chi2 = chi2_SM - chi2_GEO = {dchi2:.6f}")
    print("------------------------")
    print(f"Delta AIC (k_extra={k_extra}): dAIC = {dAIC:.6f}")
    print(f"Delta BIC (k_extra={k_extra}): dBIC = {dBIC:.6f}")
    print(f"\nSaved: {args.out}")

    # Save debug CSV
    out = df.copy()
    out["pred_sm_pb"] = pred_sm
    out["pred_geo_pb"] = pred_geo
    out["res_sm"] = res_sm
    out["res_geo"] = res_geo
    # diag pulls (not full-cov decomposition, just for quick per-bin sanity)
    diag_sigma = np.sqrt(np.clip(np.diag(C), 1e-30, None))
    out["pull_sm_diag"] = res_sm / diag_sigma
    out["pull_geo_diag"] = res_geo / diag_sigma
    out.to_csv(args.out, index=False)


if __name__ == "__main__":
    main()
