#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STRONG C3 runner: GEO inside evolution + response physics locks + χ² closure.

C3 extends C2 by:
  1) integrating GEO *inside* the eikonal evolution law (state-derived, not post-hoc overlay)
  2) validating response maps with WEAK A3-style physics locks (dense + sparse COO)
  3) preserving anti-fallback call-poison + telemetry

This runner consumes the same basic pack shape as C2, plus optional `geo` and
`response.validate` configuration.

This is a closure/integrity deliverable. It is not a claim of physical accuracy.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
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
        raise RuntimeError(f"STRONG C3 anti-fallback: forbidden PDG call: {label}.{attr}")

    setattr(mod, attr, _boom)
    return True


def _maybe_poison_pdg_calls() -> dict:
    active = (
        os.environ.get("STRONG_C3_POISON_PDG_CALLS", "0") == "1"
        or os.environ.get("STRONG_C2_POISON_PDG_CALLS", "0") == "1"
        or os.environ.get("STRONG_C1_POISON_PDG_CALLS", "0") == "1"
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


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _as_float_array(x: Any, *, name: str) -> np.ndarray:
    try:
        a = np.asarray(x, dtype=float)
    except Exception as e:
        raise ValueError(f"Could not parse {name} as float array") from e
    if a.ndim != 1:
        raise ValueError(f"{name} must be 1D, got shape={a.shape}")
    return a


def _validate_response_dense(R: np.ndarray, *, n: int, kind: str) -> dict:
    if R.ndim != 2 or R.shape[0] != n or R.shape[1] != n:
        raise ValueError(f"response.{kind}.dense must be NxN with N={n}; got {R.shape}")
    if not np.all(np.isfinite(R)):
        raise ValueError(f"response.{kind}.dense must be finite")
    if np.min(R) < -1e-15:
        raise ValueError(f"response.{kind}.dense must be nonnegative")

    colsum = np.sum(R, axis=0)
    max_dev = float(np.max(np.abs(colsum - 1.0))) if n else 0.0
    if max_dev > 1e-8:
        raise ValueError(f"response.{kind}.dense must be column-stochastic (max |Σ_col-1|={max_dev})")

    return {"kind": "dense", "column_stochastic": True, "max_colsum_dev": max_dev}


def _validate_response_sparse(coo: dict, *, n: int, kind: str) -> dict:
    ii = np.asarray(coo.get("i", []), dtype=int)
    jj = np.asarray(coo.get("j", []), dtype=int)
    vv = np.asarray(coo.get("v", []), dtype=float)
    if ii.shape != jj.shape or ii.shape != vv.shape:
        raise ValueError(f"response.{kind}.sparse_coo i/j/v must have the same length")
    if vv.size and (not np.all(np.isfinite(vv))):
        raise ValueError(f"response.{kind}.sparse_coo v must be finite")
    if vv.size and float(np.min(vv)) < -1e-15:
        raise ValueError(f"response.{kind}.sparse_coo must be nonnegative")
    if vv.size:
        if np.any(ii < 0) or np.any(ii >= n) or np.any(jj < 0) or np.any(jj >= n):
            raise ValueError(f"response.{kind}.sparse_coo indices out of range")

    # Column-stochastic: sum over rows for each column j equals 1.
    colsum = np.zeros(n, dtype=float)
    if vv.size:
        np.add.at(colsum, jj, vv)
    max_dev = float(np.max(np.abs(colsum - 1.0))) if n else 0.0
    if max_dev > 1e-8:
        raise ValueError(f"response.{kind}.sparse_coo must be column-stochastic (max |Σ_col-1|={max_dev})")

    return {"kind": "sparse_coo", "column_stochastic": True, "max_colsum_dev": max_dev, "nnz": int(vv.size)}


def _apply_response(pred: np.ndarray, response: dict | None, *, kind: str, validate: bool) -> tuple[np.ndarray, dict | None]:
    if not response:
        return pred, None

    n = int(pred.size)

    if "dense" in response:
        R = np.asarray(response["dense"], dtype=float)
        tel = _validate_response_dense(R, n=n, kind=kind) if validate else None
        return np.asarray(R @ pred, dtype=float).reshape(-1), tel

    if "sparse_coo" in response:
        coo = response["sparse_coo"]
        nn = int(coo.get("n", n))
        if nn != n:
            raise ValueError(f"response.{kind}.sparse_coo n={nn} must match pred length {n} (C3 expects square map)")
        tel = _validate_response_sparse(coo, n=n, kind=kind) if validate else None

        ii = np.asarray(coo.get("i", []), dtype=int)
        jj = np.asarray(coo.get("j", []), dtype=int)
        vv = np.asarray(coo.get("v", []), dtype=float)
        out = np.zeros(n, dtype=float)
        if vv.size:
            np.add.at(out, ii, vv * pred[jj])
        return out, tel

    raise ValueError(f"Unknown response.{kind} kind (use dense or sparse_coo)")


def _chi2_from_residuals(resid: np.ndarray, *, unc: np.ndarray | None, cov: np.ndarray | None) -> tuple[float, dict]:
    if cov is not None:
        C = np.asarray(cov, dtype=float)
        if C.ndim != 2 or C.shape[0] != C.shape[1] or C.shape[0] != resid.size:
            raise ValueError("cov must be NxN matching residual length")
        Cinv = np.linalg.pinv(C, rcond=1e-12)
        chi2 = float(resid.T @ Cinv @ resid)
        telemetry = {"kind": "cov", "cond_est": float(np.linalg.cond(C)) if resid.size > 0 else 0.0}
        return chi2, telemetry

    if unc is None:
        raise ValueError("Need either unc (diag) or cov (full covariance) to compute chi2")

    u = np.asarray(unc, dtype=float)
    if u.shape != resid.shape:
        raise ValueError("unc must match residual shape")
    u_safe = np.where(np.abs(u) > 0, u, np.inf)
    pulls = resid / u_safe
    chi2 = float(np.sum(pulls * pulls))
    return chi2, {"kind": "diag"}


def _load_cov_any(cov_spec: Any, *, n: int, pack_dir: Path) -> np.ndarray | None:
    if cov_spec is None:
        return None

    if isinstance(cov_spec, dict) and "matrix" in cov_spec:
        C = np.asarray(cov_spec["matrix"], dtype=float)
        if C.shape != (n, n):
            raise ValueError(f"cov.matrix shape mismatch: expected {(n, n)} got {C.shape}")
        return C

    if isinstance(cov_spec, dict) and "path" in cov_spec:
        p = pack_dir / str(cov_spec["path"])
        df = pd.read_csv(p)
        C = df.to_numpy(dtype=float)
        if C.shape != (n, n):
            raise ValueError(f"cov.path matrix shape mismatch: expected {(n, n)} got {C.shape}")
        return C

    if isinstance(cov_spec, str):
        p = pack_dir / cov_spec
        df = pd.read_csv(p)
        C = df.to_numpy(dtype=float)
        if C.shape != (n, n):
            raise ValueError(f"cov path matrix shape mismatch: expected {(n, n)} got {C.shape}")
        return C

    raise ValueError("Unsupported cov spec")


def main() -> int:
    antifallback = _maybe_poison_pdg_calls()

    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_json", required=True)

    args = ap.parse_args()

    pack_path = Path(args.pack)
    pack_dir = pack_path.parent
    pack = _load_json(str(pack_path))

    scan = pack.get("scan", {})
    sqrts = _as_float_array(scan.get("sqrts_GeV"), name="scan.sqrts_GeV")
    if np.any(~np.isfinite(sqrts)) or np.any(sqrts <= 0):
        raise ValueError("scan.sqrts_GeV must be finite and >0")
    channel = str(scan.get("channel", "pp")).strip().lower()

    model = pack.get("model", {})
    pars = EikonalC1Params(
        s0_GeV2=float(model.get("s0_GeV2", 1.0)),
        dt_max=float(model.get("dt_max", EikonalC1Params().dt_max)),
        sigma_norm_mb=float(model.get("sigma_norm_mb", EikonalC1Params().sigma_norm_mb)),
        b_max=float(model.get("b_max", EikonalC1Params().b_max)),
        nb=int(model.get("nb", EikonalC1Params().nb)),
    )

    geo = pack.get("geo", {})
    geo_A = float(geo.get("A", 0.0))
    geo_template = str(geo.get("template", "cos"))
    geo_phi0 = float(geo.get("phi0", 0.0))
    geo_omega = float(geo.get("omega", 1.0))
    pars = EikonalC1Params(
        **{
            **asdict(pars),
            "geo_A": geo_A,
            "geo_template": geo_template,
            "geo_phi0": geo_phi0,
            "geo_omega": geo_omega,
        }
    )

    geo_applied_in_evolution = bool(abs(geo_A) > 0.0)

    # evolve across scan
    t_arr = t_from_sqrts(sqrts, s0_GeV2=pars.s0_GeV2)
    order = np.argsort(t_arr)
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))

    t_sorted = t_arr[order]
    state = EikonalC1State.initialize(pars)

    F_re = np.empty_like(t_sorted, dtype=float)
    F_im = np.empty_like(t_sorted, dtype=float)
    sigma_pred = np.empty_like(t_sorted, dtype=float)
    rho_pred = np.empty_like(t_sorted, dtype=float)
    chiI_min = np.empty_like(t_sorted, dtype=float)
    chiI_max = np.empty_like(t_sorted, dtype=float)
    Sabs_max = np.empty_like(t_sorted, dtype=float)

    for i, t in enumerate(t_sorted):
        state.advance_to(float(t), pars)
        F = forward_amplitude_from_state(state)
        F_re[i] = float(np.real(F))
        F_im[i] = float(np.imag(F))
        sigma_pred[i] = float(pars.sigma_norm_mb) * F_im[i]
        im_safe = F_im[i] if abs(F_im[i]) > 1e-30 else (1e-30 if F_im[i] >= 0 else -1e-30)
        rho_pred[i] = F_re[i] / im_safe
        chiI_min[i] = float(np.min(state.chi_I))
        chiI_max[i] = float(np.max(state.chi_I))
        Sabs_max[i] = float(np.max(np.exp(-np.asarray(state.chi_I, dtype=float))))

    # restore order
    t_u = t_sorted[inv]
    Fre_u = F_re[inv]
    Fim_u = F_im[inv]
    sig_u = sigma_pred[inv]
    rho_u = rho_pred[inv]
    chiI_min_u = chiI_min[inv]
    chiI_max_u = chiI_max[inv]
    Sabs_u = Sabs_max[inv]

    resp = pack.get("response", {})
    validate = bool(resp.get("validate", True)) if isinstance(resp, dict) else True
    resp_tel: dict[str, Any] = {}

    sig_use, tel = _apply_response(sig_u, resp.get("sigma_tot_mb") if isinstance(resp, dict) else None, kind="sigma_tot_mb", validate=validate)
    if tel is not None:
        resp_tel["sigma_tot_mb"] = tel

    rho_use, tel = _apply_response(rho_u, resp.get("rho") if isinstance(resp, dict) else None, kind="rho", validate=validate)
    if tel is not None:
        resp_tel["rho"] = tel

    data = pack.get("data", {})
    chi2_sig = None
    chi2_rho = None
    chi2_tel: dict[str, Any] = {}

    out_df = pd.DataFrame(
        {
            "sqrts_GeV": sqrts.astype(float),
            "channel": [channel] * int(sqrts.size),
            "t": t_u,
            "F_re": Fre_u,
            "F_im": Fim_u,
            "sigma_tot_pred_mb": sig_use,
            "rho_pred": rho_use,
            "chiI_min": chiI_min_u,
            "chiI_max": chiI_max_u,
            "S_abs_max": Sabs_u,
        }
    )

    if "sigma_tot_mb" in data:
        y = _as_float_array(data["sigma_tot_mb"].get("y"), name="data.sigma_tot_mb.y")
        out_df["sigma_tot_data_mb"] = y
        out_df["sigma_tot_resid_mb"] = y - out_df["sigma_tot_pred_mb"].to_numpy(float)
        unc = data["sigma_tot_mb"].get("unc")
        cov = _load_cov_any(data["sigma_tot_mb"].get("cov"), n=y.size, pack_dir=pack_dir)
        chi2_sig, tel = _chi2_from_residuals(out_df["sigma_tot_resid_mb"].to_numpy(float), unc=_as_float_array(unc, name="data.sigma_tot_mb.unc") if unc is not None else None, cov=cov)
        chi2_tel["sigma_tot_mb"] = tel

    if "rho" in data:
        y = _as_float_array(data["rho"].get("y"), name="data.rho.y")
        out_df["rho_data"] = y
        out_df["rho_resid"] = y - out_df["rho_pred"].to_numpy(float)
        unc = data["rho"].get("unc")
        cov = _load_cov_any(data["rho"].get("cov"), n=y.size, pack_dir=pack_dir)
        chi2_rho, tel = _chi2_from_residuals(out_df["rho_resid"].to_numpy(float), unc=_as_float_array(unc, name="data.rho.unc") if unc is not None else None, cov=cov)
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

    summary = {
        "pack": {"path": str(pack_path), "meta": pack.get("meta", {})},
        "amplitude_core_used": True,
        "pdg_baseline_used": False,
        "anti_fallback": antifallback,
        "pars": asdict(pars),
        "geo": {
            "geo_applied_in_evolution": geo_applied_in_evolution,
            "A": geo_A,
            "template": geo_template,
            "phi0": geo_phi0,
            "omega": geo_omega,
        },
        "response": {"validate": validate, "telemetry": resp_tel},
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
            "note": "C3 provides state-derived GEO integration + response physics locks + χ² closure; it is not a claim of physical-model accuracy.",
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
