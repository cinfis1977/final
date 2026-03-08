#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STRONG C4 runner: HEPData-like pack ingestion (CSV + covariance paths) + χ² closure.

C4 goal
-------
Move STRONG from synthetic inline packs to a paper-facing, path-based pack style:
  - data live in CSV files
  - covariance (diag or full) can be provided via CSV paths
  - runner still uses amplitude-core (C1/C3) and preserves anti-fallback locks

This is a closure/integrity deliverable. It is not a claim of physical accuracy.

Pack format (minimal)
---------------------
{
  "meta": {"name": "..."},
  "model": {"s0_GeV2": 1.0, "dt_max": 0.05, "nb": 600, "b_max": 12.0},
  "geo": {"A": 0.0, "template": "cos", "phi0": 0.0, "omega": 1.0},
  "paths": {
    "data_csv": "strong_scan.csv",
    "cov_sigma_tot_csv": "cov_sigma.csv",   // optional
    "cov_rho_csv": "cov_rho.csv"            // optional
  },
  "columns": {
    "sqrts_GeV": "sqrts_GeV",
    "sigma_tot_mb": "sigma_tot_mb",         // optional
    "sigma_tot_unc_mb": "sigma_tot_unc_mb", // optional
    "rho": "rho",                           // optional
    "rho_unc": "rho_unc"                    // optional
  }
}

If a covariance path is provided for an observable, it is used; otherwise the
runner falls back to diagonal uncertainties if provided.

Outputs
-------
- CSV: predictions + data/residual/pulls (if data exist)
- JSON: chi2 + telemetry, including IO provenance flags

Anti-fallback
-------------
Enable call-poison via any of:
  - STRONG_C1_POISON_PDG_CALLS=1
  - STRONG_C2_POISON_PDG_CALLS=1
  - STRONG_C3_POISON_PDG_CALLS=1
  - STRONG_C4_POISON_PDG_CALLS=1

"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd

from integration_artifacts.mastereq.strong_c1_eikonal_amplitude import (
    EikonalC1Params,
    EikonalC1State,
    forward_amplitude_from_state,
    t_from_sqrts,
)


def _poison_attr(mod: ModuleType, attr: str, *, label: str) -> bool:
    if not hasattr(mod, attr):
        return False

    def _boom(*_a, **_k):
        raise RuntimeError(f"STRONG C4 anti-fallback: forbidden PDG call: {label}.{attr}")

    setattr(mod, attr, _boom)
    return True


def _maybe_poison_pdg_calls() -> dict:
    active = any(
        os.environ.get(k, "0") == "1"
        for k in (
            "STRONG_C4_POISON_PDG_CALLS",
            "STRONG_C3_POISON_PDG_CALLS",
            "STRONG_C2_POISON_PDG_CALLS",
            "STRONG_C1_POISON_PDG_CALLS",
        )
    )
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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_float_array(x: Any, *, name: str) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if a.ndim != 1:
        raise ValueError(f"{name} must be 1D, got shape={a.shape}")
    return a


def _read_cov_csv(path: Path, *, n: int) -> np.ndarray:
    df = pd.read_csv(path)
    C = df.to_numpy(dtype=float)
    if C.shape != (n, n):
        raise ValueError(f"cov matrix shape mismatch in {path}: expected {(n, n)} got {C.shape}")
    return C


def _chi2_from_residuals(resid: np.ndarray, *, unc: np.ndarray | None, cov: np.ndarray | None) -> tuple[float, dict]:
    if cov is not None:
        Cinv = np.linalg.pinv(np.asarray(cov, dtype=float), rcond=1e-12)
        chi2 = float(resid.T @ Cinv @ resid)
        tel = {"kind": "cov", "cond_est": float(np.linalg.cond(cov)) if resid.size else 0.0}
        return chi2, tel

    if unc is None:
        raise ValueError("Need either unc (diag) or cov (full) to compute chi2")

    u = np.asarray(unc, dtype=float)
    if u.shape != resid.shape:
        raise ValueError("unc must match residual shape")
    u_safe = np.where(np.abs(u) > 0, u, np.inf)
    pulls = resid / u_safe
    return float(np.sum(pulls * pulls)), {"kind": "diag"}


def main() -> int:
    antifallback = _maybe_poison_pdg_calls()

    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True, help="Path to STRONG C4 pack JSON")
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_json", required=True)
    args = ap.parse_args()

    pack_path = Path(args.pack)
    pack_dir = pack_path.parent
    pack = _load_json(pack_path)

    cols = pack.get("columns", {})
    col_sqrts = str(cols.get("sqrts_GeV", "sqrts_GeV"))
    col_sig = cols.get("sigma_tot_mb", None)
    col_sig_unc = cols.get("sigma_tot_unc_mb", None)
    col_rho = cols.get("rho", None)
    col_rho_unc = cols.get("rho_unc", None)

    paths = pack.get("paths", {})
    data_csv = paths.get("data_csv")
    if not data_csv:
        raise ValueError("pack.paths.data_csv is required")

    data_path = (pack_dir / str(data_csv)).resolve()
    df = pd.read_csv(data_path)
    if col_sqrts not in df.columns:
        raise ValueError(f"Missing sqrts column {col_sqrts} in {data_path}")

    sqrts = pd.to_numeric(df[col_sqrts], errors="coerce").to_numpy(dtype=float)
    if np.any(~np.isfinite(sqrts)) or np.any(sqrts <= 0):
        raise ValueError("sqrts_GeV must be finite and >0")

    model = pack.get("model", {})
    pars = EikonalC1Params(
        s0_GeV2=float(model.get("s0_GeV2", 1.0)),
        dt_max=float(model.get("dt_max", EikonalC1Params().dt_max)),
        sigma_norm_mb=float(model.get("sigma_norm_mb", EikonalC1Params().sigma_norm_mb)),
        b_max=float(model.get("b_max", EikonalC1Params().b_max)),
        nb=int(model.get("nb", EikonalC1Params().nb)),
    )

    geo = pack.get("geo", {})
    pars = EikonalC1Params(
        **{
            **asdict(pars),
            "geo_A": float(geo.get("A", 0.0)),
            "geo_template": str(geo.get("template", "cos")),
            "geo_phi0": float(geo.get("phi0", 0.0)),
            "geo_omega": float(geo.get("omega", 1.0)),
        }
    )

    geo_applied_in_evolution = bool(abs(float(getattr(pars, "geo_A", 0.0))) > 0.0)

    # Predict from amplitude-core.
    t_arr = t_from_sqrts(sqrts, s0_GeV2=pars.s0_GeV2)
    order = np.argsort(t_arr)
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))

    t_sorted = t_arr[order]
    state = EikonalC1State.initialize(pars)

    F_re = np.empty_like(t_sorted, dtype=float)
    F_im = np.empty_like(t_sorted, dtype=float)
    sig_pred = np.empty_like(t_sorted, dtype=float)
    rho_pred = np.empty_like(t_sorted, dtype=float)

    chiI_min = np.empty_like(t_sorted, dtype=float)
    chiI_max = np.empty_like(t_sorted, dtype=float)
    Sabs_max = np.empty_like(t_sorted, dtype=float)

    for i, t in enumerate(t_sorted):
        state.advance_to(float(t), pars)
        F = forward_amplitude_from_state(state)
        F_re[i] = float(np.real(F))
        F_im[i] = float(np.imag(F))
        sig_pred[i] = float(pars.sigma_norm_mb) * F_im[i]
        im_safe = F_im[i] if abs(F_im[i]) > 1e-30 else (1e-30 if F_im[i] >= 0 else -1e-30)
        rho_pred[i] = F_re[i] / im_safe
        chiI_min[i] = float(np.min(state.chi_I))
        chiI_max[i] = float(np.max(state.chi_I))
        Sabs_max[i] = float(np.max(np.exp(-np.asarray(state.chi_I, dtype=float))))

    # Restore original order.
    t_u = t_sorted[inv]
    Fre_u = F_re[inv]
    Fim_u = F_im[inv]
    sig_u = sig_pred[inv]
    rho_u = rho_pred[inv]
    chiI_min_u = chiI_min[inv]
    chiI_max_u = chiI_max[inv]
    Sabs_u = Sabs_max[inv]

    out_df = pd.DataFrame(
        {
            "sqrts_GeV": sqrts.astype(float),
            "t": t_u,
            "F_re": Fre_u,
            "F_im": Fim_u,
            "sigma_tot_pred_mb": sig_u,
            "rho_pred": rho_u,
            "chiI_min": chiI_min_u,
            "chiI_max": chiI_max_u,
            "S_abs_max": Sabs_u,
        }
    )

    # χ² for any observables present in the CSV.
    chi2_sig = None
    chi2_rho = None
    chi2_tel: dict[str, Any] = {}

    if col_sig is not None and str(col_sig) in df.columns:
        y = pd.to_numeric(df[str(col_sig)], errors="coerce").to_numpy(dtype=float)
        if np.any(~np.isfinite(y)):
            raise ValueError(f"Non-finite data in column {col_sig}")
        resid = y - sig_u
        out_df["sigma_tot_data_mb"] = y
        out_df["sigma_tot_resid_mb"] = resid

        cov = None
        cov_path = paths.get("cov_sigma_tot_csv")
        if cov_path:
            cov = _read_cov_csv(pack_dir / str(cov_path), n=int(y.size))

        unc = None
        if cov is None and col_sig_unc is not None and str(col_sig_unc) in df.columns:
            unc = pd.to_numeric(df[str(col_sig_unc)], errors="coerce").to_numpy(dtype=float)
            if np.any(~np.isfinite(unc)):
                raise ValueError(f"Non-finite uncertainties in column {col_sig_unc}")
            out_df["sigma_tot_unc_mb"] = unc
            u_safe = np.where(np.abs(unc) > 0, unc, np.nan)
            out_df["sigma_tot_pull"] = resid / u_safe

        chi2_sig, tel = _chi2_from_residuals(resid, unc=unc, cov=cov)
        chi2_tel["sigma_tot_mb"] = tel

    if col_rho is not None and str(col_rho) in df.columns:
        y = pd.to_numeric(df[str(col_rho)], errors="coerce").to_numpy(dtype=float)
        if np.any(~np.isfinite(y)):
            raise ValueError(f"Non-finite data in column {col_rho}")
        resid = y - rho_u
        out_df["rho_data"] = y
        out_df["rho_resid"] = resid

        cov = None
        cov_path = paths.get("cov_rho_csv")
        if cov_path:
            cov = _read_cov_csv(pack_dir / str(cov_path), n=int(y.size))

        unc = None
        if cov is None and col_rho_unc is not None and str(col_rho_unc) in df.columns:
            unc = pd.to_numeric(df[str(col_rho_unc)], errors="coerce").to_numpy(dtype=float)
            if np.any(~np.isfinite(unc)):
                raise ValueError(f"Non-finite uncertainties in column {col_rho_unc}")
            out_df["rho_unc"] = unc
            u_safe = np.where(np.abs(unc) > 0, unc, np.nan)
            out_df["rho_pull"] = resid / u_safe

        chi2_rho, tel = _chi2_from_residuals(resid, unc=unc, cov=cov)
        chi2_tel["rho"] = tel

    chi2_total = None
    if chi2_sig is not None or chi2_rho is not None:
        chi2_total = float((chi2_sig or 0.0) + (chi2_rho or 0.0))

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)

    finite = np.isfinite(out_df[["sigma_tot_pred_mb", "rho_pred", "F_re", "F_im"]].to_numpy(dtype=float))
    integrity = {
        "sigma_tot_nonnegative": bool(np.min(out_df["sigma_tot_pred_mb"].to_numpy(float)) >= -1e-12),
        "chiI_nonnegative": bool(np.min(out_df["chiI_min"].to_numpy(float)) >= -1e-12),
        "S_abs_le_1": bool(np.max(out_df["S_abs_max"].to_numpy(float)) <= 1.0 + 1e-10),
        "rho_finite": bool(np.all(np.isfinite(out_df["rho_pred"].to_numpy(float)))),
        "no_nan_inf": bool(np.all(finite)),
        "rho_reasonable_bound": bool(np.max(np.abs(out_df["rho_pred"].to_numpy(float))) <= 10.0),
        "ImF_positive": bool(np.min(out_df["F_im"].to_numpy(float)) >= -1e-12),
    }

    io = {
        "data_csv": str(data_path),
        "cov_sigma_tot_csv": str((pack_dir / str(paths.get("cov_sigma_tot_csv"))).resolve()) if paths.get("cov_sigma_tot_csv") else None,
        "cov_rho_csv": str((pack_dir / str(paths.get("cov_rho_csv"))).resolve()) if paths.get("cov_rho_csv") else None,
        "data_loaded_from_paths": True,
    }

    summary = {
        "pack": {"path": str(pack_path), "meta": pack.get("meta", {})},
        "amplitude_core_used": True,
        "pdg_baseline_used": False,
        "anti_fallback": antifallback,
        "io": io,
        "pars": asdict(pars),
        "geo": {"geo_applied_in_evolution": geo_applied_in_evolution},
        "integrity": integrity,
        "chi2": {
            "sigma_tot_mb": chi2_sig,
            "rho": chi2_rho,
            "total": chi2_total,
            "ndof": int((sqrts.size if chi2_sig is not None else 0) + (sqrts.size if chi2_rho is not None else 0)),
            "telemetry": chi2_tel,
        },
        "framing": {
            "stability_not_accuracy": True,
            "note": "C4 is HEPData-like IO closure (CSV+cov paths) over the amplitude-core; not a physical-accuracy claim.",
        },
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    if not all(integrity.values()):
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
