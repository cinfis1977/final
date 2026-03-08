#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STRONG C2 runner: amplitude-core outputs → pack/observable closure + χ²/cov.

This is the STRONG analogue of WEAK's “dynamics → pipeline closure” line.
It consumes a small pack JSON with an energy scan and (optional) data/covariance,
computes σ_tot(s) and ρ(s) from the STRONG C1 amplitude core, then computes χ².

Anti-fallback
-------------
If env var STRONG_C1_POISON_PDG_CALLS=1 or STRONG_C2_POISON_PDG_CALLS=1 is set,
this runner imports known PDG/COMPETE baseline harness modules and overwrites
their *baseline-eval* functions with stubs that raise.

C2 framing
----------
C2 provides numerical/pipeline closure (pack→pred→residual→χ²). It is not a claim
of physical accuracy.

Pack format (minimal)
---------------------
{
  "meta": {"name": "..."},
  "scan": {"sqrts_GeV": [7.0, 20.0, 200.0, 13000.0], "channel": "pp"},
  "model": {"s0_GeV2": 1.0, "dt_max": 0.05, "nb": 600, "b_max": 20.0},
  "data": {
    "sigma_tot_mb": {"y": [..], "unc": [..]},
    "rho": {"y": [..], "unc": [..]}
  },
  "response": {
    "sigma_tot_mb": {"dense": [[..NxN..]]},
    "rho": {"sparse_coo": {"n": N, "i": [...], "j": [...], "v": [...]}}
  }
}

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
        raise RuntimeError(f"STRONG C2 anti-fallback: forbidden PDG call: {label}.{attr}")

    setattr(mod, attr, _boom)
    return True


def _maybe_poison_pdg_calls() -> dict:
    active = (
        os.environ.get("STRONG_C2_POISON_PDG_CALLS", "0") == "1"
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


def _apply_response(pred: np.ndarray, response: dict | None) -> np.ndarray:
    if not response:
        return pred

    if "dense" in response:
        R = np.asarray(response["dense"], dtype=float)
        if R.ndim != 2:
            raise ValueError("response.dense must be 2D")
        if R.shape[1] != pred.size:
            raise ValueError(f"response.dense has shape {R.shape} but pred has length {pred.size}")
        return np.asarray(R @ pred, dtype=float).reshape(-1)

    if "sparse_coo" in response:
        coo = response["sparse_coo"]
        n = int(coo.get("n", pred.size))
        ii = np.asarray(coo.get("i", []), dtype=int)
        jj = np.asarray(coo.get("j", []), dtype=int)
        vv = np.asarray(coo.get("v", []), dtype=float)
        if ii.shape != jj.shape or ii.shape != vv.shape:
            raise ValueError("response.sparse_coo i/j/v must have the same length")
        if pred.size != n:
            raise ValueError(f"response.sparse_coo n={n} must match pred length {pred.size} (C2 expects square response)")
        out = np.zeros(n, dtype=float)
        if vv.size:
            if np.any(ii < 0) or np.any(ii >= n) or np.any(jj < 0) or np.any(jj >= n):
                raise ValueError("response.sparse_coo indices out of range")
            # out[i] += v * pred[j]
            np.add.at(out, ii, vv * pred[jj])
        return out

    raise ValueError("Unknown response kind (use dense or sparse_coo)")


def _chi2_from_residuals(resid: np.ndarray, *, unc: np.ndarray | None, cov: np.ndarray | None) -> tuple[float, dict]:
    if cov is not None:
        C = np.asarray(cov, dtype=float)
        if C.ndim != 2 or C.shape[0] != C.shape[1] or C.shape[0] != resid.size:
            raise ValueError("cov must be NxN matching residual length")
        # Use pseudo-inverse for stability (packs may be only semidefinite).
        Cinv = np.linalg.pinv(C, rcond=1e-12)
        chi2 = float(resid.T @ Cinv @ resid)
        telemetry = {
            "kind": "cov",
            "cond_est": float(np.linalg.cond(C)) if resid.size > 0 else 0.0,
        }
        return chi2, telemetry

    if unc is None:
        raise ValueError("Need either unc (diag) or cov (full covariance) to compute chi2")

    u = np.asarray(unc, dtype=float)
    if u.shape != resid.shape:
        raise ValueError("unc must match residual shape")
    u_safe = np.where(np.abs(u) > 0, u, np.inf)
    pulls = resid / u_safe
    chi2 = float(np.sum(pulls * pulls))
    telemetry = {"kind": "diag"}
    return chi2, telemetry


def _extract_points(pack: dict) -> tuple[np.ndarray, str]:
    if "points" in pack:
        pts = pack["points"]
        if not isinstance(pts, list) or not pts:
            raise ValueError("pack.points must be a non-empty list")
        sq = np.asarray([p.get("sqrts_GeV") for p in pts], dtype=float)
        if np.any(~np.isfinite(sq)) or np.any(sq <= 0):
            raise ValueError("All points.sqrts_GeV must be finite and >0")
        channel = str(pts[0].get("channel", pack.get("scan", {}).get("channel", "pp"))).strip().lower()
        return sq, channel

    scan = pack.get("scan", {})
    sq = _as_float_array(scan.get("sqrts_GeV"), name="scan.sqrts_GeV")
    if np.any(~np.isfinite(sq)) or np.any(sq <= 0):
        raise ValueError("scan.sqrts_GeV must be finite and >0")
    channel = str(scan.get("channel", "pp")).strip().lower()
    return sq, channel


def _extract_data(pack: dict, sqrts: np.ndarray) -> dict:
    n = int(sqrts.size)

    data: dict = {}

    if "points" in pack:
        pts = pack["points"]
        # Allow missing data fields.
        sig = np.asarray([p.get("sigma_tot_mb", np.nan) for p in pts], dtype=float)
        sig_u = np.asarray([p.get("sigma_tot_unc_mb", np.nan) for p in pts], dtype=float)
        rho = np.asarray([p.get("rho", np.nan) for p in pts], dtype=float)
        rho_u = np.asarray([p.get("rho_unc", np.nan) for p in pts], dtype=float)

        if np.all(np.isfinite(sig)):
            data["sigma_tot_mb"] = {"y": sig, "unc": sig_u if np.all(np.isfinite(sig_u)) else None}
        if np.all(np.isfinite(rho)):
            data["rho"] = {"y": rho, "unc": rho_u if np.all(np.isfinite(rho_u)) else None}
        return data

    d = pack.get("data", {})
    if "sigma_tot_mb" in d:
        y = _as_float_array(d["sigma_tot_mb"].get("y"), name="data.sigma_tot_mb.y")
        if y.size != n:
            raise ValueError("data.sigma_tot_mb.y length mismatch")
        unc = d["sigma_tot_mb"].get("unc")
        data["sigma_tot_mb"] = {"y": y, "unc": _as_float_array(unc, name="data.sigma_tot_mb.unc") if unc is not None else None, "cov": d["sigma_tot_mb"].get("cov")}

    if "rho" in d:
        y = _as_float_array(d["rho"].get("y"), name="data.rho.y")
        if y.size != n:
            raise ValueError("data.rho.y length mismatch")
        unc = d["rho"].get("unc")
        data["rho"] = {"y": y, "unc": _as_float_array(unc, name="data.rho.unc") if unc is not None else None, "cov": d["rho"].get("cov")}

    return data


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

    # Allow passing a bare relative path.
    if isinstance(cov_spec, str):
        p = pack_dir / cov_spec
        df = pd.read_csv(p)
        C = df.to_numpy(dtype=float)
        if C.shape != (n, n):
            raise ValueError(f"cov path matrix shape mismatch: expected {(n, n)} got {C.shape}")
        return C

    raise ValueError("Unsupported cov spec (use {matrix:[..]} or {path:" ") or string path)")


def main() -> int:
    antifallback = _maybe_poison_pdg_calls()

    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True, help="Path to STRONG C2 pack JSON")
    ap.add_argument("--out_csv", required=True, help="Output CSV (pred/data/resid)")
    ap.add_argument("--out_json", required=True, help="Output JSON summary (chi2 + telemetry)")

    # Override knobs (optional): these are for e2e/regression convenience.
    ap.add_argument("--dt_max", type=float, default=None)
    ap.add_argument("--nb", type=int, default=None)

    args = ap.parse_args()

    pack_path = Path(args.pack)
    pack_dir = pack_path.parent
    pack = _load_json(str(pack_path))

    sqrts, channel = _extract_points(pack)
    data = _extract_data(pack, sqrts)

    model = pack.get("model", {})
    pars = EikonalC1Params(
        s0_GeV2=float(model.get("s0_GeV2", 1.0)),
        dt_max=float(model.get("dt_max", EikonalC1Params().dt_max)),
        sigma_norm_mb=float(model.get("sigma_norm_mb", EikonalC1Params().sigma_norm_mb)),
        b_max=float(model.get("b_max", EikonalC1Params().b_max)),
        nb=int(model.get("nb", EikonalC1Params().nb)),
    )

    if args.dt_max is not None:
        pars = EikonalC1Params(**{**asdict(pars), "dt_max": float(args.dt_max)})
    if args.nb is not None:
        pars = EikonalC1Params(**{**asdict(pars), "nb": int(args.nb)})

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

    # Restore original order
    t_u = t_sorted[inv]
    Fre_u = F_re[inv]
    Fim_u = F_im[inv]
    sig_u = sigma_pred[inv]
    rho_u = rho_pred[inv]
    chiI_min_u = chiI_min[inv]
    chiI_max_u = chiI_max[inv]
    Sabs_u = Sabs_max[inv]

    # Apply optional response transforms (acceptance/eff/smearing are all linear maps here).
    resp = pack.get("response", {})
    sig_use = _apply_response(sig_u, resp.get("sigma_tot_mb")) if resp else sig_u
    rho_use = _apply_response(rho_u, resp.get("rho")) if resp else rho_u

    # Optional per-observable multiplicative factors.
    factors = pack.get("factors", {})
    if "sigma_tot_mb" in factors:
        f = _as_float_array(factors["sigma_tot_mb"], name="factors.sigma_tot_mb")
        if f.size != sig_use.size:
            raise ValueError("factors.sigma_tot_mb length mismatch")
        sig_use = sig_use * f
    if "rho" in factors:
        f = _as_float_array(factors["rho"], name="factors.rho")
        if f.size != rho_use.size:
            raise ValueError("factors.rho length mismatch")
        rho_use = rho_use * f

    # Compute chi2 if data present.
    chi2_sig = None
    chi2_rho = None
    chi2_total = None
    chi2_tel: dict[str, Any] = {}

    if "sigma_tot_mb" in data:
        y = np.asarray(data["sigma_tot_mb"]["y"], dtype=float)
        resid = y - sig_use
        unc = data["sigma_tot_mb"].get("unc")
        cov = _load_cov_any(data["sigma_tot_mb"].get("cov"), n=y.size, pack_dir=pack_dir)
        chi2_sig, tel = _chi2_from_residuals(resid, unc=unc, cov=cov)
        chi2_tel["sigma_tot_mb"] = tel

    if "rho" in data:
        y = np.asarray(data["rho"]["y"], dtype=float)
        resid = y - rho_use
        unc = data["rho"].get("unc")
        cov = _load_cov_any(data["rho"].get("cov"), n=y.size, pack_dir=pack_dir)
        chi2_rho, tel = _chi2_from_residuals(resid, unc=unc, cov=cov)
        chi2_tel["rho"] = tel

    if chi2_sig is not None or chi2_rho is not None:
        chi2_total = float((chi2_sig or 0.0) + (chi2_rho or 0.0))

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
        out_df["sigma_tot_data_mb"] = np.asarray(data["sigma_tot_mb"]["y"], dtype=float)
        out_df["sigma_tot_resid_mb"] = out_df["sigma_tot_data_mb"].to_numpy(float) - out_df["sigma_tot_pred_mb"].to_numpy(float)
        if data["sigma_tot_mb"].get("unc") is not None:
            out_df["sigma_tot_unc_mb"] = np.asarray(data["sigma_tot_mb"]["unc"], dtype=float)
            u = out_df["sigma_tot_unc_mb"].to_numpy(float)
            u_safe = np.where(np.abs(u) > 0, u, np.nan)
            out_df["sigma_tot_pull"] = out_df["sigma_tot_resid_mb"].to_numpy(float) / u_safe

    if "rho" in data:
        out_df["rho_data"] = np.asarray(data["rho"]["y"], dtype=float)
        out_df["rho_resid"] = out_df["rho_data"].to_numpy(float) - out_df["rho_pred"].to_numpy(float)
        if data["rho"].get("unc") is not None:
            out_df["rho_unc"] = np.asarray(data["rho"]["unc"], dtype=float)
            u = out_df["rho_unc"].to_numpy(float)
            u_safe = np.where(np.abs(u) > 0, u, np.nan)
            out_df["rho_pull"] = out_df["rho_resid"].to_numpy(float) / u_safe

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
            "note": "χ² closure here is a pipeline/integrity deliverable; it is not a claim of physical-model accuracy.",
        },
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    # Fail fast if integrity fails.
    if not all(integrity.values()):
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
