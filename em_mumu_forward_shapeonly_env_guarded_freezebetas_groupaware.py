#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py

e+e- -> mu+mu- forward harness (LEP-like differential cross sections vs cos(theta)).

Goal: match the EM/Bhabha harness semantics so EM subchannels share ONE bridge form.

Model:
- baseline per-bin "Born-level gamma+Z" dσ/dcosθ in pb (PDG χ1/χ2 convention), bin-averaged.
- nuisance: one nonnegative normalization beta per energy group (group column in data).
- GEO: multiplicative modulation: pred_geo = pred_sm * (1 + delta_i)

Delta bridge (same as the Bhabha groupaware harness):
    t_abs = 0.5*s*(1 - cosθ)  (GeV^2)
    q = max(t_abs, t_ref^2) / t_ref^2
    f = alpha * log(q)
    R = R_max * (1 - exp(- zeta*(1 + omega0*t_ref) * |f|))
    delta = env_scale * A * struct_factor * gen_factor * R * sin(phi) * f
Options:
- --shape_only: remove per-group mean(delta) -> tests only intra-group shape
- --freeze_betas: fit betas on SM once and reuse for GEO (recommended for prereg tests)
- --beta_nonneg: enforce beta_g >= 0 (physical)
- --require_positive: fail if any (1+delta_i) <= 0

Inputs via pack json:
{
  "meta": {...},
  "data_csv": "lep_mumu_table13_clean.csv",
  "columns": { ... },
  "cov_files": { "stat":..., "sys_corr":..., "total":..., "diag_total":... }
}
(compatible with the uploaded lep_mumu_pack.json)

Outputs: prints summary + writes per-bin table to --out
"""

import argparse, json, math, os
import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

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

C_LIGHT = 299_792_458.0  # m/s


def _chis(s: float):
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


def structure_factor(structure: str) -> float:
    structure = (structure or "").lower().strip()
    if structure.startswith("off"):
        return -1.0
    return 1.0


def gen_factor(gen: str) -> float:
    gen = (gen or "").lower().strip()
    if gen == "lam2":
        return 2.0
    if gen == "lam3":
        return 3.0
    return 1.0


def omega0_from_geom(mode: str, L0_km: float) -> float:
    mode = (mode or "").lower().strip()
    if mode == "fixed":
        return math.pi / max(L0_km, 1e-12)
    try:
        return float(mode)
    except Exception:
        return 0.0


def load_pack(pack_path: str):
    with open(pack_path, "r", encoding="utf-8") as f:
        pack = json.load(f)
    base = os.path.dirname(os.path.abspath(pack_path))
    def abspath(rel):
        return rel if os.path.isabs(rel) else os.path.join(base, rel)
    data_csv = abspath(pack["data_csv"])
    cov_files = {k: abspath(v) for k, v in pack["cov_files"].items()}
    cols = pack.get("columns", pack.get("colmap", {}))
    df = pd.read_csv(data_csv)
    return pack, df, cov_files, cols


def load_cov(cov_files: dict, which: str) -> np.ndarray:
    p = cov_files[which]
    cov = pd.read_csv(p, header=None).values.astype(float)
    cov = 0.5 * (cov + cov.T)
    return cov


def inv_cov(cov: np.ndarray) -> np.ndarray:
    cov = cov.copy()
    jitter = 0.0
    for _ in range(8):
        try:
            L = np.linalg.cholesky(cov)
            Linv = np.linalg.inv(L)
            return Linv.T @ Linv
        except np.linalg.LinAlgError:
            jitter = 1e-12 if jitter == 0.0 else jitter * 10.0
            cov += np.eye(cov.shape[0]) * jitter
    return np.linalg.pinv(cov)


def chi2(obs: np.ndarray, pred: np.ndarray, cov_inv: np.ndarray) -> float:
    r = obs - pred
    return float(r.T @ cov_inv @ r)


def fit_betas_group_nonneg(obs: np.ndarray, base_curve: np.ndarray, group_ids: np.ndarray, n_groups: int, cov_inv: np.ndarray, nonneg: bool) -> np.ndarray:
    """
    Fit one beta per group: pred = sum_g beta_g * base_curve * 1_{group=g}
    Weighted by cov_inv (whitened LS).
    """
    N = len(obs)
    X = np.zeros((N, n_groups), dtype=float)
    for g in range(n_groups):
        m = (group_ids == g)
        X[m, g] = base_curve[m]

    # whiten with cov_inv
    try:
        L = np.linalg.cholesky(cov_inv)
        LT = L.T
        Xw = LT @ X
        yw = LT @ obs
    except np.linalg.LinAlgError:
        U, s, _ = np.linalg.svd(cov_inv)
        W = (U * np.sqrt(np.maximum(s, 0.0)))
        Xw = W.T @ X
        yw = W.T @ obs

    if nonneg:
        res = lsq_linear(Xw, yw, bounds=(0.0, np.inf), lsmr_tol="auto", verbose=0)
        beta = res.x
    else:
        beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    return beta.astype(float)


def build_delta(cos_ctr: np.ndarray, sqrt_s: np.ndarray, A: float, alpha: float, phi: float,
                geo_structure: str, geo_gen: str, omega0_geom: str, L0_km: float,
                zeta: float, R_max: float, t_ref_GeV: float, env_scale: float) -> np.ndarray:
    s = sqrt_s * sqrt_s
    t_abs = 0.5 * s * (1.0 - cos_ctr)  # GeV^2
    t_ref2 = max(t_ref_GeV, 1e-12) ** 2
    q = np.maximum(t_abs, t_ref2) / t_ref2
    f = alpha * np.log(q)
    omega0 = omega0_from_geom(omega0_geom, L0_km)
    x = zeta * (1.0 + omega0 * (t_ref_GeV + 1e-12)) * np.abs(f)
    R = R_max * (1.0 - np.exp(-x))
    delta = env_scale * A * structure_factor(geo_structure) * gen_factor(geo_gen) * R * math.sin(phi) * f
    return delta.astype(float)


def env_u_from_args(env_u: float|None, v_kms: float|None, r_over_Rs: float|None) -> float:
    if env_u is not None:
        return float(env_u)
    if v_kms is not None:
        v = float(v_kms) * 1_000.0
        return (v / C_LIGHT) ** 2
    if r_over_Rs is not None:
        r = float(r_over_Rs)
        return 0.5 / max(r, 1e-12)  # gives 0.05 at r=10
    return 1e-8  # lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True)
    ap.add_argument("--cov", default="total", choices=["total","stat","sys_corr","diag_total"])
    ap.add_argument("--A", type=float, default=0.0)
    ap.add_argument("--alpha", type=float, default=7.5e-05)
    ap.add_argument("--phi", type=float, default=math.pi/2)
    ap.add_argument("--geo_structure", default="offdiag")
    ap.add_argument("--geo_gen", default="lam2")
    ap.add_argument("--omega0_geom", default="fixed")
    ap.add_argument("--L0_km", type=float, default=810.0)
    ap.add_argument("--zeta", type=float, default=0.05)
    ap.add_argument("--R_max", type=float, default=10.0)
    ap.add_argument("--t_ref_GeV", type=float, default=0.02)
    ap.add_argument("--aic_k", type=int, default=2)
    ap.add_argument("--shape_only", action="store_true")
    ap.add_argument("--require_positive", action="store_true")
    ap.add_argument("--beta_nonneg", action="store_true")
    ap.add_argument("--freeze_betas", action="store_true")
    # env controls (same semantics as bhabha harness)
    ap.add_argument("--env_u0", type=float, default=1e-8)
    ap.add_argument("--env_u", type=float, default=None)
    ap.add_argument("--v_kms", type=float, default=None)
    ap.add_argument("--r_over_Rs", type=float, default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pack, df, cov_files, cols = load_pack(args.pack)

    # columns
    xlo = cols.get("cos_lo", "cos_lo")
    xhi = cols.get("cos_hi", "cos_hi")
    xct = cols.get("cos_ctr", "cos_ctr")
    ycol = cols.get("obs_pb", "obs_pb")
    gcol = cols.get("group", "group")
    ecol = cols.get("sqrt_s_GeV", "sqrt_s_GeV")

    cos_lo = df[xlo].to_numpy(float)
    cos_hi = df[xhi].to_numpy(float)
    cos_ctr = df[xct].to_numpy(float)
    obs = df[ycol].to_numpy(float)
    group_ids = df[gcol].astype(int).to_numpy()
    sqrt_s = df[ecol].to_numpy(float)

    # group remap to 0..G-1
    uniq = sorted(set(int(x) for x in group_ids))
    gmap = {g:i for i,g in enumerate(uniq)}
    gid = np.array([gmap[int(x)] for x in group_ids], dtype=int)
    G = len(uniq)

    cov = load_cov(cov_files, args.cov)
    cov_inv = inv_cov(cov)

    # baseline per bin (bin-averaged Born)
    pred0 = np.array([bin_avg(lambda c: dsigma_dcos_mumu(c, float(es)), float(lo), float(hi))
                      for lo,hi,es in zip(cos_lo, cos_hi, sqrt_s)], dtype=float)

    betas_sm = fit_betas_group_nonneg(obs, pred0, gid, G, cov_inv, args.beta_nonneg)
    pred_sm = np.zeros_like(obs, dtype=float)
    for g in range(G):
        m = (gid == g)
        pred_sm[m] = betas_sm[g] * pred0[m]
    chi2_sm = chi2(obs, pred_sm, cov_inv)

    # env scale
    env_u = env_u_from_args(args.env_u, args.v_kms, args.r_over_Rs)
    env_scale = env_u / max(args.env_u0, 1e-30)

    # delta
    delta = build_delta(
        cos_ctr=cos_ctr, sqrt_s=sqrt_s, A=args.A, alpha=args.alpha, phi=args.phi,
        geo_structure=args.geo_structure, geo_gen=args.geo_gen, omega0_geom=args.omega0_geom,
        L0_km=args.L0_km, zeta=args.zeta, R_max=args.R_max, t_ref_GeV=args.t_ref_GeV, env_scale=env_scale
    )

    if args.shape_only:
        # remove per-group mean(delta) so overall normalization isn't reintroduced via delta
        for g in range(G):
            m = (gid == g)
            delta[m] = delta[m] - float(np.mean(delta[m]))

    if args.require_positive and np.any(1.0 + delta <= 0.0):
        print("FAIL: require_positive triggered (some 1+delta <= 0).")
        raise SystemExit(2)

    pred_geo0 = pred_sm * (1.0 + delta)

    if args.freeze_betas:
        betas_geo = betas_sm.copy()
        pred_geo = pred_geo0
    else:
        # refit betas under GEO modulation (still physical if beta_nonneg)
        # since pred_geo0 already includes betas_sm, we refit against pred0*(1+delta)
        base_geo = pred0 * (1.0 + delta)
        betas_geo = fit_betas_group_nonneg(obs, base_geo, gid, G, cov_inv, args.beta_nonneg)
        pred_geo = np.zeros_like(obs, dtype=float)
        for g in range(G):
            m = (gid == g)
            pred_geo[m] = betas_geo[g] * base_geo[m]

    chi2_geo = chi2(obs, pred_geo, cov_inv)

    dchi2 = chi2_sm - chi2_geo
    dAIC = (chi2_sm - chi2_geo) - 2.0 * args.aic_k
    n = len(obs)
    dBIC = (chi2_sm - chi2_geo) - args.aic_k * math.log(max(n,1))

    print("\n========================")
    print("REAL-DATA EM (mu+mu-) FORWARD SUMMARY (bridge-aligned)")
    print("========================")
    print(f"pack      : {args.pack}")
    print(f"data_csv  : {pack.get('data_csv')}")
    print(f"cov       : {args.cov}")
    print(f"bins      : {len(obs)}  (groups={G}, ids={uniq})")
    print("baseline  : Born (gamma+Z) PDG χ1/χ2, massless; betas fitted per energy group")
    print(f"SM fit    : betas[{G}] = " + ", ".join([f"g{uniq[i]}={betas_sm[i]:.8g}" for i in range(G)]) + f"  chi2_SM={chi2_sm:.6f}")
    print(f"mech      : omega0={omega0_from_geom(args.omega0_geom, args.L0_km):.12g} (1/km) omega0_geom={args.omega0_geom} L0_km={args.L0_km} zeta={args.zeta} R_max={args.R_max} t_ref_GeV={args.t_ref_GeV}")
    print(f"env       : env_u={env_u:g} env_u0={args.env_u0:g} env_scale={env_scale:g}")
    print(f"geo       : A={args.A} alpha={args.alpha} phi={args.phi} structure={args.geo_structure} gen={args.geo_gen} shape_only={args.shape_only} freeze_betas={args.freeze_betas} beta_nonneg={args.beta_nonneg}")
    print(f"GEO fit   : betas[{G}] = " + ", ".join([f"g{uniq[i]}={betas_geo[i]:.8g}" for i in range(G)]) + f"  chi2_GEO={chi2_geo:.6f}")
    print("\n------------------------")
    print(f"TOTAL chi2_SM  = {chi2_sm:.6f}")
    print(f"TOTAL chi2_GEO = {chi2_geo:.6f}")
    print(f"Delta chi2 = chi2_SM - chi2_GEO = {dchi2:.6f}")
    print("------------------------")
    print(f"Delta AIC (k_extra={args.aic_k}): dAIC = {dAIC:.6f}")
    print(f"Delta BIC (k_extra={args.aic_k}): dBIC = {dBIC:.6f}")
    print("------------------------")

    out = df.copy()
    out["pred0_pb"] = pred0
    out["beta_sm"] = np.array([betas_sm[g] for g in gid], dtype=float)
    out["pred_sm"] = pred_sm
    out["delta"] = delta
    out["beta_geo"] = np.array([betas_geo[g] for g in gid], dtype=float)
    out["pred_geo"] = pred_geo
    out.to_csv(args.out, index=False)
    print(f"\nSaved: {args.out}\n")


if __name__ == "__main__":
    main()
