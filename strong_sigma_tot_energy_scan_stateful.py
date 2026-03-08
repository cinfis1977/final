#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stateful STRONG sigma_tot runner.

This is a drop-in *film/stateful* version of `strong_sigma_tot_energy_scan_v2.py`.
It reproduces the same frozen-PDG baseline + GEO modulation outputs, but computes
sigma_SM by evolving an internal state along t = ln(s/sM) and deriving observables
from that state.

Output columns match the v2 runner for easy diffing / golden checks.
"""

from __future__ import annotations

import argparse
import json
from typing import Tuple

import numpy as np
import pandas as pd

from integration_artifacts.mastereq.strong_pdg_stateful_dynamics import PDGParamsSigmaTot, scan_sigma_tot_stateful


def _pick_col(df: pd.DataFrame, candidates: Tuple[str, ...]) -> str:
    cols = {c.lower(): c for c in df.columns}
    for k in candidates:
        if k.lower() in cols:
            return cols[k.lower()]
    raise KeyError(f"Could not find any of columns {candidates} in: {list(df.columns)}")


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    sqrts_col = _pick_col(df, ("sqrts_GeV", "sqrt_s_GeV", "sqrts", "sqrt_s", "sqrtS_GeV"))
    sig_col = _pick_col(df, ("sigma_mb", "sigma_tot_mb", "sigma_tot", "sigma"))
    err_col = _pick_col(df, ("err_mb", "sigma_err_mb", "sigma_tot_err", "err", "sigma_err"))

    out = pd.DataFrame({
        "sqrts_GeV": pd.to_numeric(df[sqrts_col], errors="coerce"),
        "sigma_mb": pd.to_numeric(df[sig_col], errors="coerce"),
        "err_mb": pd.to_numeric(df[err_col], errors="coerce"),
    })
    if "channel" in [c.lower() for c in df.columns]:
        ch_col = [c for c in df.columns if c.lower() == "channel"][0]
        out["channel"] = df[ch_col].astype(str).str.strip().str.lower()
    else:
        out["channel"] = "pp"

    out = out.dropna().reset_index(drop=True)
    out = out[(out.err_mb > 0) & (out.sqrts_GeV > 0)].reset_index(drop=True)
    return out


def chi2_diag(y: np.ndarray, yhat: np.ndarray, err: np.ndarray) -> float:
    r = (y - yhat) / err
    return float(np.sum(r * r))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Input CSV (e.g., pdg_sigma_tot_clean.csv)")
    ap.add_argument("--channel", choices=["pp", "pbarp", "both", "all"], default="pp")
    ap.add_argument("--smin_GeV", type=float, default=7.0)
    ap.add_argument("--smax_GeV", type=float, default=1.0e5)
    ap.add_argument("--A", type=float, default=0.0)
    ap.add_argument("--A_I", type=float, default=None, help="(two-channel) Imag/bulk amplitude. If set, overrides --A for bulk observables (sigma_tot).")
    ap.add_argument("--A_R", type=float, default=None, help="(two-channel) Real/interference amplitude (unused here; accepted for runbook symmetry).")
    ap.add_argument("--template", choices=["cos", "sin"], default="cos")
    ap.add_argument("--env_mode", choices=["none", "debroglie", "log", "radius", "eikonal"], default="none")
    ap.add_argument("--sqrts_ref_GeV", type=float, default=13000.0)
    ap.add_argument("--delta_geo_ref", type=float, default=-1.315523)
    ap.add_argument("--c1_abs", type=float, default=0.725147)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chi2_out", required=True)
    args = ap.parse_args()
    if args.channel == "all":
        args.channel = "both"

    df = load_data(args.data)
    df = df[(df.sqrts_GeV >= args.smin_GeV) & (df.sqrts_GeV <= args.smax_GeV)].reset_index(drop=True)

    pars = PDGParamsSigmaTot()

    # two-channel amplitude selection (bulk panel): A_eff = A_I if provided else A
    A_eff = float(args.A_I) if args.A_I is not None else float(args.A)

    def run_one(ch: str) -> dict:
        d = df[df.channel == ch].copy()
        if len(d) == 0:
            return {"channel": ch, "n": 0}

        sq = d.sqrts_GeV.to_numpy(dtype=float)
        y = d.sigma_mb.to_numpy(dtype=float)
        e = d.err_mb.to_numpy(dtype=float)

        sm, scale, geo = scan_sigma_tot_stateful(
            sq,
            ch,  # type: ignore[arg-type]
            pars,
            A_rad=A_eff,
            delta_geo_ref_rad=float(args.delta_geo_ref),
            c1_abs=float(args.c1_abs),
            template=args.template,
            env_mode=args.env_mode,
            sqrts_ref_GeV=float(args.sqrts_ref_GeV),
        )

        chi_sm = chi2_diag(y, sm, e)
        chi_geo = chi2_diag(y, geo, e)

        outd = d.copy()
        outd["sigma_sm_mb"] = sm
        outd["sigma_geo_mb"] = geo
        outd["resid_sm"] = (y - sm) / e
        outd["resid_geo"] = (y - geo) / e
        outd["env_scale"] = scale if float(A_eff) != 0.0 else 0.0

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

    frames = [r["out_df"] for r in results if "out_df" in r]
    out_df = pd.concat(frames, axis=0, ignore_index=True) if frames else pd.DataFrame()
    out_df.to_csv(args.out, index=False)

    summary = {
        "data": args.data,
        "s_window_GeV": [args.smin_GeV, args.smax_GeV],
        "channel": args.channel,
        "baseline": {
            "form": "PDG/COMPETE (stateful film): P + H ln^2(s/sM) + R1 (s/sM)^(-eta1) +/- R2 (s/sM)^(-eta2)",
            "P_mb": pars.P_mb,
            "H_mb": pars.H_mb,
            "R1_mb": pars.R1_mb,
            "eta1": pars.eta1,
            "R2_mb": pars.R2_mb,
            "eta2": pars.eta2,
            "sM_GeV2": pars.sM_GeV2,
        },
        "geometry": {
            "A_rad": float(args.A),
            "A_I": None if args.A_I is None else float(args.A_I),
            "A_R": None if args.A_R is None else float(args.A_R),
            "A_eff_used_for_sigma_tot": float(A_eff),
            "template": args.template,
            "env_mode": args.env_mode,
            "sqrts_ref_GeV": float(args.sqrts_ref_GeV),
            "delta_geo_ref_rad": float(args.delta_geo_ref),
            "c1_abs": float(args.c1_abs),
        },
        "results": [{k: v for k, v in r.items() if k != "out_df"} for r in results],
        "out_csv": args.out,
    }
    with open(args.chi2_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
