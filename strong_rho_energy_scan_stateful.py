#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stateful STRONG rho(s) runner.

This is a *film/stateful* version of `strong_rho_energy_scan_v3.py`.
It reproduces the same frozen-PDG sigma_tot baseline + DDR rho proxy, then
applies the preregistered GEO phase rotation.

The key difference is that sigma_SM and its derivative are computed from an
explicit internal state evolved along t = ln(s/sM).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from integration_artifacts.mastereq.strong_pdg_stateful_dynamics import PDGParamsRho, scan_rho_stateful


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
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
    ap.add_argument("--data", required=True)
    ap.add_argument("--channel", choices=["pp", "pbarp", "both"], default="both")
    ap.add_argument("--A", type=float, required=True)
    ap.add_argument("--A_I", type=float, default=None, help="(two-channel) Imag/bulk amplitude (unused here; accepted for runbook symmetry).")
    ap.add_argument("--A_R", type=float, default=None, help="(two-channel) Real/dispersive amplitude. If set, overrides --A for phase-sensitive observables (rho).")
    ap.add_argument("--template", choices=["cos", "sin"], default="cos")
    ap.add_argument("--env_mode", choices=["none", "debroglie", "log", "radius", "eikonal", "radius_amp", "eikonal_amp"], default="none")
    ap.add_argument("--sqrts_ref_GeV", type=float, default=13000.0)
    ap.add_argument("--delta_geo_ref", type=float, default=-1.315523)
    ap.add_argument("--c1_abs", type=float, default=0.725147)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chi2_out", required=True)
    ap.add_argument("--out_csv", default=None)

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

    df = load_data(args.data)
    pars = PDGParamsRho()

    # two-channel amplitude selection (phase-sensitive panel): A_eff = A_R if provided else A
    A_eff = float(args.A_R) if args.A_R is not None else float(args.A)

    outs = []
    for ch in (["pp", "pbarp"] if args.channel == "both" else [args.channel]):
        sub = df[df["channel"] == ch].copy()
        if len(sub) == 0:
            continue
        sq = sub["sqrts_GeV"].to_numpy(dtype=float)

        sig_sm, rho_sm, phi, sig_geo, rho_geo = scan_rho_stateful(
            sq,
            ch,  # type: ignore[arg-type]
            pars,
            A=A_eff,
            delta_geo_ref=float(args.delta_geo_ref),
            c1_abs=float(args.c1_abs),
            template=args.template,
            env_mode=args.env_mode,
            sqrts_ref_GeV=float(args.sqrts_ref_GeV),
        )

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

    chi2_sm = chi2_diag(out_df["rho"].to_numpy(), out_df["rho_sm"].to_numpy(), out_df["err"].to_numpy())
    chi2_geo = chi2_diag(out_df["rho"].to_numpy(), out_df["rho_geo"].to_numpy(), out_df["err"].to_numpy())

    summary = {
        "data": args.data,
        "channel": args.channel,
        "A": float(args.A),
        "A_I": None if args.A_I is None else float(args.A_I),
        "A_R": None if args.A_R is None else float(args.A_R),
        "A_eff_used_for_rho": float(A_eff),
        "template": args.template,
        "env_mode": args.env_mode,
        "sqrts_ref_GeV": float(args.sqrts_ref_GeV),
        "delta_geo_ref": float(args.delta_geo_ref),
        "c1_abs": float(args.c1_abs),
        "n": int(len(out_df)),
        "chi2_SM": float(chi2_sm),
        "chi2_GEO": float(chi2_geo),
        "dchi2": float(chi2_sm - chi2_geo),
    }
    Path(args.chi2_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
