#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strong_sigma_tot_energy_scan_v1.py

Purpose
-------
A NO-FIT / NO-SCAN diagnostic runner for pp and pbarp total cross section
sigma_tot(sqrt(s)) using a frozen PDG/COMPETE-style baseline and a preregistered
CurvedCube "geometry phase" modulation.

This is *not* a full strong-sector theory of pp scattering. It's a deliberately
minimal bridge aimed at the "film vs photo" test idea:
  - many energy points (accumulation along energy axis)
  - zero fitting of baseline coefficients
  - fixed geometry knobs (k_rt, phi, zeta) summarized into a fixed delta_geo_ref

Baseline (PDG form; parameters frozen)
--------------------------------------
sigma_tot^{pp/pbarp}(s) = P + H ln^2(s/sM) + R1 (s/sM)^(-eta1) +/- R2 (s/sM)^(-eta2)

with (P,H,R1,eta1,R2,eta2,sM) taken from a PDG parameterization as quoted in
literature (see citations in your notes).

Geometry modulation (minimal)
-----------------------------
We apply a tiny multiplicative correction to the baseline:
  sigma_geo = sigma_sm * (1 + A * |c1| * template(delta_geo(E)))

Where:
  - A is the preregistered phase amplitude (rad), e.g. 1e-3
  - |c1| is the diag-projection factor from your CurvedCube runner (fixed)
  - template is cos or sin
  - delta_geo(E) = delta_geo_ref * env_scale(E)

env_scale(E) choices are provided because strong lacks a natural path-integral
accumulation. You MUST treat each env_mode as a separate preregistered hypothesis.

  env_mode=none      : env_scale = 1
  env_mode=debroglie : env_scale = sqrt(s)/sqrt(s)_ref  (more cells probed as momentum increases)
  env_mode=log       : env_scale = ln(s/s_ref)
  env_mode=radius    : env_scale = sqrt(sigma_SM(s)/sigma_SM(s_ref))

No fitting is performed; chi2 is diagonal using provided uncertainties.

Input CSV
---------
Expected columns (flexible):
  - sqrts_GeV (or sqrt_s_GeV, sqrts)
  - sigma_mb (or sigma_tot_mb, sigma_tot)
  - err_mb (or sigma_err_mb, sigma_tot_err)
  - channel (optional): 'pp' or 'pbarp' (if missing, assumed pp)

Output
------
Writes a CSV with predictions and a JSON summary containing chi2 and dchi2.

Usage example (pp only, env_mode=none):
  py -3 .\strong_sigma_tot_energy_scan_v1.py --data .\data\hepdata\pdg_sigma_tot_clean.csv --channel pp --A 0 --out out_sig_pp_NULL.csv --chi2_out out_sig_pp_NULL_chi2.json
  py -3 .\strong_sigma_tot_energy_scan_v1.py --data .\data\hepdata\pdg_sigma_tot_clean.csv --channel pp --A 1e-3 --out out_sig_pp_GEO.csv --chi2_out out_sig_pp_GEO_chi2.json

"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Literal, Tuple

import numpy as np
import pandas as pd


# ----------------------------
# Frozen PDG/COMPETE baseline
# ----------------------------

@dataclass(frozen=True)
class PDGParams:
    P_mb: float = 33.73
    H_mb: float = 0.2838
    R1_mb: float = 13.67
    eta1: float = 0.412
    R2_mb: float = 7.77
    eta2: float = 0.5626
    mN_GeV: float = 0.938  # nucleon mass
    M_GeV: float = 2.076   # PDG scale parameter

    @property
    def sM_GeV2(self) -> float:
        return (2.0 * self.mN_GeV + self.M_GeV) ** 2


def sigma_tot_pdg_mb(sqrts_GeV: np.ndarray, channel: Literal["pp", "pbarp"], pars: PDGParams) -> np.ndarray:
    """PDG/COMPETE-style frozen baseline for sigma_tot in mb."""
    s = np.asarray(sqrts_GeV, dtype=float) ** 2
    sM = pars.sM_GeV2
    x = s / sM
    # guard against tiny/invalid
    x = np.maximum(x, 1e-30)

    logx = np.log(x)
    base = pars.P_mb + pars.H_mb * (logx ** 2) + pars.R1_mb * (x ** (-pars.eta1))
    odd = pars.R2_mb * (x ** (-pars.eta2))
    if channel == "pp":
        return base - odd
    return base + odd


# ----------------------------
# Geometry modulation (minimal)
# ----------------------------

def env_scale(sqrts_GeV: np.ndarray, mode: Literal["none", "debroglie", "log"], sqrts_ref_GeV: float) -> np.ndarray:
    x = np.asarray(sqrts_GeV, dtype=float)
    if mode == "none":
        return np.ones_like(x)
    if mode == "debroglie":
        return x / float(sqrts_ref_GeV)
    # mode == "log"
    # use log(s/s_ref) with s = sqrts^2 => log(s/s_ref) = 2 log(sqrts/sqrts_ref)
    return 2.0 * np.log(np.maximum(x, 1e-30) / float(sqrts_ref_GeV))


def env_scale_radius_from_sigma(sigma_sm_mb: np.ndarray, sigma_sm_ref_mb: float) -> np.ndarray:
    """
    Interaction-radius bridge (param-free):
      sigma_tot ~ pi R^2  =>  R ~ sqrt(sigma_tot)
      scale(s) = R(s)/R(s_ref) = sqrt( sigma_sm(s) / sigma_sm(s_ref) )
    """
    ref = max(float(sigma_sm_ref_mb), 1e-30)
    return np.sqrt(np.maximum(np.asarray(sigma_sm_mb, dtype=float), 1e-30) / ref)


def sigma_geo_mb(
    sigma_sm: np.ndarray,
    sqrts_GeV: np.ndarray,
    A_rad: float,
    delta_geo_ref_rad: float,
    c1_abs: float,
    template: Literal["cos", "sin"],
    env_mode: Literal["none", "debroglie", "log", "radius", "eikonal"],
    sqrts_ref_GeV: float,
    scale_override: np.ndarray | None = None,
) -> np.ndarray:
    if A_rad == 0.0:
        return sigma_sm.copy()

    if scale_override is None:
        # radius scale must be computed upstream from the SM baseline
        scale = env_scale(sqrts_GeV, "none" if env_mode == "radius" else env_mode, sqrts_ref_GeV)
    else:
        scale = np.asarray(scale_override, dtype=float)
    phase = delta_geo_ref_rad * scale
    if template == "cos":
        t = np.cos(phase)
    else:
        t = np.sin(phase)

    # tiny multiplicative correction; keep sign control in A
    return sigma_sm * (1.0 + A_rad * c1_abs * t)


# ----------------------------
# IO helpers
# ----------------------------

def _pick_col(df: pd.DataFrame, candidates: Tuple[str, ...]) -> str:
    cols = {c.lower(): c for c in df.columns}
    for k in candidates:
        if k.lower() in cols:
            return cols[k.lower()]
    raise KeyError(f"Could not find any of columns {candidates} in: {list(df.columns)}")


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # normalize column names gently
    sqrts_col = _pick_col(df, ("sqrts_GeV", "sqrt_s_GeV", "sqrts", "sqrt_s", "sqrtS_GeV"))
    sig_col   = _pick_col(df, ("sigma_mb", "sigma_tot_mb", "sigma_tot", "sigma"))
    err_col   = _pick_col(df, ("err_mb", "sigma_err_mb", "sigma_tot_err", "err", "sigma_err"))

    out = pd.DataFrame({
        "sqrts_GeV": pd.to_numeric(df[sqrts_col], errors="coerce"),
        "sigma_mb": pd.to_numeric(df[sig_col], errors="coerce"),
        "err_mb": pd.to_numeric(df[err_col], errors="coerce"),
    })
    if "channel" in [c.lower() for c in df.columns]:
        # keep original
        ch_col = [c for c in df.columns if c.lower() == "channel"][0]
        out["channel"] = df[ch_col].astype(str).str.strip().str.lower()
    else:
        out["channel"] = "pp"

    out = out.dropna().reset_index(drop=True)
    # basic sanity
    out = out[(out.err_mb > 0) & (out.sqrts_GeV > 0)].reset_index(drop=True)
    return out


def chi2_diag(y: np.ndarray, yhat: np.ndarray, err: np.ndarray) -> float:
    r = (y - yhat) / err
    return float(np.sum(r * r))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Input CSV (e.g., pdg_sigma_tot_clean.csv)")
    ap.add_argument("--channel", choices=["pp", "pbarp", "both", "all"], default="pp", help="Which channel(s) to evaluate")
    ap.add_argument("--smin_GeV", type=float, default=7.0, help="Min sqrt(s) [GeV] to include (PDG fit region starts ~7 GeV)")
    ap.add_argument("--smax_GeV", type=float, default=1.0e5, help="Max sqrt(s) [GeV] to include")
    ap.add_argument("--A", type=float, default=0.0, help="Geometry amplitude A [rad]; A=0 => strict null")
    ap.add_argument("--template", choices=["cos", "sin"], default="cos")
    ap.add_argument("--env_mode", choices=["none", "debroglie", "log", "radius", "eikonal"], default="none")
    ap.add_argument("--sqrts_ref_GeV", type=float, default=13000.0, help="Reference sqrt(s) for env scaling")
    ap.add_argument("--delta_geo_ref", type=float, default=-1.315523, help="Preregistered delta_geo at reference knobs (rad)")
    ap.add_argument("--c1_abs", type=float, default=0.725147, help="Preregistered |c1| projection factor")
    g_out = ap.add_mutually_exclusive_group(required=True)
    g_out.add_argument("--out", help="Output CSV path")
    g_out.add_argument("--out_csv", dest="out", help="Alias for --out (back-compat)")
    ap.add_argument("--chi2_out", required=True, help="Output JSON summary path")
    args = ap.parse_args()
    if args.channel == "all":
        args.channel = "both"

    df = load_data(args.data)
    df = df[(df.sqrts_GeV >= args.smin_GeV) & (df.sqrts_GeV <= args.smax_GeV)].reset_index(drop=True)

    pars = PDGParams()

    def run_one(ch: str) -> dict:
        d = df[df.channel == ch].copy()
        if len(d) == 0:
            return {"channel": ch, "n": 0}

        sq = d.sqrts_GeV.to_numpy()
        y = d.sigma_mb.to_numpy()
        e = d.err_mb.to_numpy()

        sm = sigma_tot_pdg_mb(sq, ch, pars)

        # --- physically-motivated energy scale (param-free bridge) ---
        if args.env_mode == "radius":
            sm_ref = float(sigma_tot_pdg_mb(np.array([args.sqrts_ref_GeV], dtype=float), ch, pars)[0])
            scale = env_scale_radius_from_sigma(sm, sm_ref)
        elif args.env_mode == "eikonal":
            # Param-free multi-exchange proxy (uses baseline's COMPETE scale sM):
            # scale(s) = ln(s/sM) / ln(s_ref/sM)
            s = np.asarray(sq, dtype=float) ** 2
            s_ref = float(args.sqrts_ref_GeV) ** 2
            sM = float(pars.sM_GeV2)
            logx = np.log(np.maximum(s / sM, 1e-30))
            logx_ref = float(np.log(max(s_ref / sM, 1e-30)))
            if abs(logx_ref) < 1e-12:
                scale = np.ones_like(logx)
            else:
                scale = logx / logx_ref
        else:
            scale = env_scale(sq, args.env_mode, args.sqrts_ref_GeV)

        geo = sigma_geo_mb(
            sm, sq,
            A_rad=args.A,
            delta_geo_ref_rad=args.delta_geo_ref,
            c1_abs=args.c1_abs,
            template=args.template,
            env_mode=args.env_mode,
            sqrts_ref_GeV=args.sqrts_ref_GeV,
            scale_override=scale,
        )

        chi_sm = chi2_diag(y, sm, e)
        chi_geo = chi2_diag(y, geo, e)

        outd = d.copy()
        outd["sigma_sm_mb"] = sm
        outd["sigma_geo_mb"] = geo
        outd["resid_sm"] = (y - sm) / e
        outd["resid_geo"] = (y - geo) / e
        outd["env_scale"] = scale if args.A != 0 else 0.0

        return {
            "channel": ch,
            "n": int(len(d)),
            "chi2_SM": float(chi_sm),
            "chi2_GEO": float(chi_geo),
            "dchi2": float(chi_sm - chi_geo),
            "out_df": outd,
        }

    results = []
    if args.channel in ("pp", "both"):
        results.append(run_one("pp"))
    if args.channel in ("pbarp", "both"):
        results.append(run_one("pbarp"))

    # concat outputs
    frames = [r["out_df"] for r in results if "out_df" in r]
    out_df = pd.concat(frames, axis=0, ignore_index=True) if frames else pd.DataFrame()
    out_df.to_csv(args.out, index=False)

    # summary JSON
    summary = {
        "data": args.data,
        "s_window_GeV": [args.smin_GeV, args.smax_GeV],
        "channel": args.channel,
        "baseline": {
            "form": "PDG/COMPETE: P + H ln^2(s/sM) + R1 (s/sM)^(-eta1) +/- R2 (s/sM)^(-eta2)",
            "P_mb": pars.P_mb, "H_mb": pars.H_mb, "R1_mb": pars.R1_mb, "eta1": pars.eta1,
            "R2_mb": pars.R2_mb, "eta2": pars.eta2, "sM_GeV2": pars.sM_GeV2,
        },
        "geometry": {
            "A_rad": args.A,
            "template": args.template,
            "env_mode": args.env_mode,
            "sqrts_ref_GeV": args.sqrts_ref_GeV,
            "delta_geo_ref_rad": args.delta_geo_ref,
            "c1_abs": args.c1_abs,
        },
        "results": [{k: v for k, v in r.items() if k != "out_df"} for r in results],
        "out_csv": args.out,
    }
    with open(args.chi2_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print a compact human log
    print("=== STRONG sigma_tot(sqrt(s)) NO-FIT (PDG baseline) + GEO modulation ===")
    print(f"data    : {args.data}")
    print(f"window  : [{args.smin_GeV}, {args.smax_GeV}] GeV")
    print(f"channel : {args.channel}")
    print("Baseline (frozen PDG params)")
    print(f"  P,H   = {pars.P_mb}, {pars.H_mb}  mb")
    print(f"  R1,eta1 = {pars.R1_mb}, {pars.eta1}")
    print(f"  R2,eta2 = {pars.R2_mb}, {pars.eta2}")
    print(f"  sM    = {pars.sM_GeV2:.6f} GeV^2")
    print("Geometry (single-shot)")
    print(f"  A       = {args.A}")
    print(f"  template= {args.template}")
    print(f"  env_mode= {args.env_mode} (ref sqrt(s)={args.sqrts_ref_GeV} GeV)")
    print(f"  delta_geo_ref = {args.delta_geo_ref} rad, |c1|={args.c1_abs}")
    for r in results:
        if r.get("n", 0) == 0:
            print(f"  [{r['channel']}] n=0 (no rows)")
            continue
        print(f"  [{r['channel']}] n={r['n']}  chi2_SM={r['chi2_SM']:.6f}  chi2_GEO={r['chi2_GEO']:.6f}  dchi2={r['dchi2']:.6f}")
    print(f"out_csv : {args.out}")
    print(f"chi2_js : {args.chi2_out}")


if __name__ == "__main__":
    main()
