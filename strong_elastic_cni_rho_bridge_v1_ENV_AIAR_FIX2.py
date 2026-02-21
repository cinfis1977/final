#!/usr/bin/env python3
# strong_elastic_cni_rho_bridge_v1.py
#
# Strong-sector CNI/ρ runner (pp elastic, very small-|t|, Coulomb-Nuclear Interference).
#
# NO-FIT / NO-SCAN philosophy:
#   1) Baseline is FROZEN from published physical parameters (sigma_tot, rho, B).
#      Do NOT fit these to this table.
#   2) Geometry produces a single-shot phase delta_geo from CurvedCube (du_phase/u_phase).
#   3) GEO enters as an extra *phase* on the nuclear amplitude:
#        F_N^geo(t) = F_N^SM(t) * exp(i * phase_geo(t))
#      with phase_geo(t) = A * ENV(t) * TEMPLATE( s(t), delta_geo )
#   4) Compare chi2 under the same covariance (diag from stat/sys columns):
#        dchi2 = chi2_SM - chi2_GEO  (positive => GEO improves)
#
# Strict null:
#   - If A==0, CurvedCube must NOT be called.
#
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import inspect
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
# --- FRW environment scale (drop-in)
from cosmo_env_apply_dropin_v1 import env_scale as _env_scale
from cosmo_env_apply_dropin_v1 import apply_env_to_delta_geo as _apply_env_to_delta_geo

import pandas as pd

try:
    if os.name == "nt":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HBARC2_MB_GEV2 = 0.389379338  # (ħc)^2 in mb·GeV^2
ALPHA_EM = 1.0 / 137.035999084
EULER_GAMMA = 0.5772156649015329

# ----------------------------
# IO helpers
# ----------------------------
def _load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _join(pack_dir: str, rel: str) -> str:
    return os.path.join(pack_dir, rel)

def _infer_t_columns(df: pd.DataFrame) -> Tuple[str, str, str]:
    candidates = [
        ("t_lo", "t_ctr", "t_hi"),
        ("t_lo_GeV2", "t_ctr_GeV2", "t_hi_GeV2"),
        ("t_lo_GEV2", "t_ctr_GEV2", "t_hi_GEV2"),
    ]
    cols = set(df.columns)
    for a, b, c in candidates:
        if a in cols and b in cols and c in cols:
            return a, b, c
    raise ValueError("Could not infer t_lo/t_ctr/t_hi columns from dsdt CSV.")

def _load_cov_from_table(df: pd.DataFrame, cov_kind: str) -> np.ndarray:
    cov_kind = (cov_kind or "total").lower()
    if cov_kind not in ("total", "stat", "sys"):
        raise ValueError("--cov must be total|stat|sys")

    stat = df.get("stat_mb_per_GeV2", pd.Series(np.zeros(len(df)))).to_numpy(float)
    sysu = df.get("sys_mb_per_GeV2", pd.Series(np.zeros(len(df)))).to_numpy(float)
    if cov_kind == "stat":
        v = np.clip(stat, 0, None) ** 2
    elif cov_kind == "sys":
        v = np.clip(sysu, 0, None) ** 2
    else:
        v = (np.clip(stat, 0, None) ** 2) + (np.clip(sysu, 0, None) ** 2)
    return np.diag(v)

# ----------------------------
# CurvedCube single-shot phase
# ----------------------------
def _wrap_pi(x: float) -> float:
    y = (x + math.pi) % (2.0 * math.pi) - math.pi
    if y <= -math.pi:
        y += 2.0 * math.pi
    return float(y)

def _curvedcube_delta_geo(
    k_rt: int,
    phi: float,
    zeta: float,
    geo_mode: str,
    baseline_km: float,
    L0_km: float,
    Nin: int,
    Nface: int,
) -> Tuple[float, float]:
    try:
        from weak_prob_engine_LAYERED_CURVED_v1 import _curvedcube_u_profile
    except Exception as e:
        raise RuntimeError(
            "Cannot import weak_prob_engine_LAYERED_CURVED_v1._curvedcube_u_profile. "
            "Run inside the same repo/env where run_curvedcube_predict_dcp_v6.py works."
        ) from e

    N = int(k_rt)
    phi = float(phi)
    zeta = float(zeta)

    sig = inspect.signature(_curvedcube_u_profile)
    params = sig.parameters
    kwargs = {}

    if "L_km" in params:
        kwargs["L_km"] = float(baseline_km)
    if "baseline_km" in params:
        kwargs["baseline_km"] = float(baseline_km)
    if "L0_km" in params:
        kwargs["L0_km"] = float(L0_km)
    if "phi" in params:
        kwargs["phi"] = phi
    if "zeta" in params:
        kwargs["zeta"] = zeta

    if "Nin" in params:
        kwargs["Nin"] = int(Nin)
    if "Nface" in params:
        kwargs["Nface"] = int(Nface)
    if "N_in" in params:
        kwargs["N_in"] = int(Nin)
    if "N_face" in params:
        kwargs["N_face"] = int(Nface)

    try:
        u = _curvedcube_u_profile(N, **kwargs)
    except TypeError:
        try:
            u = _curvedcube_u_profile(N, float(baseline_km), float(L0_km), phi, zeta)
        except TypeError:
            u = _curvedcube_u_profile(N, float(L0_km), float(baseline_km), phi, zeta)

    u = np.asarray(u, dtype=float)
    if u.ndim != 1 or u.size < 8:
        raise RuntimeError(f"CurvedCube u_profile invalid shape: {u.shape}")

    if geo_mode == "u_phase":
        a = u
    elif geo_mode == "du_phase":
        a = np.gradient(u)
    else:
        raise ValueError("Unknown geo_mode (use u_phase or du_phase)")

    theta = 2.0 * math.pi * (np.arange(u.size, dtype=float) / float(u.size))
    phasor = np.sum(a * np.exp(1j * theta))
    delta = _wrap_pi(float(np.angle(phasor)))

    denom = float(np.sum(np.abs(a)) + 1e-12)
    c1_abs = float(np.abs(phasor) / denom)
    return delta, c1_abs

# ----------------------------
# CNI baseline model (frozen)
# ----------------------------
def _dipole_form_factor(t_abs: np.ndarray, lam: float = 0.71) -> np.ndarray:
    x = 1.0 + (t_abs / float(lam))
    return 1.0 / (x * x)

def _coulomb_phase_west_yennie(t_abs: np.ndarray, B: float) -> np.ndarray:
    t = np.clip(t_abs, 1e-12, None)
    return np.log(np.clip(B * t / 2.0, 1e-30, None)) + EULER_GAMMA

def _amp_nuclear_mb(t_abs: np.ndarray, sigma_tot_mb: float, rho: float, B: float) -> np.ndarray:
    pref = float(sigma_tot_mb) / (4.0 * math.pi)
    return pref * (float(rho) + 1j) * np.exp(-0.5 * float(B) * t_abs)

def _amp_coulomb_mb(t_abs: np.ndarray, B_for_phase: float, sign_pp: int = -1, lam_ff: float = 0.71) -> np.ndarray:
    t = np.clip(t_abs, 1e-12, None)
    G = _dipole_form_factor(t, lam=lam_ff)
    phi = _coulomb_phase_west_yennie(t, B=float(B_for_phase))
    mag = (2.0 * ALPHA_EM * HBARC2_MB_GEV2) * (G * G) / t
    return float(sign_pp) * mag * np.exp(1j * (ALPHA_EM * phi))

def _dsdt_from_amp_mb(F: np.ndarray) -> np.ndarray:
    return (math.pi / HBARC2_MB_GEV2) * (np.abs(F) ** 2)

# ----------------------------
# GEO phase template
# ----------------------------
def _s_map_from_t(t_abs: np.ndarray, t_ref: float, mode: str) -> np.ndarray:
    tau = t_abs / max(float(t_ref), 1e-12)
    tau_max = float(np.max(tau)) if tau.size else 1.0
    if tau_max <= 0:
        tau_max = 1.0

    mode = (mode or "frac").lower()
    if mode == "log":
        s = np.log1p(tau) / np.log1p(tau_max)
    elif mode == "frac":
        s = tau / (tau + 1.0)
        s = s / max(float(np.max(s)), 1e-12)
    elif mode == "linear":
        s = tau / tau_max
    else:
        raise ValueError("Unknown s_map (use log, frac, linear)")

    return np.clip(s, 0.0, 1.0)

def _env_q_gauss(t_abs: np.ndarray, qmax: float) -> np.ndarray:
    q = np.sqrt(np.clip(t_abs, 0, None))
    qm = max(float(qmax), 1e-9)
    return np.exp(- (q / qm) ** 2)

def _phase_geo(
    t_abs: np.ndarray,
    A: float,
    delta_geo: float,
    template: str,
    s_map: str,
    t_ref: float,
    qmax: float,
) -> np.ndarray:
    s = _s_map_from_t(t_abs, float(t_ref), str(s_map))
    theta = 2.0 * math.pi * s - float(delta_geo)
    template = (template or "cos").lower()
    if template == "cos":
        base = np.cos(theta)
    elif template == "sin":
        base = np.sin(theta)
    else:
        raise ValueError("--template must be cos|sin")

    env = _env_q_gauss(t_abs, float(qmax))
    denom = np.max(np.abs(base)) + 1e-12
    base_u = base / denom
    return float(A) * env * base_u

# ----------------------------
# Chi2
# ----------------------------
def _chi2(y: np.ndarray, yhat: np.ndarray, cov: np.ndarray, rcond: float = 1e-12) -> float:
    r = (y - yhat).reshape(-1, 1)
    C = 0.5 * (cov + cov.T)
    eps = 1e-18 * max(1.0, float(np.mean(np.diag(C))))
    C[np.diag_indices_from(C)] += eps
    try:
        sol = np.linalg.solve(C, r)
    except np.linalg.LinAlgError:
        w, V = np.linalg.eigh(C)
        wmax = float(np.max(w)) if w.size else 1.0
        thr = float(rcond) * wmax
        winv = np.array([1.0/wi if wi > thr else 0.0 for wi in w], dtype=float)
        Cpinv = (V * winv) @ V.T
        sol = Cpinv @ r
    return float((r.T @ sol).squeeze())

def _eig_diag(C: np.ndarray, rcond: float) -> Dict:
    C = 0.5 * (C + C.T)
    w = np.linalg.eigvalsh(C)
    wmax = float(w[-1]) if w.size else 1.0
    thr = float(rcond) * wmax
    return {
        "eig_min": float(w[0]) if w.size else 0.0,
        "eig_med": float(np.median(w)) if w.size else 0.0,
        "eig_max": wmax,
        "neg_eigs": int((w < 0).sum()),
        "tiny_eigs": int((w < thr).sum()),
        "rank_eff": int((w >= thr).sum()),
        "cond_approx": float(wmax / max(float(w[0]), 1e-300)) if w.size else 0.0,
        "thr": thr,
    }

def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument("--pack", required=True, help="Path to elastic_pack.json built from HEPData archive")
    ap.add_argument("--cov", default="total", choices=["total", "stat", "sys"])
    ap.add_argument("--rcond", type=float, default=1e-12)

    ap.add_argument("--tmin", type=float, default=None)
    ap.add_argument("--tmax", type=float, default=None)

    # Frozen baseline (publication numbers; DO NOT FIT)
    ap.add_argument("--sigma_tot_mb", type=float, required=True)
    ap.add_argument("--rho", type=float, required=True)
    ap.add_argument("--B", type=float, required=True)

    ap.add_argument("--pp_sign", type=int, default=-1)
    ap.add_argument("--ff_lam", type=float, default=0.71)

    # Geometry (single-shot)
    ap.add_argument("--A", type=float, default=0.0)
    ap.add_argument("--A_I", type=float, default=None, help="(two-channel) Imag/bulk amplitude (unused here; accepted for symmetry).")
    ap.add_argument("--A_R", type=float, default=None, help="(two-channel) Real/interference amplitude. If set, overrides --A in CNI/rho interference tests.")
    ap.add_argument("--geo_mode", choices=["du_phase", "u_phase"], default="du_phase")
    ap.add_argument("--template", choices=["cos", "sin"], default="cos")
    ap.add_argument("--s_map", choices=["log", "frac", "linear"], default="frac")
    ap.add_argument("--t_ref_GeV2", type=float, default=0.01)
    ap.add_argument("--qmax_GeV", type=float, default=0.35)

    # CurvedCube args (consistency with Weak v6)
    ap.add_argument("--k_rt", type=int, default=180)
    ap.add_argument("--phi", type=float, default=1.57079632679)
    ap.add_argument("--zeta", type=float, default=0.05)

    # FRW environment (cosmic expansion) scaling (NOT a fit knob)
    ap.add_argument("--env_z", type=float, default=0.0, help="Environment redshift (lab today: 0.0).")
    ap.add_argument("--env_lookback_gyr", type=float, default=None, help="Alternative to env_z (provide only one).")
    ap.add_argument("--baseline_km", type=float, default=810.0)
    ap.add_argument("--L0_km", type=float, default=810.0)
    ap.add_argument("--Nin", type=int, default=8)
    ap.add_argument("--Nface", type=int, default=16)

    ap.add_argument("--out", default="out_cni_pred.csv")
    ap.add_argument("--chi2_out", default=None)

    args = ap.parse_args()

    # two-channel amplitude selection (real/interference panel)
    A_eff = float(args.A_R) if args.A_R is not None else float(args.A)

    env = _env_scale(z=float(args.env_z))

    pack_path = Path(args.pack)
    pack_dir = str(pack_path.parent)
    pack = _load_json(str(pack_path))

    dsdt_rel = pack.get("paths", {}).get("dsdt_csv", None)
    if not dsdt_rel:
        raise ValueError("pack.paths.dsdt_csv missing")

    dsdt_path = _join(pack_dir, dsdt_rel)
    df = pd.read_csv(dsdt_path)

    t_lo, t_ctr, t_hi = _infer_t_columns(df)
    if "dsdt_mb_per_GeV2" not in df.columns:
        raise ValueError("Missing required column: dsdt_mb_per_GeV2")

    t_abs_all = np.abs(df[t_ctr].to_numpy(float))
    y_all = df["dsdt_mb_per_GeV2"].to_numpy(float)

    tmin = float(np.nanmin(t_abs_all)) if args.tmin is None else float(args.tmin)
    tmax = float(np.nanmax(t_abs_all)) if args.tmax is None else float(args.tmax)

    m = (t_abs_all >= tmin) & (t_abs_all <= tmax) & np.isfinite(t_abs_all) & np.isfinite(y_all)
    idx = np.flatnonzero(m)
    if idx.size < 8:
        raise RuntimeError(f"Too few bins after cut: n={idx.size}. Check --tmin/--tmax.")

    dfw = df.iloc[idx].reset_index(drop=True)
    t_abs = np.abs(dfw[t_ctr].to_numpy(float))
    y = dfw["dsdt_mb_per_GeV2"].to_numpy(float)

    cov = _load_cov_from_table(dfw, args.cov)

    FN = _amp_nuclear_mb(t_abs, args.sigma_tot_mb, args.rho, args.B)
    FC = _amp_coulomb_mb(t_abs, B_for_phase=args.B, sign_pp=args.pp_sign, lam_ff=args.ff_lam)
    y_sm = _dsdt_from_amp_mb(FC + FN)

    if abs(float(A_eff)) < 1e-18:
        delta_geo, c1_abs = 0.0, 0.0
        phase = np.zeros_like(t_abs, dtype=float)
        y_geo = y_sm.copy()
        did_geo = False
    else:
        delta_geo, c1_abs = _curvedcube_delta_geo(
            k_rt=args.k_rt,
            phi=args.phi,
            zeta=args.zeta,
            geo_mode=args.geo_mode,
            baseline_km=args.baseline_km,
            L0_km=args.L0_km,
            Nin=args.Nin,
            Nface=args.Nface,
        )
        # Apply FRW env scaling: delta_geo -> delta_geo * (1/a). Lab (z=0) => ~no-op.
        if args.env_lookback_gyr is not None and abs(float(args.env_z)) > 0:
            raise ValueError("Provide only one: --env_z OR --env_lookback_gyr")
        if args.env_lookback_gyr is not None:
            delta_geo = _apply_env_to_delta_geo(delta_geo, lookback_gyr=float(args.env_lookback_gyr))
            env = _env_scale(lookback_gyr=float(args.env_lookback_gyr))
        else:
            delta_geo = _apply_env_to_delta_geo(delta_geo, z=float(args.env_z))
            env = _env_scale(z=float(args.env_z))
        phase = _phase_geo(
            t_abs=t_abs,
            A=A_eff,
            delta_geo=delta_geo,
            template=args.template,
            s_map=args.s_map,
            t_ref=args.t_ref_GeV2,
            qmax=args.qmax_GeV,
        )
        FN_geo = FN * np.exp(1j * phase)
        y_geo = _dsdt_from_amp_mb(FC + FN_geo)
        did_geo = True

    chi2_sm = _chi2(y, y_sm, cov, rcond=args.rcond)
    chi2_geo = _chi2(y, y_geo, cov, rcond=args.rcond)
    dchi2 = float(chi2_sm - chi2_geo)

    diag = np.clip(np.diag(cov), 1e-300, None)
    sig = np.sqrt(diag)
    pull_sm = (y - y_sm) / sig
    pull_geo = (y - y_geo) / sig

    out = pd.DataFrame({
        "t_abs_GeV2": t_abs,
        "y_obs": y,
        "y_SM": y_sm,
        "y_GEO": y_geo,
        "phase_geo_rad": phase,
        "pull_SM": pull_sm,
        "pull_GEO": pull_geo,
    })
    out.to_csv(str(args.out), index=False)

    ed = _eig_diag(cov, args.rcond)

    print("=== STRONG CNI/ρ NO-FIT (Coulomb + Nuclear) + GEO phase ===")
    print(f"pack         : {args.pack}")
    print(f"data_csv     : {dsdt_path}")
    print(f"cov          : {args.cov} (diag)   n={len(y)}")
    print(f"rcond        : {args.rcond}")
    print(f"t_window     : [{tmin}, {tmax}] GeV^2")
    print("")
    print("Frozen baseline (publication numbers; DO NOT FIT)")
    print(f"  sigma_tot_mb = {args.sigma_tot_mb}")
    print(f"  rho          = {args.rho}")
    print(f"  B            = {args.B}  GeV^-2")
    print("")
    print("Geometry (single-shot)")
    print(f"  A_eff(real)   = {A_eff}  rad   (A=0 => strict null; no CurvedCube call)")
    print(f"  geo_mode     = {args.geo_mode}")
    print(f"  template     = {args.template}")
    print(f"  s_map        = {args.s_map}  t_ref={args.t_ref_GeV2}  qmax={args.qmax_GeV}")
    print(f"  delta_geo    = {delta_geo:.6f} rad")
    print(f"  |c1| (diag)  = {c1_abs:.6f}")
    print(f"  did_geo      = {did_geo}")
    print("")
    print("Cov eig diagnostics")
    print(f"  eig min/med/max  = {ed['eig_min']:.3e}  {ed['eig_med']:.3e}  {ed['eig_max']:.3e}")
    print(f"  neg_eigs         = {ed['neg_eigs']}")
    print(f"  tiny_eigs        = {ed['tiny_eigs']}   (thr = rcond*max = {ed['thr']:.3e})")
    print(f"  rank_eff         = {ed['rank_eff']}")
    print(f"  cond_approx      = {ed['cond_approx']:.3e}")
    print("")
    print("Results")
    print(f"  chi2_SM      = {chi2_sm:.6f}")
    print(f"  chi2_GEO     = {chi2_geo:.6f}")
    print(f"  dchi2        = {dchi2:.6f}   (positive => GEO improves)")
    print(f"  out_csv      = {args.out}")

    if args.chi2_out:
        jj = {
            "chi2_SM": chi2_sm,
            "chi2_GEO": chi2_geo,
            "dchi2": dchi2,
            "delta_geo_rad": float(delta_geo),
            "c1_abs": float(c1_abs),
            "n_bins": int(len(y)),
            "tmin": float(tmin),
            "tmax": float(tmax),
            "cov": str(args.cov),
            "rcond": float(args.rcond),
            "sigma_tot_mb": float(args.sigma_tot_mb),
            "rho": float(args.rho),
            "B": float(args.B),
            "A_rad": float(A_eff),
            "A": float(args.A),
            "A_I": (None if args.A_I is None else float(args.A_I)),
            "A_R": (None if args.A_R is None else float(args.A_R)),
            "geo_mode": str(args.geo_mode),
            "template": str(args.template),
            "s_map": str(args.s_map),
            "t_ref_GeV2": float(args.t_ref_GeV2),
            "qmax_GeV": float(args.qmax_GeV),
            "k_rt": int(args.k_rt),
            "phi": float(args.phi),
            "zeta": float(args.zeta),
            "baseline_km": float(args.baseline_km),
            "L0_km": float(args.L0_km),
            "Nin": int(args.Nin),
            "Nface": int(args.Nface),
            "out_csv": str(args.out),
        }
        with open(str(args.chi2_out), "w", encoding="utf-8") as f:
            json.dump(jj, f, indent=2)
        print(f"  chi2_json    = {args.chi2_out}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
