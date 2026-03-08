#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH GKSL leave-one-run-out runner — DROP-IN v1

Purpose
-------
Automate a stricter predictive test loop:
- leave one real run out,
- fit a GKSL-modulated slot profile on the remaining real runs,
- score only the holdout run windows,
- aggregate `J_data` vs `J_model` into one CSV/MD.

This creates a cleaner scientific separation than calibrated closure.
It still remains a bridge because slot6 seeds are empirical.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List


KEYS = ("00", "01", "10", "11")


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_counts_csv(path: Path) -> Dict[str, Any]:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        rows = list(r)
    total = 0
    per = {}
    for row in rows:
        k = f"{int(row.get('a_set', row.get('a', 0)))}{int(row.get('b_set', row.get('b', 0)))}"
        tvi = int(float(row.get("trials_valid", row.get("trials", row.get("n", "0")))))
        total += tvi
        per[k] = tvi
    return {"total_valid_trials": total, "per_setting_trials": per}


def _extract_run_id(summary: Dict[str, Any], summary_path: Path) -> str:
    h5 = str(summary.get("h5_path", ""))
    base = os.path.basename(h5)
    m = re.search(r"(\d{2}_\d{2})", base)
    if m:
        return m.group(1)
    m = re.search(r"run(\d{2}_\d{2})", summary_path.name)
    if m:
        return m.group(1)
    return summary_path.stem


def _slots_spec(slots: List[int]) -> str:
    if not slots:
        return ""
    slots = sorted(slots)
    if len(slots) == 1:
        return f"{slots[0]}"
    if slots == list(range(slots[0], slots[-1] + 1)):
        return f"{slots[0]}-{slots[-1]}"
    return ",".join(str(s) for s in slots)


def _window_label(slots: List[int]) -> str:
    if not slots:
        return "unknown"
    if len(slots) == 1:
        return f"slot{slots[0]}"
    return f"slots{_slots_spec(slots).replace(',', '_')}"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def _clip01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def _compute_J_from_probs(N: Dict[str, int], probs: Dict[str, Any]) -> Dict[str, Any]:
    P_pp = probs["P_pp"]
    if "P_p0" in probs and "P_0p" in probs:
        P_p0 = probs["P_p0"]
        P_0p = probs["P_0p"]
    else:
        P_A = probs.get("P_A_plus")
        P_B = probs.get("P_B_plus")
        if P_A is None or P_B is None:
            raise ValueError("Provider must return either (P_p0,P_0p) or (P_A_plus,P_B_plus) with P_pp.")
        P_p0, P_0p = {}, {}
        for k in KEYS:
            P_p0[k] = _clip01(float(P_A[k]) - float(P_pp[k]))
            P_0p[k] = _clip01(float(P_B[k]) - float(P_pp[k]))
    J = N["00"] * float(P_pp["00"]) - N["01"] * float(P_p0["01"]) - N["10"] * float(P_0p["10"]) - N["11"] * float(P_pp["11"])
    return {"J_model": float(J), "P_pp": P_pp, "P_p0": P_p0, "P_0p": P_0p}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--provider", default=r".\CODE\ch_model_prob_provider_v1_GKSL_PREDICTIVE_V2_DROPIN.py")
    ap.add_argument("--init_module", default=r".\CODE\nist_ch_init_gksl_predictive_v2_DROPIN.py")
    ap.add_argument("--out_csv", default=r".\out\nist_ch\MODEL_SCORECARD_GKSL_LOO_V1.csv")
    ap.add_argument("--out_md", default=r".\out\nist_ch\MODEL_SCORECARD_GKSL_LOO_V1.md")
    ap.add_argument("--out_params_dir", default=r".\out\nist_ch\gksl_loo_params")
    ap.add_argument("--center_slot", type=int, default=6)
    ap.add_argument("--chunk", type=int, default=2_000_000)
    ap.add_argument("--profile_scope", default="by_channel", choices=["by_channel", "by_channel_setting"])
    ap.add_argument("--dm2", type=float, default=0.0025)
    ap.add_argument("--theta_deg", type=float, default=45.0)
    ap.add_argument("--L0_km", type=float, default=1.0)
    ap.add_argument("--E_GeV", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--gamma_km_inv", type=float, default=None)
    ap.add_argument("--use_microphysics", action="store_true")
    ap.add_argument("--n_cm3", type=float, default=1.0e18)
    ap.add_argument("--visibility_ref", type=float, default=0.9)
    ap.add_argument("--v_cm_s", type=float, default=3.0e10)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    provider_mod = _load_module(Path(args.provider), "gksl_predictive_provider_v2")
    init_mod = _load_module(Path(args.init_module), "gksl_predictive_init_v2")
    compute_probs = provider_mod.compute_probabilities
    build_bundle = init_mod.build_gksl_param_bundle

    summary_paths = sorted(in_dir.glob("run*.summary.json"))
    real_runs = sorted({
        _extract_run_id(_read_json(sp), sp)
        for sp in summary_paths
        if "slot6" in sp.name and int(_read_json(sp).get("processed_trials_total_scanned", 0) or 0) >= 100000
    })
    if not real_runs:
        raise SystemExit(f"No real runs found in {in_dir}")

    out_params_dir = Path(args.out_params_dir)
    out_params_dir.mkdir(parents=True, exist_ok=True)

    gksl = {
        "dm2": float(args.dm2),
        "theta_deg": float(args.theta_deg),
        "L0_km": float(args.L0_km),
        "E_GeV": float(args.E_GeV),
        "steps": int(args.steps),
        "gamma_km_inv": args.gamma_km_inv,
        "use_microphysics": bool(args.use_microphysics),
        "n_cm3": float(args.n_cm3),
        "visibility_ref": float(args.visibility_ref),
        "v_cm_s": float(args.v_cm_s),
    }
    if not gksl["use_microphysics"] and gksl["gamma_km_inv"] is None:
        gksl["gamma_km_inv"] = 0.0

    records: List[Dict[str, Any]] = []
    for holdout_run in real_runs:
        bundle, report = build_bundle(
            in_dir=in_dir,
            center_slot=int(args.center_slot),
            chunk=int(args.chunk),
            profile_scope=str(args.profile_scope),
            train_runs=[r for r in real_runs if r != holdout_run],
            holdout_runs=[holdout_run],
            gksl=gksl,
        )
        params_path = out_params_dir / f"model_params_gksl_predictive_v2_holdout_{holdout_run}.json"
        report_path = out_params_dir / f"gksl_predictive_v2_holdout_{holdout_run}.report.json"
        params_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        for sp in summary_paths:
            summary = _read_json(sp)
            run_id = _extract_run_id(summary, sp)
            if run_id != holdout_run:
                continue
            counts_path = sp.with_name(sp.name.replace(".summary.json", ".counts.csv"))
            if not counts_path.exists():
                continue
            counts = _read_counts_csv(counts_path)
            N = counts["per_setting_trials"]
            N_valid = int(counts["total_valid_trials"])
            slots = summary.get("slots", [])
            bitmask_hex = summary.get("bitmask_hex", "")
            ch = summary.get("CH_terms", {})
            run_params = dict(bundle.get("defaults", {}))
            run_params.update(bundle.get("runs", {}).get(run_id, {}))
            run_ctx = {
                "run_id": run_id,
                "slots": slots,
                "bitmask_hex": bitmask_hex,
                "N_valid_by_setting": N,
                "trials_valid": N_valid,
                "h5_path": str(summary.get("h5_path", "")),
                "params": run_params,
            }
            probs = compute_probs(run_ctx)
            model = _compute_J_from_probs(N, probs)
            J_model = model["J_model"]
            J_data = int(summary.get("J", 0))
            j_data_per_1m = float(J_data) * 1e6 / N_valid if N_valid else 0.0
            j_model_per_1m = float(J_model) * 1e6 / N_valid if N_valid else 0.0
            records.append({
                "holdout_run": holdout_run,
                "run_id": run_id,
                "window": _window_label(slots),
                "slots": _slots_spec(slots),
                "trials_valid": N_valid,
                "J_data": J_data,
                "J_model": f"{J_model:.6g}",
                "delta_J": f"{(J_model - J_data):.6g}",
                "j_data_per_1M": f"{j_data_per_1m:.6g}",
                "j_model_per_1M": f"{j_model_per_1m:.6g}",
                "delta_j_per_1M": f"{(j_model_per_1m - j_data_per_1m):.6g}",
                "sign_ok": "YES" if (J_model > 0) == (J_data > 0) else "NO",
                "provider": probs.get("__provider_label__", str(Path(args.provider))),
                "params_json": str(params_path),
                "emp_N_pp_ab": int(ch.get("N_pp_ab", 0)),
                "emp_N_p0_abp": int(ch.get("N_p0_abp", 0)),
                "emp_N_0p_apb": int(ch.get("N_0p_apb", 0)),
                "emp_N_pp_apbp": int(ch.get("N_pp_apbp", 0)),
            })

    if not records:
        raise SystemExit("No records were produced.")

    def win_size(slotspec: str) -> int:
        if not slotspec:
            return 999
        if "-" in slotspec:
            a, b = slotspec.split("-", 1)
            return int(b) - int(a) + 1
        if "," in slotspec:
            return len(slotspec.split(","))
        return 1

    records.sort(key=lambda r: (r["holdout_run"], win_size(r["slots"])))

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        w.writeheader()
        for r in records:
            w.writerow(r)

    out_md = Path(args.out_md)
    headers = ["holdout_run", "run_id", "window", "slots", "trials_valid", "J_data", "J_model", "delta_J", "delta_j_per_1M", "sign_ok", "provider"]
    lines = ["# NIST CH GKSL leave-one-run-out scorecard", ""]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in records:
        lines.append("| " + " | ".join(str(r[h]).replace("|", "\\|") for h in headers) + " |")
    lines.append("")
    lines.append("## Notes")
    lines.append("- Each row is scored with a params bundle fitted on all real runs except the listed holdout run.")
    lines.append("- This is a GKSL-modulated predictive holdout bridge, not a calibrated closure.")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("[OK] wrote:", str(out_csv))
    print("[OK] wrote:", str(out_md))
    print("rows:", len(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
