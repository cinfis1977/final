#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STRONG C1 runner: amplitude-level (toy) eikonal core.

This runner is the STRONG analogue of WEAK's "internal state + evolution law +
observables from state + integrity + anti-fallback" closure.

It *does not* evaluate the frozen PDG/COMPETE closed form. Instead it evolves a
complex eikonal chi(b,t) along t=ln(s/s0) and computes:
  - sigma_tot_mb from Im F(s,0) (optical theorem proxy)
  - rho from Re F(s,0)/Im F(s,0)

Anti-fallback
-------------
If env var STRONG_C1_POISON_PDG_CALLS=1 is set, this runner imports the known
PDG/COMPETE baseline harness modules and overwrites their *baseline-eval*
functions with stubs that raise. Import graphs are not blocked; only accidental
fallback calls are made impossible.

Inputs
------
- CSV with at least: sqrts_GeV
  Optional: channel (pp/pbarp) is kept as a label only.

Outputs
-------
- CSV with columns:
    sqrts_GeV, channel, sigma_tot_sm_mb, rho_sm, sigma_tot_geo_mb, rho_geo,
    F_re, F_im, t, chiI_min, chiI_max, S_abs_max
- JSON summary with integrity and anti-fallback flags.

"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from types import ModuleType


def _poison_attr(mod: ModuleType, attr: str, *, label: str) -> bool:
    if not hasattr(mod, attr):
        return False

    def _boom(*_a, **_k):
        raise RuntimeError(f"STRONG C1 anti-fallback: forbidden PDG call: {label}.{attr}")

    setattr(mod, attr, _boom)
    return True


def _maybe_poison_pdg_calls() -> dict:
    """Optionally overwrite baseline-eval functions so accidental fallback calls raise.

    This is intentionally *not* an import-blocking mechanism.
    """

    active = os.environ.get("STRONG_C1_POISON_PDG_CALLS", "0") == "1"
    info: dict = {"pdg_call_poison_active": bool(active), "poisoned_targets": [], "missing_modules": []}
    if not active:
        return info

    targets: list[tuple[str, list[str]]] = [
        ("strong_sigma_tot_energy_scan_v2", ["sigma_tot_pdg_mb"]),
        ("strong_sigma_tot_energy_scan_v2_AIAR_FIX2", ["sigma_tot_pdg_mb"]),
        ("strong_rho_energy_scan_v3", ["sigma_tot_pdg_mb", "dsigma_dlns_pdg_mb", "rho_sm_proxy"]),
        ("strong_rho_energy_scan_v3_AIAR_FIX2", ["sigma_tot_pdg_mb", "dsigma_dlns_pdg_mb", "rho_sm_proxy"]),
        ("integration_artifacts.mastereq.strong_pdg_stateful_dynamics", ["scan_sigma_tot_stateful", "scan_rho_stateful"]),
    ]

    for modname, attrs in targets:
        try:
            mod = __import__(modname, fromlist=["*"])
        except Exception:
            info["missing_modules"].append(modname)
            continue

        for a in attrs:
            if _poison_attr(mod, a, label=modname):
                info["poisoned_targets"].append(f"{modname}.{a}")

    return info


import numpy as np
import pandas as pd

from integration_artifacts.mastereq.strong_c1_eikonal_amplitude import (
    EikonalC1Params,
    EikonalC1State,
    forward_amplitude_from_state,
    t_from_sqrts,
)


def _pick_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str:
    cols = {c.lower(): c for c in df.columns}
    for k in candidates:
        if k.lower() in cols:
            return cols[k.lower()]
    raise KeyError(f"Could not find any of columns {candidates} in: {list(df.columns)}")


def _rotate_amplitude(rho: float, sigma_mb: float, phi: float) -> tuple[float, float]:
    """Apply the same forward-amplitude rotation convention as the v3 rho runner."""

    # F_SM ∝ sigma * (rho + i)
    c = float(np.cos(phi))
    s = float(np.sin(phi))
    re = float(rho) * c - 1.0 * s
    im = float(rho) * s + 1.0 * c
    im_safe = im if abs(im) > 1e-30 else (1e-30 if im >= 0 else -1e-30)
    rho_geo = re / im_safe
    sigma_geo = float(sigma_mb) * im
    return rho_geo, sigma_geo


def main() -> int:
    antifallback = _maybe_poison_pdg_calls()

    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Input CSV with sqrts_GeV (and optional channel)")
    ap.add_argument("--out", required=True, help="Output CSV")
    ap.add_argument("--summary_out", required=True, help="Output JSON summary")

    # Optional GEO rotation (kept for runbook symmetry; default is null)
    ap.add_argument("--A", type=float, default=0.0, help="GEO phase amplitude (radians); A=0 => null")
    ap.add_argument("--phi0", type=float, default=-1.315523, help="Reference phase argument (radians)")
    ap.add_argument("--template", choices=["cos", "sin"], default="cos")

    # C1 eikonal params (exposed minimally; defaults are chosen to be stable)
    ap.add_argument("--s0_GeV2", type=float, default=1.0)
    ap.add_argument("--dt_max", type=float, default=None, help="Max step in t (substepping); smaller => more stable/accurate")
    ap.add_argument("--sigma_norm_mb", type=float, default=None)
    ap.add_argument("--b_max", type=float, default=None)
    ap.add_argument("--nb", type=int, default=None)

    args = ap.parse_args()

    df = pd.read_csv(args.data)
    sq_col = _pick_col(df, ("sqrts_GeV", "sqrt_s_GeV", "sqrts", "sqrt_s"))
    out_df = pd.DataFrame({"sqrts_GeV": pd.to_numeric(df[sq_col], errors="coerce")})

    if "channel" in [c.lower() for c in df.columns]:
        ch_col = [c for c in df.columns if c.lower() == "channel"][0]
        out_df["channel"] = df[ch_col].astype(str).str.strip().str.lower()
    else:
        out_df["channel"] = "pp"

    out_df = out_df.dropna().reset_index(drop=True)
    out_df = out_df[out_df["sqrts_GeV"] > 0].reset_index(drop=True)

    pars = EikonalC1Params(s0_GeV2=float(args.s0_GeV2))
    if args.dt_max is not None:
        pars = EikonalC1Params(**{**asdict(pars), "dt_max": float(args.dt_max)})
    if args.sigma_norm_mb is not None:
        pars = EikonalC1Params(**{**asdict(pars), "sigma_norm_mb": float(args.sigma_norm_mb)})
    if args.b_max is not None:
        pars = EikonalC1Params(**{**asdict(pars), "b_max": float(args.b_max)})
    if args.nb is not None:
        pars = EikonalC1Params(**{**asdict(pars), "nb": int(args.nb)})

    t_arr = t_from_sqrts(out_df["sqrts_GeV"].to_numpy(dtype=float), s0_GeV2=pars.s0_GeV2)

    # Ensure monotone advance in t by sorting, but keep output order.
    order = np.argsort(t_arr)
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))

    t_sorted = t_arr[order]

    state = EikonalC1State.initialize(pars)

    F_re = np.empty_like(t_sorted, dtype=float)
    F_im = np.empty_like(t_sorted, dtype=float)
    sigma_sm = np.empty_like(t_sorted, dtype=float)
    rho_sm = np.empty_like(t_sorted, dtype=float)
    chiI_min = np.empty_like(t_sorted, dtype=float)
    chiI_max = np.empty_like(t_sorted, dtype=float)
    Sabs_max = np.empty_like(t_sorted, dtype=float)

    for i, t in enumerate(t_sorted):
        state.advance_to(float(t), pars)
        F = forward_amplitude_from_state(state)
        F_re[i] = float(np.real(F))
        F_im[i] = float(np.imag(F))
        sigma_sm[i] = float(pars.sigma_norm_mb) * F_im[i]
        im_safe = F_im[i] if abs(F_im[i]) > 1e-30 else (1e-30 if F_im[i] >= 0 else -1e-30)
        rho_sm[i] = F_re[i] / im_safe
        chiI_min[i] = float(np.min(state.chi_I))
        chiI_max[i] = float(np.max(state.chi_I))
        # Unitarity/absorptivity: |S| = exp(-chiI) <= 1
        Sabs_max[i] = float(np.max(np.exp(-np.asarray(state.chi_I, dtype=float))))

    # GEO rotation (optional)
    A = float(args.A)
    if A == 0.0:
        sigma_geo = sigma_sm.copy()
        rho_geo = rho_sm.copy()
        phi_used = np.zeros_like(t_sorted)
    else:
        # A * template(phi0) is used as a single-phase knob for now.
        # (A future C-step can replace this with a t-dependent accumulation law.)
        mod = float(np.cos(float(args.phi0)) if args.template == "cos" else np.sin(float(args.phi0)))
        phi = A * mod
        phi_used = np.full_like(t_sorted, float(phi), dtype=float)
        rho_geo = np.empty_like(rho_sm)
        sigma_geo = np.empty_like(sigma_sm)
        for i in range(len(t_sorted)):
            r, s = _rotate_amplitude(float(rho_sm[i]), float(sigma_sm[i]), float(phi_used[i]))
            rho_geo[i] = r
            sigma_geo[i] = s

    # Restore original order
    sigma_sm_u = sigma_sm[inv]
    rho_sm_u = rho_sm[inv]
    sigma_geo_u = sigma_geo[inv]
    rho_geo_u = rho_geo[inv]
    t_u = t_sorted[inv]
    chiI_min_u = chiI_min[inv]
    chiI_max_u = chiI_max[inv]
    phi_u = phi_used[inv]
    Fre_u = F_re[inv]
    Fim_u = F_im[inv]
    Sabs_u = Sabs_max[inv]

    out_df["t"] = t_u
    out_df["sigma_tot_sm_mb"] = sigma_sm_u
    out_df["rho_sm"] = rho_sm_u
    out_df["sigma_tot_geo_mb"] = sigma_geo_u
    out_df["rho_geo"] = rho_geo_u
    out_df["phi_geo"] = phi_u

    out_df["F_re"] = Fre_u
    out_df["F_im"] = Fim_u

    out_df["chiI_min"] = chiI_min_u
    out_df["chiI_max"] = chiI_max_u
    out_df["S_abs_max"] = Sabs_u

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    # Integrity summary
    finite = np.isfinite(out_df[["sigma_tot_sm_mb", "rho_sm", "sigma_tot_geo_mb", "rho_geo", "F_re", "F_im"]].to_numpy(dtype=float))
    integrity = {
        "sigma_tot_nonnegative": bool(np.min(out_df["sigma_tot_sm_mb"].to_numpy(float)) >= -1e-12),
        "chiI_nonnegative": bool(np.min(out_df["chiI_min"].to_numpy(float)) >= -1e-12),
        "S_abs_le_1": bool(np.max(out_df["S_abs_max"].to_numpy(float)) <= 1.0 + 1e-10),
        "rho_finite": bool(np.all(finite[:, 1])),
        "no_nan_inf": bool(np.all(finite)),
        "rho_reasonable_bound": bool(np.max(np.abs(out_df["rho_sm"].to_numpy(float))) <= 10.0),
        "ImF_positive": bool(np.min(out_df["F_im"].to_numpy(float)) >= -1e-12),
    }

    summary = {
        "runner": "strong_amplitude_eikonal_energy_scan_c1.py",
        "core": "STRONG C1 toy eikonal amplitude",
        "notes": "Amplitude-level internal state chi(b,t) evolved along t=ln(s/s0); forward amplitude F(s,0) derived from state; sigma_tot = sigma_norm*ImF and rho=ReF/ImF.",
        "amplitude_core_used": True,
        "pdg_baseline_used": False,
        "pars": asdict(pars),
        "geo": {"A": float(A), "template": args.template, "phi0": float(args.phi0)},
        "anti_fallback": antifallback,
        "integrity": integrity,
        "n_points": int(len(out_df)),
        "ranges": {
            "sqrts_GeV_min": float(np.min(out_df["sqrts_GeV"].to_numpy(float))) if len(out_df) else None,
            "sqrts_GeV_max": float(np.max(out_df["sqrts_GeV"].to_numpy(float))) if len(out_df) else None,
            "sigma_tot_sm_mb_min": float(np.min(out_df["sigma_tot_sm_mb"].to_numpy(float))) if len(out_df) else None,
            "sigma_tot_sm_mb_max": float(np.max(out_df["sigma_tot_sm_mb"].to_numpy(float))) if len(out_df) else None,
            "rho_sm_min": float(np.min(out_df["rho_sm"].to_numpy(float))) if len(out_df) else None,
            "rho_sm_max": float(np.max(out_df["rho_sm"].to_numpy(float))) if len(out_df) else None,
            "chiI_max": float(np.max(out_df["chiI_max"].to_numpy(float))) if len(out_df) else None,
            "F_im_min": float(np.min(out_df["F_im"].to_numpy(float))) if len(out_df) else None,
            "F_im_max": float(np.max(out_df["F_im"].to_numpy(float))) if len(out_df) else None,
        },
    }

    summ_path = Path(args.summary_out)
    summ_path.parent.mkdir(parents=True, exist_ok=True)
    summ_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Fail-fast if integrity is violated.
    if not all(integrity.values()):
        bad = [k for k, v in integrity.items() if not v]
        raise SystemExit(f"Integrity checks failed: {bad}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
