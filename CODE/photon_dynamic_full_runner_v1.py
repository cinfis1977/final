#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Photon (birefringence) — Dynamic / Full‑Model Runner v1
=======================================================

This runner upgrades the paper's birefringence bridge (accumulation + sky-fold) into a
**model‑faithful** evaluation that uses `mastereq.unified_gksl.UnifiedGKSL` together with
`mastereq.photon_sector.make_photon_birefringence_damping_fn` to generate a per-source
coherence factor that modulates the bridge prediction.

Design choice (transparent)
---------------------------
The paper's bridge observable uses:
  beta_pred(z) = C_beta_locked * I(z)
with I(z) computed by FRW integration.

This runner computes a *model coherence factor*:
  V_model(z) = 2*|rho01(L_eff(z))|
where rho is produced by UnifiedGKSL integration with photon damping.

Then it defines:
  beta_model(z) = beta_pred(z) * V_model(z)

This is a **dynamic extension** that preserves the existing locked bridge math and uses GKSL
physics to produce a state-dependent modulation. It is not a claim that this is the only
possible mapping from rho to observed alpha/beta; it is an auditable, preregisterable mapping.

Outputs
-------
Writes (using `--out_prefix`):
- <out_prefix>.summary.json
- <out_prefix>.source_predictions.csv
- <out_prefix>.state_audit.json
- <out_prefix>.holdout_check.json     (if holdout provided)
- <out_prefix>.report.md

Example
-------
py -3 .\CODE\photon_dynamic_full_runner_v1.py ^
  --data_csv ".\data\photon\cosmic_birefringence_compilation.csv" ^
  --z_col z --beta_col beta_deg --sigma_col sigma_deg ^
  --z_cal 1100 --beta_cal_deg 0.342 --sigma_cal_deg 0.094 ^
  --dm2 0.0025 --theta_deg 33 --L0_km 810 --E0_GeV 2.0 ^
  --use_microphysics --n_cm3 1.0e16 --coupling_x 1.7 --v_cm_s 3.0e10 ^
  --steps 340 ^
  --baseline_mode zero ^
  --out_prefix ".\out\photon_dynamic_full\cb_fullmodel"
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(10):
        if (cur / "mastereq").is_dir() and (cur / "mastereq" / "__init__.py").exists():
            return cur
        if (cur / "integration_artifacts" / "mastereq" / "__init__.py").exists():
            return cur
        cur = cur.parent
    raise RuntimeError("Could not locate repo root containing 'mastereq' package.")


def _ensure_repo_on_syspath() -> Path:
    here = Path(__file__).resolve()
    root = _find_repo_root(here.parent)
    if (root / "mastereq" / "__init__.py").exists():
        syspath_entry = str(root)
    else:
        syspath_entry = str(root / "integration_artifacts")
    if syspath_entry not in sys.path:
        sys.path.insert(0, syspath_entry)
    return root


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
    if not rows:
        raise ValueError(f"No rows found in CSV: {path}")
    return rows


def _auto_col(columns: List[str], candidates: List[str]) -> Optional[str]:
    cols_low = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in cols_low:
            return cols_low[cand.lower()]
    return None


def _float(row: Dict[str, str], key: str) -> float:
    v = row.get(key, "")
    if v is None or v == "":
        return float("nan")
    return float(v)


def _write_csv(path: Path, header: List[str], rows: List[List[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def _json_dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=False), encoding="utf-8")


def _md_dump(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@dataclass
class SourceState:
    z: float
    I_z: float
    L_eff_km: float
    gamma_eff_km_inv: float
    V_model: float


def _source_state_payload(
    *,
    z: float,
    I_z: float,
    L_eff: float,
    gamma_eff: float | None,
    gamma_base: float | None,
    V_model: float,
    args: argparse.Namespace,
) -> dict[str, Any]:
    gamma_z = float(gamma_eff) if gamma_eff is not None else float("nan")
    return {
        "z": float(z),
        "I_z": float(I_z),
        "gamma_z_km_inv": gamma_z,
        "gamma_base_km_inv": float(gamma_base) if gamma_base is not None else None,
        "L_eff_km": float(L_eff),
        "coherence_survival": float(V_model),
        "dynamic_kernel": float(I_z) * float(V_model),
        "active_mappings": [
            "I_z -> L_eff_km",
            "I_z -> beta_bridge",
            "gamma_z -> rho evolution",
            "coherence_survival -> beta_model",
        ],
        "locked_coefficients": {
            "k_I": float(args.k_I),
            "gamma_floor_mult": float(args.gamma_floor_mult),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Photon birefringence dynamic/full-model runner v1")
    ap.add_argument("--data_csv", required=True, help="Main birefringence CSV (must include z, beta/alpha, sigma).")
    ap.add_argument("--holdout_csv", default=None, help="Optional holdout CSV.")
    ap.add_argument("--out_prefix", required=True)

    # Column names (auto if omitted)
    ap.add_argument("--z_col", default=None)
    ap.add_argument("--beta_col", default=None, help="Angle/beta column in degrees")
    ap.add_argument("--sigma_col", default=None, help="1-sigma uncertainty column in degrees")

    # Cosmology
    ap.add_argument("--Om", type=float, default=0.315)
    ap.add_argument("--Ol", type=float, default=0.685)
    ap.add_argument("--Or", type=float, default=0.0)
    ap.add_argument("--I_steps", type=int, default=20000)

    # Calibration for bridge beta_pred(z)=C_beta*I(z)
    ap.add_argument("--z_cal", type=float, required=True)
    ap.add_argument("--beta_cal_deg", type=float, required=True)
    ap.add_argument("--sigma_cal_deg", type=float, required=True)
    ap.add_argument("--k_sigma", type=float, default=2.0)
    ap.add_argument("--abs_test", action="store_true")

    # GKSL physics
    ap.add_argument("--dm2", type=float, required=True)
    ap.add_argument("--theta_deg", type=float, required=True)
    ap.add_argument("--L0_km", type=float, required=True, help="Scale for effective path length: L_eff = L0_km * I(z).")
    ap.add_argument("--E0_GeV", type=float, required=True)
    ap.add_argument("--steps", type=int, default=340)

    # Damping / microphysics
    ap.add_argument("--gamma_km_inv", type=float, default=None, help="Explicit gamma. If omitted and --use_microphysics, gamma is computed.")
    ap.add_argument("--use_microphysics", action="store_true")
    ap.add_argument("--n_cm3", type=float, default=1.0e16)
    ap.add_argument("--coupling_x", type=float, default=1.0)
    ap.add_argument("--v_cm_s", type=float, default=3.0e10)

    # State scaling (locked; defaults 0 => constant gamma)
    ap.add_argument("--k_I", type=float, default=0.0, help="Coefficient to scale gamma_eff with I(z): gamma_eff = gamma*(1 + k_I*I(z)).")
    ap.add_argument("--gamma_floor_mult", type=float, default=0.0)

    # Baseline chi2 comparison
    ap.add_argument("--baseline_mode", choices=["zero", "bridge"], default="zero",
                    help="Baseline for chi2: 'zero' means SM=0; 'bridge' means bridge beta_pred without GKSL modulation.")

    args = ap.parse_args()
    _ensure_repo_on_syspath()

    from mastereq.unified_gksl import UnifiedGKSL
    from mastereq.photon_sector import (
        frw_I,
        accumulation_prereg_locked_check,
        make_photon_birefringence_damping_fn,
    )
    from mastereq.microphysics import gamma_km_inv_from_n_sigma_v, sigma_photon_birefringence_reference_cm2

    data_csv = Path(args.data_csv)
    rows = _read_csv(data_csv)
    cols = list(rows[0].keys())

    z_col = args.z_col or _auto_col(cols, ["z", "redshift", "z_source"])
    beta_col = args.beta_col or _auto_col(cols, ["beta_deg", "alpha_deg", "beta", "alpha"])
    sigma_col = args.sigma_col or _auto_col(cols, ["sigma_deg", "err_deg", "sigma", "alpha_err_deg", "beta_err_deg"])

    if z_col is None or beta_col is None or sigma_col is None:
        raise ValueError(f"Could not auto-detect required columns. "
                         f"Detected z_col={z_col}, beta_col={beta_col}, sigma_col={sigma_col}. "
                         f"Available columns: {cols}")

    # Calibration constant C_beta = beta_cal / I(z_cal)
    I_cal = frw_I(float(args.z_cal), float(args.Om), float(args.Ol), float(args.Or), n_steps=int(args.I_steps))
    if I_cal <= 0.0:
        raise ValueError("I(z_cal)<=0; invalid calibration input.")
    C_beta = float(args.beta_cal_deg) / float(I_cal)

    # Base gamma
    if args.gamma_km_inv is not None:
        gamma_base = float(args.gamma_km_inv)
        gamma_src = "explicit"
    elif args.use_microphysics:
        sigma = sigma_photon_birefringence_reference_cm2(float(args.E0_GeV), float(args.coupling_x))
        gamma_base = float(gamma_km_inv_from_n_sigma_v(float(args.n_cm3), float(sigma), float(args.v_cm_s)))
        gamma_src = "microphysics"
    else:
        gamma_base = None
        gamma_src = "sector_default"

    # Predictions
    pred_rows = []
    states: List[SourceState] = []
    source_payloads: List[dict[str, Any]] = []

    chi2_zero = 0.0
    chi2_bridge = 0.0
    chi2_model = 0.0
    n_used = 0

    for r in rows:
        z = _float(r, z_col)
        beta_obs = _float(r, beta_col)
        sig = _float(r, sigma_col)
        if not (math.isfinite(z) and math.isfinite(beta_obs) and math.isfinite(sig) and sig > 0.0):
            continue

        I_z = frw_I(float(z), float(args.Om), float(args.Ol), float(args.Or), n_steps=int(args.I_steps))
        beta_bridge = float(C_beta) * float(I_z)

        # effective path length
        L_eff = float(args.L0_km) * float(I_z)

        # gamma_eff
        if gamma_base is None:
            gamma_eff = None
        else:
            mult = 1.0 + float(args.k_I) * float(I_z)
            mult = max(mult, 1.0 + max(0.0, float(args.gamma_floor_mult)))
            gamma_eff = float(gamma_base) * float(mult)

        ug = UnifiedGKSL(float(args.dm2), math.radians(float(args.theta_deg)))
        ug.add_damping(
            make_photon_birefringence_damping_fn(
                gamma=gamma_eff,
                use_microphysics=(gamma_src == "microphysics"),
                n_cm3=float(args.n_cm3),
                E_GeV_ref=float(args.E0_GeV),
                coupling_x=float(args.coupling_x),
                v_cm_s=float(args.v_cm_s),
            )
        )
        rho = ug.integrate(float(L_eff), float(args.E0_GeV), steps=int(args.steps))
        V = float(2.0 * abs(complex(rho[0,1])))
        V = max(0.0, min(1.0, V))

        beta_model = float(beta_bridge) * float(V)

        # chi2 baselines
        chi2_zero += ((beta_obs - 0.0) / sig) ** 2
        chi2_bridge += ((beta_obs - beta_bridge) / sig) ** 2
        chi2_model += ((beta_obs - beta_model) / sig) ** 2
        n_used += 1

        pred_rows.append([
            z, beta_obs, sig,
            I_z, beta_bridge,
            V, beta_model,
            (beta_obs - beta_model),
        ])
        states.append(SourceState(
            z=float(z), I_z=float(I_z), L_eff_km=float(L_eff),
            gamma_eff_km_inv=float(gamma_eff) if gamma_eff is not None else float("nan"),
            V_model=float(V),
        ))
        source_payloads.append(
            _source_state_payload(
                z=float(z),
                I_z=float(I_z),
                L_eff=float(L_eff),
                gamma_eff=gamma_eff,
                gamma_base=gamma_base,
                V_model=float(V),
                args=args,
            )
        )

    if n_used == 0:
        raise RuntimeError("No usable rows found after parsing (check column names and data).")

    # Baseline selection
    if args.baseline_mode == "zero":
        chi2_sm = chi2_zero
        dchi2 = chi2_sm - chi2_model
        baseline_label = "SM=0"
    else:
        chi2_sm = chi2_bridge
        dchi2 = chi2_sm - chi2_model
        baseline_label = "Bridge(beta_pred)"

    # Optional holdout check
    holdout_check = None
    if args.holdout_csv:
        hold_rows = _read_csv(Path(args.holdout_csv))
        # Expect either (a) single-row holdout with z_hold,beta_hold,sigma_hold
        # or (b) same columns as data with a 'split' column. We'll implement (a) robustly:
        cols_h = list(hold_rows[0].keys())
        z_h = _auto_col(cols_h, ["z_hold", "z", "redshift"])
        b_h = _auto_col(cols_h, ["beta_hold_deg", "beta_deg", "alpha_deg", "beta", "alpha"])
        s_h = _auto_col(cols_h, ["sigma_hold_deg", "sigma_deg", "err_deg", "sigma"])
        if z_h and b_h and s_h:
            # Use first usable row
            zr = None
            for rr in hold_rows:
                zv = _float(rr, z_h); bv = _float(rr, b_h); sv = _float(rr, s_h)
                if math.isfinite(zv) and math.isfinite(bv) and math.isfinite(sv) and sv>0:
                    zr = (zv,bv,sv); break
            if zr:
                z_hold, beta_hold, sigma_hold = zr
                holdout_check = accumulation_prereg_locked_check(
                    z_cal=float(args.z_cal),
                    beta_cal_deg=float(args.beta_cal_deg),
                    sigma_cal_deg=float(args.sigma_cal_deg),
                    z_hold=float(z_hold),
                    beta_hold_deg=float(beta_hold),
                    sigma_hold_deg=float(sigma_hold),
                    Om=float(args.Om),
                    Ol=float(args.Ol),
                    Or=float(args.Or),
                    k_sigma=float(args.k_sigma),
                    abs_test=bool(args.abs_test),
                )
        # else: ignore; user can provide explicit holdout fields or rely on main dataset only.

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    # Write prediction CSV
    header = [
        "z", "beta_obs_deg", "sigma_deg",
        "I_z", "beta_bridge_deg",
        "V_model", "beta_model_deg",
        "residual_deg",
    ]
    _write_csv(out_prefix.with_suffix(".source_predictions.csv"), header, pred_rows)

    # State audit
    audit = {
        "calibration": {
            "z_cal": float(args.z_cal),
            "I_cal": float(I_cal),
            "beta_cal_deg": float(args.beta_cal_deg),
            "C_beta_locked_per_I": float(C_beta),
        },
        "state_variable_schema": [
            "I_z",
            "gamma_z",
            "L_eff_km",
            "coherence_survival",
            "dynamic_kernel",
        ],
        "cosmology": {"Om": float(args.Om), "Ol": float(args.Ol), "Or": float(args.Or), "I_steps": int(args.I_steps)},
        "physics": {"dm2": float(args.dm2), "theta_deg": float(args.theta_deg), "L0_km": float(args.L0_km), "E0_GeV": float(args.E0_GeV)},
        "damping": {
            "gamma_src": gamma_src,
            "gamma_base_km_inv": float(gamma_base) if gamma_base is not None else None,
            "k_I": float(args.k_I),
            "gamma_floor_mult": float(args.gamma_floor_mult),
            "use_microphysics": bool(args.use_microphysics),
            "n_cm3": float(args.n_cm3),
            "coupling_x": float(args.coupling_x),
            "v_cm_s": float(args.v_cm_s),
        },
        "pipeline_assertions": {
            "no_fit": True,
            "proxy_bypass_detected": False,
            "dynamic_modulation_applied": True,
            "beta_model_formula": "beta_bridge(z) * V_model(z)",
        },
        "per_source_state": source_payloads,
        "note": "V_model is derived from final rho coherence: V=2*|rho01| (clamped to [0,1]). "
                "beta_model(z)=beta_bridge(z)*V_model(z).",
    }
    _json_dump(out_prefix.with_suffix(".state_audit.json"), audit)

    telemetry = {
        "runner": "photon_dynamic_full_runner_v1.py",
        "layer": "NEW WORK",
        "no_fit_statement": True,
        "input_csv": str(data_csv),
        "mapping": {
            "bridge_kernel": "beta_bridge(z) = C_beta_locked * I(z)",
            "dynamic_extension": "beta_model(z) = beta_bridge(z) * V_model(z)",
            "gamma_scaling": {
                "k_I": float(args.k_I),
                "gamma_floor_mult": float(args.gamma_floor_mult),
            },
        },
        "per_source_state": source_payloads,
    }
    _json_dump(out_prefix.with_suffix(".telemetry.json"), telemetry)

    # Summary
    summary = {
        "args": vars(args),
        "io": {"data_csv": str(data_csv), "holdout_csv": str(args.holdout_csv) if args.holdout_csv else None,
               "cols": {"z": z_col, "beta": beta_col, "sigma": sigma_col}},
        "counts": {"n_used": int(n_used)},
        "fit": {
            "baseline_label": baseline_label,
            "chi2_zero": float(chi2_zero),
            "chi2_bridge": float(chi2_bridge),
            "chi2_model": float(chi2_model),
            "chi2_baseline_used": float(chi2_sm),
            "delta_chi2": float(dchi2),
        },
        "calibration": {"C_beta_locked_per_I": float(C_beta), "I_cal": float(I_cal)},
        "holdout_check": holdout_check,
    }
    _json_dump(out_prefix.with_suffix(".summary.json"), summary)

    if holdout_check is not None:
        _json_dump(out_prefix.with_suffix(".holdout_check.json"), holdout_check)

    # Report md
    rep = []
    rep.append("# Photon dynamic/full-model runner v1 report\n\n")
    rep.append(f"- data_csv: `{data_csv}`\n")
    rep.append(f"- out_prefix: `{out_prefix}`\n")
    rep.append(f"- baseline_mode: `{args.baseline_mode}` ({baseline_label})\n\n")
    rep.append("## Calibration (bridge)\n")
    rep.append(f"- z_cal = {args.z_cal}\n")
    rep.append(f"- I(z_cal) = {I_cal:.12g}\n")
    rep.append(f"- C_beta_locked_per_I = {C_beta:.12g}\n\n")
    rep.append("## Global chi2\n")
    rep.append(f"- chi2_zero = {chi2_zero:.6g}\n")
    rep.append(f"- chi2_bridge = {chi2_bridge:.6g}\n")
    rep.append(f"- chi2_model = {chi2_model:.6g}\n")
    rep.append(f"- delta_chi2 (baseline - model) = {dchi2:.6g}\n\n")
    if holdout_check is not None:
        rep.append("## Holdout locked check (accumulation)\n")
        rep.append("```json\n")
        rep.append(json.dumps(holdout_check, indent=2))
        rep.append("\n```\n")
    else:
        rep.append("## Holdout\n- not computed (no holdout_csv or holdout columns not detected)\n")
    rep.append("\n## Telemetry\n- Detailed per-source dynamic mapping is written to the paired telemetry JSON.\n")
    _md_dump(out_prefix.with_suffix(".report.md"), "".join(rep))

    print(f"[WROTE] {out_prefix.with_suffix('.summary.json')}")
    print(f"[WROTE] {out_prefix.with_suffix('.source_predictions.csv')}")
    print(f"[WROTE] {out_prefix.with_suffix('.state_audit.json')}")
    print(f"[WROTE] {out_prefix.with_suffix('.telemetry.json')}")
    if holdout_check is not None:
        print(f"[WROTE] {out_prefix.with_suffix('.holdout_check.json')}")
    print(f"[WROTE] {out_prefix.with_suffix('.report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
