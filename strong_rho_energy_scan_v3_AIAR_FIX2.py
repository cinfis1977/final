#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strong_rho_energy_scan_v2.py

No-fit / no-scan energy scan for rho(sqrt(s)) using a frozen PDG/COMPETE-style sigma_tot baseline
and a minimal dispersion-relation proxy for rho_SM.

Then applies a preregistered geometric phase rotation:
  F_SM(0) ∝ sigma_SM * (rho_SM + i)
  F_GEO(0) = F_SM(0) * exp(i * phi_geo(s))
which implies:
  sigma_GEO = sigma_SM * Im[(rho_SM + i) * exp(i phi_geo)]
  rho_GEO   = Re[(rho_SM + i) * exp(i phi_geo)] / Im[(rho_SM + i) * exp(i phi_geo)]

Env scaling options for phase:
  none     : scale = 1
  debroglie: scale = sqrts_ref / sqrts
  log      : scale = 2 ln(sqrts/sqrts_ref)
  radius   : scale = sqrt( sigma_SM(s) / sigma_SM(s_ref) )   (argument scaling)
  radius_amp : amp_scale = sqrt( sigma_SM(s) / sigma_SM(s_ref) ) (amplitude scaling)
  eikonal  : scale = ln(s/sM) / ln(s_ref/sM)                 (argument scaling)
  eikonal_amp : amp_scale = ln(s/sM) / ln(s_ref/sM)          (amplitude scaling, multi-exchange)

Outputs:
  - CSV with per-point predictions
  - JSON summary with chi2 values and dchi2

This is a harness for strong-sector "phase-sensitive" energy scans, not a full eikonal model.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd


Channel = Literal["pp", "pbarp"]
ChannelSel = Literal["pp", "pbarp", "both"]


@dataclass(frozen=True)
class PDGParams:
    # COMPETE/PDG-style
    sM_GeV2: float = 1.0
    P_mb: float = 33.73
    H_mb: float = 0.283
    R1_mb: float = 13.67
    eta1: float = 0.412
    R2_mb: float = 7.77
    eta2: float = 0.562


def sigma_tot_pdg_mb(sqrts_GeV: np.ndarray, channel: Channel, pars: PDGParams) -> np.ndarray:
    s = np.asarray(sqrts_GeV, dtype=float) ** 2
    x = np.maximum(s / float(pars.sM_GeV2), 1e-30)
    logx = np.log(x)
    base = float(pars.P_mb) + float(pars.H_mb) * (logx ** 2) + float(pars.R1_mb) * (x ** (-float(pars.eta1)))
    odd = float(pars.R2_mb) * (x ** (-float(pars.eta2)))
    return base - odd if channel == "pp" else base + odd


def dsigma_dlns_pdg_mb(sqrts_GeV: np.ndarray, channel: Channel, pars: PDGParams) -> np.ndarray:
    """
    d sigma / d ln(s) for the frozen PDG baseline.
    Since logx = ln(s/sM), d/dln(s) == d/dlogx.
    """
    s = np.asarray(sqrts_GeV, dtype=float) ** 2
    x = np.maximum(s / float(pars.sM_GeV2), 1e-30)
    logx = np.log(x)

    # sigma pieces
    # d/dlogx [ H logx^2 ] = 2 H logx
    term_log = 2.0 * float(pars.H_mb) * logx

    # d/dlogx [ R x^{-eta} ] = -eta R x^{-eta}
    term_r1 = -float(pars.eta1) * float(pars.R1_mb) * (x ** (-float(pars.eta1)))
    term_r2 = -float(pars.eta2) * float(pars.R2_mb) * (x ** (-float(pars.eta2)))

    if channel == "pp":
        # sigma = base - odd, so derivative also subtracts odd-derivative
        return term_log + term_r1 - term_r2
    return term_log + term_r1 + term_r2


def rho_sm_proxy(sqrts_GeV: np.ndarray, channel: Channel, pars: PDGParams) -> np.ndarray:
    """
    Minimal DDR proxy:
      rho ≈ (pi/2) * (d sigma / d ln s) / sigma
    (Harness-level; not a full amplitude model.)
    """
    sig = np.maximum(sigma_tot_pdg_mb(sqrts_GeV, channel, pars), 1e-30)
    ds = dsigma_dlns_pdg_mb(sqrts_GeV, channel, pars)
    return (math.pi / 2.0) * (ds / sig)


def env_scale_basic(sqrts_GeV: np.ndarray, mode: Literal["none", "debroglie", "log"], sqrts_ref_GeV: float) -> np.ndarray:
    x = np.asarray(sqrts_GeV, dtype=float)
    if mode == "none":
        return np.ones_like(x)
    if mode == "debroglie":
        ref = max(float(sqrts_ref_GeV), 1e-30)
        return ref / np.maximum(x, 1e-30)
    if mode == "log":
        ref = max(float(sqrts_ref_GeV), 1e-30)
        return 2.0 * np.log(np.maximum(x, 1e-30) / ref)
    raise ValueError(f"Unknown mode {mode}")


def env_scale_radius_from_sigma(sigma_sm_mb: np.ndarray, sigma_sm_ref_mb: float) -> np.ndarray:
    ref = max(float(sigma_sm_ref_mb), 1e-30)
    return np.sqrt(np.maximum(np.asarray(sigma_sm_mb, dtype=float), 1e-30) / ref)


def phase_geo(
    sqrts_GeV: np.ndarray,
    sigma_sm_mb: np.ndarray,
    pars: PDGParams,
    *,
    A: float,
    delta_geo_ref: float,
    c1_abs: float,
    template: Literal["cos", "sin"],
    env_mode: Literal["none", "debroglie", "log", "radius", "eikonal", "radius_amp", "eikonal_amp"],
    sqrts_ref_GeV: float,
) -> np.ndarray:
    """
    phi_geo(s) = A * c1_abs * template( delta_geo_ref * scale(s) )
    """
    sq = np.asarray(sqrts_GeV, dtype=float)

    # Two families of scaling:
    #  - argument-scaling modes (radius/eikonal/log/debroglie/none): phase_arg = delta_geo_ref * scale
    #  - amplitude-scaling modes (radius_amp/eikonal_amp): phase_arg = delta_geo_ref (fixed), phi multiplied by amp_scale(s)
    arg_scale = None
    amp_scale = np.ones_like(sq, dtype=float)

    if env_mode == "radius":
        sm_ref = float(sigma_tot_pdg_mb(np.array([sqrts_ref_GeV], dtype=float), "pp", pars)[0])
        arg_scale = env_scale_radius_from_sigma(sigma_sm_mb, sm_ref)
    elif env_mode == "eikonal":
        s = np.asarray(sq, dtype=float) ** 2
        s_ref = float(sqrts_ref_GeV) ** 2
        sM = float(pars.sM_GeV2)
        logx = np.log(np.maximum(s / sM, 1e-30))
        logx_ref = float(np.log(max(s_ref / sM, 1e-30)))
        arg_scale = np.ones_like(logx) if abs(logx_ref) < 1e-12 else (logx / logx_ref)
    elif env_mode == "radius_amp":
        # amplitude scaling using interaction-radius proxy from sigma_SM
        sm_ref = float(sigma_tot_pdg_mb(np.array([sqrts_ref_GeV], dtype=float), "pp", pars)[0])
        amp_scale = env_scale_radius_from_sigma(sigma_sm_mb, sm_ref)
        arg_scale = None
    elif env_mode == "eikonal_amp":
        # amplitude scaling using param-free multi-exchange proxy
        s = np.asarray(sq, dtype=float) ** 2
        s_ref = float(sqrts_ref_GeV) ** 2
        sM = float(pars.sM_GeV2)
        logx = np.log(np.maximum(s / sM, 1e-30))
        logx_ref = float(np.log(max(s_ref / sM, 1e-30)))
        amp_scale = np.ones_like(logx) if abs(logx_ref) < 1e-12 else (logx / logx_ref)
        arg_scale = None
    else:
        # basic argument scaling
        arg_scale = env_scale_basic(sq, env_mode, sqrts_ref_GeV)

    if arg_scale is None:
        phase_arg = float(delta_geo_ref)
    else:
        phase_arg = float(delta_geo_ref) * np.asarray(arg_scale, dtype=float)

    mod = np.cos(phase_arg) if template == "cos" else np.sin(phase_arg)
    return float(A) * float(c1_abs) * amp_scale * mod


def rotate_rho_sigma(rho_sm: np.ndarray, sigma_sm: np.ndarray, phi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Apply forward amplitude phase rotation, assuming:
      F_SM ∝ sigma_sm * (rho_sm + i)
      F_GEO = F_SM * exp(i phi)

    Then:
      sigma_geo = sigma_sm * Im[(rho+i) e^{i phi}]   (since Im(rho+i) = 1)
      rho_geo   = Re[(rho+i) e^{i phi}] / Im[(rho+i) e^{i phi}]
    """
    rho = np.asarray(rho_sm, dtype=float)
    sig = np.asarray(sigma_sm, dtype=float)
    ph = np.asarray(phi, dtype=float)

    # z = (rho + i) e^{i phi}
    c = np.cos(ph)
    s = np.sin(ph)

    re = rho * c - 1.0 * s
    im = rho * s + 1.0 * c

    im_safe = np.where(np.abs(im) < 1e-30, np.sign(im) * 1e-30 + 1e-30, im)
    rho_geo = re / im_safe
    sigma_geo = sig * im
    return rho_geo, sigma_geo


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # normalize columns
    colmap = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in colmap:
                return colmap[n]
        return None

    c_s = pick("sqrts_gev", "sqrts", "sqrt_s", "sqrt_s_gev")
    c_r = pick("rho", "rho_val", "rho_mb", "rho_value")
    c_e = pick("err", "rho_err", "error", "sigma", "rho_sigma")
    if c_s is None or c_r is None or c_e is None:
        raise SystemExit(f"CSV must contain sqrts_GeV, rho, err (found columns: {list(df.columns)})")

    df = df.rename(columns={c_s: "sqrts_GeV", c_r: "rho", c_e: "err"})
    if "channel" not in df.columns:
        df["channel"] = "pp"
    df["channel"] = df["channel"].astype(str).str.lower().replace({"p-pbar": "pbarp", "pbar": "pbarp"})
    if "experiment" not in df.columns:
        df["experiment"] = ""
    return df


def chi2_diag(y: np.ndarray, mu: np.ndarray, err: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    mu = np.asarray(mu, dtype=float)
    e = np.asarray(err, dtype=float)
    e = np.where(e <= 0, 1e-12, e)
    r = (y - mu) / e
    return float(np.sum(r * r))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Input CSV containing rho(s) points.")
    ap.add_argument("--channel", choices=["pp", "pbarp", "both"], default="both", help="Channel selection (use --channel all as alias for both).")
    ap.add_argument("--A", type=float, default=0.0, help="Geometry amplitude (radians). A=0 => null.")
    ap.add_argument("--A_I", type=float, default=None, help="(two-channel) Imag/bulk amplitude (unused here; accepted for symmetry).")
    ap.add_argument("--A_R", type=float, default=None, help="(two-channel) Real/interference amplitude. If set, overrides --A for rho/CNI-like observables.")
    ap.add_argument("--template", choices=["cos", "sin"], default="cos")
    ap.add_argument("--env_mode", choices=["none", "debroglie", "log", "radius", "eikonal", "radius_amp", "eikonal_amp"], default="none")
    ap.add_argument("--sqrts_ref_GeV", type=float, default=13000.0)
    ap.add_argument("--delta_geo_ref", type=float, default=-1.315523)
    ap.add_argument("--c1_abs", type=float, default=0.725147)
    ap.add_argument("--out", required=True, help="Output CSV")
    ap.add_argument("--chi2_out", required=True, help="Output JSON with chi2 summary")
    ap.add_argument("--out_csv", default=None, help="Alias for --out (backward compat)")

    # Backward-compat aliases in argv
    argv = sys.argv[1:]
    if "--channel" in argv:
        i = argv.index("--channel")
        if i + 1 < len(argv) and argv[i + 1] == "all":
            argv[i + 1] = "both"
    if "--out_csv" in argv:
        i = argv.index("--out_csv")
        if i + 1 < len(argv):
            if "--out" in argv:
                j = argv.index("--out")
                if j + 1 < len(argv):
                    argv[j + 1] = argv[i + 1]
            else:
                argv.extend(["--out", argv[i + 1]])

    args = ap.parse_args(argv)
    if args.out_csv:
        args.out = args.out_csv

    # two-channel amplitude selection (real/interference panel): A_eff = A_R if provided else A
    A_eff = float(args.A_R) if args.A_R is not None else float(args.A)

    df = load_data(args.data)
    pars = PDGParams()

    # compute per-point predictions
    outs = []
    for ch in (["pp", "pbarp"] if args.channel == "both" else [args.channel]):
        sub = df[df["channel"] == ch].copy()
        if len(sub) == 0:
            continue
        sq = sub["sqrts_GeV"].to_numpy(dtype=float)

        sig_sm = sigma_tot_pdg_mb(sq, ch, pars)
        rho_sm = rho_sm_proxy(sq, ch, pars)

        phi = phase_geo(
            sq, sig_sm, pars,
            A=A_eff, delta_geo_ref=args.delta_geo_ref, c1_abs=args.c1_abs,
            template=args.template, env_mode=args.env_mode,
            sqrts_ref_GeV=args.sqrts_ref_GeV,
        )

        rho_geo, sig_geo = rotate_rho_sigma(rho_sm, sig_sm, phi)

        out = sub.copy()
        out["sigma_sm_mb"] = sig_sm
        out["sigma_geo_mb"] = sig_geo
        out["rho_sm"] = rho_sm
        out["rho_geo"] = rho_geo
        out["phi_geo_rad"] = phi
        outs.append(out)

    if not outs:
        raise SystemExit("No rows matched selected channel(s).")

    out_df = pd.concat(outs, axis=0).sort_values(["channel", "sqrts_GeV"]).reset_index(drop=True)
    out_df.to_csv(args.out, index=False)

    # chi2
    chi2_sm = chi2_diag(out_df["rho"].to_numpy(), out_df["rho_sm"].to_numpy(), out_df["err"].to_numpy())
    chi2_geo = chi2_diag(out_df["rho"].to_numpy(), out_df["rho_geo"].to_numpy(), out_df["err"].to_numpy())
    dchi2 = chi2_sm - chi2_geo

    summary = {
        "data": args.data,
        "channel": args.channel,
        "A_rad": float(A_eff),
        "A": float(args.A),
        "A_I": (None if args.A_I is None else float(args.A_I)),
        "A_R": (None if args.A_R is None else float(args.A_R)),
        "template": args.template,
        "env_mode": args.env_mode,
        "sqrts_ref_GeV": float(args.sqrts_ref_GeV),
        "delta_geo_ref": float(args.delta_geo_ref),
        "c1_abs": float(args.c1_abs),
        "n": int(len(out_df)),
        "chi2_SM": float(chi2_sm),
        "chi2_GEO": float(chi2_geo),
        "dchi2": float(dchi2),
    }
    Path(args.chi2_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
