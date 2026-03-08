#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
em_bhabha_forward_shapeonly_env_guarded_freezebetas_dropin.py

Bhabha (e+e- -> e+e-) forward harness:
- baseline: simple 2-shape proxy in cos(theta): beta1/(1-c)^2 + beta2/(1+c)^2
- GEO: multiplicative modulation: pred_geo = pred_sm * (1 + delta_i)

Features requested:
- --shape_only: remove overall normalization component of delta (mean delta) so we test shape only
- --require_positive: fail-fast if any (1+delta_i) <= 0
- --beta_nonneg: enforce beta >= 0 via bounded least-squares fit
- --freeze_betas: fit betas on SM once, reuse same betas for GEO (no refit)  [important for limit scans]
- env scaling:
    env_u0 sets lab reference (default 1e-8)
    env_u / v_kms / r_over_Rs define environment potential u; env_scale = env_u/env_u0

Optional (for publishable route later):
- --baseline_csv + --baseline_col: import an SM baseline curve per bin. If provided, fit only a single
  normalization beta_norm (>=0 if beta_nonneg) multiplying that curve; GEO then applies on top.

Outputs:
- prints summary and chi2
- writes per-bin table to --out

This is intentionally a "plumbing + constraint + limit-scan" harness, not a full radiatively-corrected Bhabha prediction.
"""

import argparse, json, math, os
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

C_LIGHT = 299_792_458.0  # m/s

def load_pack(pack_path: str):
    with open(pack_path, "r", encoding="utf-8") as f:
        pack = json.load(f)
    base = os.path.dirname(os.path.abspath(pack_path))
    paths = pack.get("paths", {})
    cols = pack.get("columns", {})
    def abspath(rel):
        return rel if os.path.isabs(rel) else os.path.join(base, rel)
    return pack, base, {k: abspath(v) for k, v in paths.items()}, cols


def _cov_key_for_choice(which: str) -> str:
    key_map = {
        "total": "cov_total_csv",
        "stat": "cov_stat_csv",
        "sys_corr": "cov_sys_csv",
        "diag_total": "cov_diag_total_csv",
    }
    if which not in key_map:
        raise ValueError(f"Unknown cov '{which}'")
    return key_map[which]

def load_cov(paths: dict, which: str) -> np.ndarray:
    p = paths[_cov_key_for_choice(which)]
    cov = pd.read_csv(p, header=None).values.astype(float)
    return cov

def inv_cov(cov: np.ndarray) -> np.ndarray:
    # robust inverse via Cholesky with jitter if needed
    cov = cov.copy()
    jitter = 0.0
    for _ in range(8):
        try:
            L = np.linalg.cholesky(cov)
            # inv(cov) = inv(L.T) @ inv(L)
            Linv = np.linalg.inv(L)
            return Linv.T @ Linv
        except np.linalg.LinAlgError:
            jitter = 1e-12 if jitter == 0.0 else jitter * 10.0
            cov += np.eye(cov.shape[0]) * jitter
    # fallback
    return np.linalg.pinv(cov)

def chi2(obs: np.ndarray, pred: np.ndarray, cov_inv: np.ndarray) -> float:
    r = obs - pred
    return float(r.T @ cov_inv @ r)

def gen_factor(name: str) -> float:
    name = (name or "").lower()
    if name == "lam1":
        return 0.5
    if name == "lam2":
        return 1.0
    if name == "lam3":
        return 1.5
    if name == "lam4":
        return 2.0
    # allow numeric
    try:
        return float(name)
    except Exception:
        return 1.0

def struct_factor(name: str) -> float:
    name = (name or "").lower()
    if name == "diag":
        return 1.0
    if name == "offdiag":
        return -1.0
    return 1.0

def omega0_from_geom(mode: str, L0_km: float) -> float:
    mode = (mode or "").lower()
    if mode == "fixed":
        return math.pi / max(L0_km, 1e-12)  # matches your prints: pi/810 ~ 0.0038785
    try:
        return float(mode)
    except Exception:
        return 0.0

def env_u_from_args(env_u: float|None, v_kms: float|None, r_over_Rs: float|None) -> float:
    if env_u is not None:
        return float(env_u)
    if v_kms is not None:
        v = float(v_kms) * 1_000.0
        return (v / C_LIGHT) ** 2
    if r_over_Rs is not None:
        r = float(r_over_Rs)
        return 0.5 / max(r, 1e-12)  # gives 0.05 at r=10
    # default "lab"
    return 1e-8

def build_delta(
    cos_ctr: np.ndarray,
    sqrt_s_GeV: float,
    A: float,
    alpha: float,
    phi: float,
    geo_structure: str,
    geo_gen: str,
    omega0_geom: str,
    L0_km: float,
    zeta: float,
    R_max: float,
    t_ref_GeV: float,
    env_scale: float,
    shape_only: bool,
) -> np.ndarray:
    s = (sqrt_s_GeV ** 2)
    # |t| proxy for Bhabha: |t| ~ s/2 * (1 - cosθ)
    t_abs = 0.5 * s * (1.0 - cos_ctr)  # GeV^2
    t_ref2 = max(t_ref_GeV, 1e-12) ** 2
    q = np.maximum(t_abs, t_ref2) / t_ref2  # dimensionless
    f = alpha * np.log(q)  # small in lab for small alpha
    g = gen_factor(geo_gen)
    st = struct_factor(geo_structure)
    omega0 = omega0_from_geom(omega0_geom, L0_km)
    # simple saturating mech response: R in [0, R_max]
    # dependence uses zeta and omega0 so parameters still "wired"
    # use x = zeta * (1 + omega0 * t_ref) * fscale
    x = zeta * (1.0 + omega0 * (t_ref_GeV + 1e-12)) * np.abs(f)
    R = R_max * (1.0 - np.exp(-x))
    delta = env_scale * A * st * g * R * math.sin(phi) * f

    if shape_only:
        # remove mean delta (weighted by 1) -> tests only shape
        delta = delta - float(np.mean(delta))
    return delta

def fit_betas_proxy(obs: np.ndarray, cos_ctr: np.ndarray, cov_inv: np.ndarray, nonneg: bool) -> np.ndarray:
    b1 = 1.0 / np.maximum(1.0 - cos_ctr, 1e-9) ** 2
    b2 = 1.0 / np.maximum(1.0 + cos_ctr, 1e-9) ** 2
    X = np.vstack([b1, b2]).T  # N x 2

    # whiten using cov_inv: minimize (obs - Xb)^T C^-1 (obs - Xb)
    # Use Cholesky of cov_inv if PD; else SVD whitening.
    try:
        L = np.linalg.cholesky(cov_inv)
        # For cov_inv = L L^T (numpy returns lower-triangular), the correct whitening is L^T
        LT = L.T
        Xw = LT @ X
        yw = LT @ obs
    except np.linalg.LinAlgError:
        U, s, _ = np.linalg.svd(cov_inv)
        W = (U * np.sqrt(np.maximum(s, 0.0)))  # cov_inv^{1/2}
        Xw = W.T @ X
        yw = W.T @ obs

    if nonneg:
        res = lsq_linear(Xw, yw, bounds=(0.0, np.inf), lsmr_tol="auto", verbose=0)
        beta = res.x
    else:
        beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    return beta.astype(float)

def fit_beta_norm_import(obs: np.ndarray, base_curve: np.ndarray, cov_inv: np.ndarray, nonneg: bool) -> float:
    X = base_curve.reshape(-1, 1)
    try:
        L = np.linalg.cholesky(cov_inv)
        # For cov_inv = L L^T (numpy returns lower-triangular), the correct whitening is L^T
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
        return float(res.x[0])
    else:
        b, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
        return float(b[0])


def infer_group_ids_from_repeated_bins(df: pd.DataFrame, xlo_col: str, xhi_col: str, mode: str = "auto"):
    """Infer group_id for tables that repeat the same angular bins in multiple blocks.

    Returns: (group_id array, n_groups, n_unique, method)
    method in {"data", "block", "occ"}.
    """
    # If data already provides group_id, trust it.
    if "group_id" in df.columns:
        g = df["group_id"].astype(int).to_numpy()
        return g, int(g.max()) + 1, int(df[[xlo_col, xhi_col]].drop_duplicates().shape[0]), "data"

    keys = [(round(float(a), 8), round(float(b), 8)) for a, b in zip(df[xlo_col].to_numpy(float), df[xhi_col].to_numpy(float))]
    N = len(keys)

    # helper: check periodic repetition with period P
    def _is_period(P: int) -> bool:
        if P <= 0 or N % P != 0:
            return False
        base = keys[:P]
        for g in range(N // P):
            if keys[g*P:(g+1)*P] != base:
                return False
        return True

    # Try block-mode (contiguous repeats) first (good for LEP table18: 60 = 15×4).
    if mode in ("auto", "block"):
        first = keys[0]
        candidates = [i for i, k in enumerate(keys) if (i > 0 and k == first)]
        P = None
        for cand in candidates:
            if _is_period(cand):
                P = cand
                break
        if P is None:
            # fallback: try n_unique as a period
            n_unique = len(set(keys))
            if _is_period(n_unique):
                P = n_unique
        if P is not None:
            g = np.array([i // P for i in range(N)], dtype=int)
            return g, int(N // P), int(P), "block"

        if mode == "block":
            raise SystemExit("group_mode=block selected, but could not infer repeated contiguous blocks from data.")

    # Fallback: occurrence counting per (xlo,xhi) key (works if rows are interleaved).
    if mode in ("auto", "occ"):
        counter = {}
        g = []
        for k in keys:
            occ = counter.get(k, 0)
            g.append(occ)
            counter[k] = occ + 1
        g = np.array(g, dtype=int)
        return g, int(g.max()) + 1, int(df[[xlo_col, xhi_col]].drop_duplicates().shape[0]), "occ"

    raise SystemExit(f"Unknown group_mode: {mode}")

def _detect_baseline_group_col(bdf: pd.DataFrame, override: str | None):
    if override:
        if override not in bdf.columns:
            raise SystemExit(f"baseline_group_col '{override}' not found in baseline_csv columns: {list(bdf.columns)}")
        return override
    for cand in ["group_id", "group", "block", "dataset_id"]:
        if cand in bdf.columns:
            return cand
    return None

def _detect_bin_cols(df: pd.DataFrame, prefer_lo: str, prefer_hi: str):
    """Pick bin edge columns. Prefer pack-provided names; fall back to common aliases."""
    lo_cands = [prefer_lo, "cos_lo", "x_lo", "bin_lo"]
    hi_cands = [prefer_hi, "cos_hi", "x_hi", "bin_hi"]
    lo = next((c for c in lo_cands if c and c in df.columns), None)
    hi = next((c for c in hi_cands if c and c in df.columns), None)
    if lo is None or hi is None:
        raise SystemExit(f"Could not find bin edge columns in CSV. Tried lo={lo_cands}, hi={hi_cands}. Columns: {list(df.columns)}")
    return lo, hi

def build_import_base_curve(
    df_data: pd.DataFrame,
    bdf: pd.DataFrame,
    baseline_col: str,
    group_ids: np.ndarray,
    n_groups: int,
    xlo_data: str,
    xhi_data: str,
    baseline_group_col: str | None,
    xlo_base: str,
    xhi_base: str,
):
    """Return per-row base_curve aligned to df_data rows.

    Supports:
      A) baseline without group_id: one prediction per (xlo,xhi), shared across all groups
      B) baseline with group_id: prediction per (group_id, xlo, xhi)
    """
    if baseline_col not in bdf.columns:
        raise SystemExit(f"baseline_col '{baseline_col}' not found in baseline_csv columns: {list(bdf.columns)}")

    # build lookup maps
    def _k(a, b):
        return (round(float(a), 8), round(float(b), 8))

    if baseline_group_col is None:
        bmap = {}
        for a, b, v in zip(bdf[xlo_base].to_numpy(float), bdf[xhi_base].to_numpy(float), bdf[baseline_col].to_numpy(float)):
            kk = _k(a, b)
            if kk in bmap:
                # if duplicates exist, average
                bmap[kk] = 0.5 * (bmap[kk] + float(v))
            else:
                bmap[kk] = float(v)

        keys = [_k(a, b) for a, b in zip(df_data[xlo_data].to_numpy(float), df_data[xhi_data].to_numpy(float))]
        missing = [kk for kk in set(keys) if kk not in bmap]
        if missing:
            raise SystemExit(f"baseline_csv does not cover all data bins (missing up to 5): {missing[:5]}")
        return np.array([bmap[kk] for kk in keys], dtype=float), False

    # grouped baseline
    try:
        bg = bdf[baseline_group_col].astype(int).to_numpy(int)
    except Exception:
        # allow string labels, map to ints by sorted unique
        labels = bdf[baseline_group_col].astype(str).to_list()
        uniq = sorted(set(labels))
        m = {lab: i for i, lab in enumerate(uniq)}
        bg = np.array([m[lab] for lab in labels], dtype=int)

    bmap = {}
    for gid, a, b, v in zip(bg, bdf[xlo_base].to_numpy(float), bdf[xhi_base].to_numpy(float), bdf[baseline_col].to_numpy(float)):
        kk = (int(gid),) + _k(a, b)
        bmap[kk] = float(v)

    keys = [(int(g),) + _k(a, b) for g, a, b in zip(group_ids, df_data[xlo_data].to_numpy(float), df_data[xhi_data].to_numpy(float))]
    missing = [kk for kk in set(keys) if kk not in bmap]
    if missing:
        raise SystemExit(
            "baseline_csv does not cover all (group_id, bin) pairs required by data. "
            f"Missing (showing up to 5): {missing[:5]}"
        )

    # sanity: ensure baseline covers all groups 0..n_groups-1
    present_groups = set(int(k[0]) for k in bmap.keys())
    needed_groups = set(range(n_groups))
    if not needed_groups.issubset(present_groups):
        raise SystemExit(f"baseline_csv group coverage mismatch. Need groups {sorted(needed_groups)} but baseline has {sorted(present_groups)}")

    return np.array([bmap[kk] for kk in keys], dtype=float), True

def fit_betas_import_groups(obs: np.ndarray, base_curve: np.ndarray, group_ids: np.ndarray, n_groups: int, cov_inv: np.ndarray, nonneg: bool) -> np.ndarray:
    """Fit one normalization beta per group, using full covariance."""
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True)
    ap.add_argument("--cov", default="total", choices=["total","stat","sys_corr","diag_total"])
    ap.add_argument("--sqrt_s_GeV", type=float, default=189.0, help="Used only for |t| proxy from cos(theta).")
    ap.add_argument("--A", type=float, default=0.0)
    ap.add_argument(
        "--alpha",
        type=float,
        default=7.5e-05,
        help="DEPRECATED (EM only): use --em_alpha_tshape. Kept for backward compatibility.",
    )
    ap.add_argument(
        "--em_alpha_tshape",
        type=float,
        default=None,
        help="EM |t|-shape exponent for f(|t|) = (|t|/t_ref)**em_alpha_tshape; overrides --alpha if provided.",
    )
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
    # env controls
    ap.add_argument("--env_u0", type=float, default=1e-8)
    ap.add_argument("--env_u", type=float, default=None)
    ap.add_argument("--v_kms", type=float, default=None)
    ap.add_argument("--r_over_Rs", type=float, default=None)
    # optional baseline import
    ap.add_argument("--baseline_csv", default=None, help="Optional: CSV with baseline prediction per bin.")
    ap.add_argument("--baseline_col", default="pred_sm", help="Column name in baseline_csv.")
    ap.add_argument("--baseline_group_col", default=None, help="Optional: group id column in baseline_csv (e.g. group_id). If omitted, auto-detect.")
    ap.add_argument("--group_mode", default="auto", choices=["auto","block","occ"], help="How to infer group_id from repeated bins when data has no group_id column.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out_json", default=None, help="Optional: write a JSON summary/telemetry artifact (paper-facing IO closure, not accuracy).")
    args = ap.parse_args()

    em_alpha_tshape = float(args.alpha) if args.em_alpha_tshape is None else float(args.em_alpha_tshape)

    pack, base, paths, cols = load_pack(args.pack)
    df = pd.read_csv(paths["data_csv"])

    cos_ctr = df[cols["x_ctr"]].to_numpy(float)
    obs = df[cols["y"]].to_numpy(float)

    cov = load_cov(paths, args.cov)
    cov_inv = inv_cov(cov)

    # env scale
    env_u = env_u_from_args(args.env_u, args.v_kms, args.r_over_Rs)
    env_scale = env_u / max(args.env_u0, 1e-30)

    # baseline prediction (SM proxy or imported)
    imported = False
    group_ids = np.zeros_like(obs, dtype=int)
    n_groups = 1
    group_method = "none"
    base_curve = None
    baseline_grouped = False

    if args.baseline_csv:
        bdf = pd.read_csv(args.baseline_csv)

        # Infer group structure from repeated angular bins (data often has 60 rows = 15 bins × 4 blocks).
        xlo_data = cols["x_lo"]
        xhi_data = cols["x_hi"]
        group_ids, n_groups, n_unique, group_method = infer_group_ids_from_repeated_bins(
            df, xlo_data, xhi_data, mode=args.group_mode
        )

        # Detect bin columns in baseline CSV and (optionally) its group column.
        xlo_base, xhi_base = _detect_bin_cols(bdf, xlo_data, xhi_data)
        baseline_group_col = _detect_baseline_group_col(bdf, args.baseline_group_col)

        base_curve, baseline_grouped = build_import_base_curve(
            df_data=df,
            bdf=bdf,
            baseline_col=args.baseline_col,
            group_ids=group_ids,
            n_groups=n_groups,
            xlo_data=xlo_data,
            xhi_data=xhi_data,
            baseline_group_col=baseline_group_col,
            xlo_base=xlo_base,
            xhi_base=xhi_base,
        )

        # Fit one normalization beta per group (with full covariance).
        betas_sm = fit_betas_import_groups(obs, base_curve, group_ids, n_groups, cov_inv, args.beta_nonneg)
        pred_sm = np.zeros_like(obs, dtype=float)
        for g in range(n_groups):
            m = (group_ids == g)
            pred_sm[m] = betas_sm[g] * base_curve[m]

        imported = True
    else:
        # Simple proxy basis for quick plumbing checks
        betas_sm = fit_betas_proxy(obs, cos_ctr, cov_inv, args.beta_nonneg)
        b1 = 1.0 / np.maximum(1.0 - cos_ctr, 1e-9) ** 2
        b2 = 1.0 / np.maximum(1.0 + cos_ctr, 1e-9) ** 2
        pred_sm = betas_sm[0] * b1 + betas_sm[1] * b2
    chi2_sm = chi2(obs, pred_sm, cov_inv)

    # GEO modulation
    delta = build_delta(
        cos_ctr=cos_ctr,
        sqrt_s_GeV=args.sqrt_s_GeV,
        A=args.A,
        alpha=em_alpha_tshape,
        phi=args.phi,
        geo_structure=args.geo_structure,
        geo_gen=args.geo_gen,
        omega0_geom=args.omega0_geom,
        L0_km=args.L0_km,
        zeta=args.zeta,
        R_max=args.R_max,
        t_ref_GeV=args.t_ref_GeV,
        env_scale=env_scale,
        shape_only=args.shape_only,
    )

    if args.require_positive:
        if np.any(1.0 + delta <= 0.0):
            print("FAIL: require_positive triggered (some 1+delta <= 0).")
            raise SystemExit(2)

    pred_geo_0 = pred_sm * (1.0 + delta)

    if args.freeze_betas:
        pred_geo = pred_geo_0
        betas_geo = betas_sm.copy()
    else:
        # refit nuisance betas under GEO (only if not using imported baseline)
        
        if imported:
            # refit one normalization per group on the modulated curve
            base_curve_geo = base_curve * (1.0 + delta)
            betas_geo = fit_betas_import_groups(obs, base_curve_geo, group_ids, n_groups, cov_inv, args.beta_nonneg)
            pred_geo = np.zeros_like(obs, dtype=float)
            for g in range(n_groups):
                m = (group_ids == g)
                pred_geo[m] = betas_geo[g] * base_curve_geo[m]
        else:
            # refit beta1, beta2 on the modulated basis
            b1 = 1.0 / np.maximum(1.0 - cos_ctr, 1e-9) ** 2
            b2 = 1.0 / np.maximum(1.0 + cos_ctr, 1e-9) ** 2
            X = np.vstack([b1*(1.0+delta), b2*(1.0+delta)]).T
            # whiten
            try:
                L = np.linalg.cholesky(cov_inv)
                # For cov_inv = L L^T (numpy returns lower-triangular), the correct whitening is L^T
                LT = L.T
                Xw = LT @ X
                yw = LT @ obs
            except np.linalg.LinAlgError:
                U, s, _ = np.linalg.svd(cov_inv)
                W = (U * np.sqrt(np.maximum(s, 0.0)))
                Xw = W.T @ X
                yw = W.T @ obs
            if args.beta_nonneg:
                res = lsq_linear(Xw, yw, bounds=(0.0, np.inf), lsmr_tol="auto", verbose=0)
                betas_geo = res.x.astype(float)
            else:
                betas_geo, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
                betas_geo = betas_geo.astype(float)
            pred_geo = X @ betas_geo

    chi2_geo = chi2(obs, pred_geo, cov_inv)

    delta_chi2 = chi2_sm - chi2_geo
    k_extra = 2  # for A, alpha by default in these harnesses
    dAIC = delta_chi2 - 2*k_extra
    dBIC = delta_chi2 - k_extra*math.log(len(obs))

    # ASCII-only prints (avoid Windows cp1252 issues when piped)
    print("========================")
    print("REAL-DATA EM (Bhabha) FORWARD SUMMARY")
    print("========================")
    print(f"pack      : {args.pack}")
    print(f"data_csv  : {paths['data_csv']}")
    print(f"cov       : {args.cov}")
    print(f"bins      : {len(obs)}")
    
    if imported:
        print("baseline  : imported SM curve (per-bin), fitted per-group normalization")
        print(f"grouping  : n_groups={n_groups} method={group_method} baseline_has_group={baseline_grouped}")
        betas_str = ", ".join([f"g{g}={betas_sm[g]:.8g}" for g in range(n_groups)])
        print(f"SM fit    : betas[{n_groups}] = {betas_str}  chi2_SM={chi2_sm:.6f}")
    else:
        print("baseline  : proxy beta1/(1-c)^2 + beta2/(1+c)^2")
        print(f"SM fit    : beta1={betas_sm[0]:.8g}  beta2={betas_sm[1]:.8g}  chi2_SM={chi2_sm:.6f}")
    omega0 = omega0_from_geom(args.omega0_geom, args.L0_km)
    print(f"mech      : omega0={omega0:.10g} (1/km) omega0_geom={args.omega0_geom} L0_km={args.L0_km} zeta={args.zeta} R_max={args.R_max} t_ref_GeV={args.t_ref_GeV}")
    print(f"env       : env_u={env_u:.6g} env_u0={args.env_u0:.6g} env_scale={env_scale:.6g}")
    print(f"geo       : A={args.A} em_alpha_tshape={em_alpha_tshape} phi={args.phi} structure={args.geo_structure} gen={args.geo_gen} shape_only={args.shape_only} freeze_betas={args.freeze_betas}")
    
    if imported:
        betas_str = ", ".join([f"g{g}={betas_geo[g]:.8g}" for g in range(n_groups)])
        print(f"GEO fit   : betas[{n_groups}] = {betas_str}  chi2_GEO={chi2_geo:.6f}")
    else:
        print(f"GEO fit   : beta1={betas_geo[0]:.8g}  beta2={betas_geo[1]:.8g}  chi2_GEO={chi2_geo:.6f}")

    print("\n------------------------")
    print(f"TOTAL chi2_SM  = {chi2_sm:.6f}")
    print(f"TOTAL chi2_GEO = {chi2_geo:.6f}")
    print(f"Delta chi2 = chi2_SM - chi2_GEO = {delta_chi2:.6f}")
    print("------------------------")
    print(f"Delta AIC (k_extra={k_extra}): dAIC = {dAIC:.6f}")
    print(f"Delta BIC (k_extra={k_extra}): dBIC = {dBIC:.6f}")

    out_df = pd.DataFrame({
        "cos_lo": df[cols["x_lo"]],
        "cos_ctr": df[cols["x_ctr"]],
        "cos_hi": df[cols["x_hi"]],
        "group_id": group_ids,
        "obs_pb": obs,
        "pred_sm": pred_sm,
        "pred_geo": pred_geo,
        "delta": delta,
        "ratio_geo_sm": np.where(pred_sm != 0, pred_geo/pred_sm, np.nan),
    })
    out_df.to_csv(args.out, index=False)
    print(f"\nSaved: {args.out}")

    if args.out_json:
        out_json = Path(args.out_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)

        cov_key = _cov_key_for_choice(args.cov)
        io = {
            "data_csv": str(Path(paths["data_csv"]).resolve()),
            "cov_choice": str(args.cov),
            "cov_csv": str(Path(paths[cov_key]).resolve()) if cov_key in paths else None,
            "data_loaded_from_paths": True,
        }
        if args.baseline_csv:
            io["baseline_csv"] = str(Path(args.baseline_csv).resolve())

        summary = {
            "pack": {"path": str(Path(args.pack).resolve()), "meta": pack.get("meta", {})},
            "io": io,
            "telemetry": {
                "baseline_import_used": bool(imported),
                "baseline_import_grouped": bool(baseline_grouped),
                "group_method": str(group_method),
                "n_groups": int(n_groups),
            },
            "params": {
                "sqrt_s_GeV": float(args.sqrt_s_GeV),
                "A": float(args.A),
                "alpha": float(em_alpha_tshape),
                "em_alpha_tshape": float(em_alpha_tshape),
                "phi": float(args.phi),
                "geo_structure": str(args.geo_structure),
                "geo_gen": str(args.geo_gen),
                "omega0_geom": str(args.omega0_geom),
                "L0_km": float(args.L0_km),
                "zeta": float(args.zeta),
                "R_max": float(args.R_max),
                "t_ref_GeV": float(args.t_ref_GeV),
                "shape_only": bool(args.shape_only),
                "freeze_betas": bool(args.freeze_betas),
                "beta_nonneg": bool(args.beta_nonneg),
                "require_positive": bool(args.require_positive),
                "env_u0": float(args.env_u0),
                "env_u": None if args.env_u is None else float(args.env_u),
                "v_kms": None if args.v_kms is None else float(args.v_kms),
                "r_over_Rs": None if args.r_over_Rs is None else float(args.r_over_Rs),
            },
            "chi2": {
                "sm": float(chi2_sm),
                "geo": float(chi2_geo),
                "delta": float(delta_chi2),
                "ndof": int(len(obs)),
            },
            "integrity": {
                "no_nan_inf": bool(np.all(np.isfinite(out_df[["obs_pb", "pred_sm", "pred_geo", "delta"]].to_numpy(dtype=float)))),
                "require_positive_ok": bool(np.all(1.0 + delta > 0.0)) if args.require_positive else True,
            },
            "framing": {
                "stability_not_accuracy": True,
                "note": "EM paper-run telemetry (IO closure + schema stability) for the declared proxy model; not a physical-accuracy claim.",
            },
        }

        out_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

if __name__ == "__main__":
    main()
