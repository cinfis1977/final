#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH GKSL hypergrid scan — DROP-IN v1

Systematically scans:
- gamma_km_inv
- L0_km
- profile_form
- optional profile_scope

using strict leave-one-run-out evaluation. It writes:
- full config summary CSV/MD
- best-config scorecard CSV/MD
- best params JSON + report JSON

Selection rule
--------------
Choose the lowest wide-window MAE among candidates that are actually gamma
sensitive relative to the gamma=0 baseline for the same profile/L0/scope.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple


KEYS = ("00", "01", "10", "11")
WIDE_WINDOWS = {"slots5-7", "slots4-8"}


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
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


def _compute_J_from_probs(N: Dict[str, int], probs: Dict[str, Any]) -> float:
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
    return float(N["00"] * float(P_pp["00"]) - N["01"] * float(P_p0["01"]) - N["10"] * float(P_0p["10"]) - N["11"] * float(P_pp["11"]))


def _parse_float_list(spec: str) -> List[float]:
    out = []
    for part in spec.split(","):
        tok = part.strip()
        if tok:
            out.append(float(tok))
    return out


def _parse_text_list(spec: str) -> List[str]:
    return [part.strip() for part in spec.split(",") if part.strip()]


def _window_label(slots: List[int]) -> str:
    if len(slots) == 1:
        return f"slot{slots[0]}"
    if slots == list(range(slots[0], slots[-1] + 1)):
        return f"slots{slots[0]}-{slots[-1]}"
    return "slots" + "_".join(str(x) for x in slots)


def _slots_spec(slots: List[int]) -> str:
    if len(slots) == 1:
        return str(slots[0])
    if slots == list(range(slots[0], slots[-1] + 1)):
        return f"{slots[0]}-{slots[-1]}"
    return ",".join(str(x) for x in slots)


def _score_candidate(records: List[Dict[str, Any]]) -> Dict[str, float]:
    abs_all = [abs(float(r["delta_j_per_1M"])) for r in records]
    abs_wide = [abs(float(r["delta_j_per_1M"])) for r in records if r["window"] in WIDE_WINDOWS]
    rmse_wide = math.sqrt(mean([float(r["delta_j_per_1M"]) ** 2 for r in records if r["window"] in WIDE_WINDOWS])) if abs_wide else float("nan")
    sign_rate = mean([1.0 if r["sign_ok"] == "YES" else 0.0 for r in records]) if records else 0.0
    slot6_mae = mean([abs(float(r["delta_j_per_1M"])) for r in records if r["window"] == "slot6"]) if records else float("nan")
    return {
        "mae_all_per_1M": mean(abs_all) if abs_all else float("nan"),
        "mae_wide_per_1M": mean(abs_wide) if abs_wide else float("nan"),
        "rmse_wide_per_1M": rmse_wide,
        "slot6_mae_per_1M": slot6_mae,
        "sign_rate": sign_rate,
    }


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--provider", default=r".\CODE\ch_model_prob_provider_v1_GKSL_PREDICTIVE_V3_DROPIN.py")
    ap.add_argument("--init_module", default=r".\CODE\nist_ch_init_gksl_predictive_v3_DROPIN.py")
    ap.add_argument("--out_csv", default=r".\out\nist_ch\GKSL_HYPERGRID_SCAN_V1.csv")
    ap.add_argument("--out_md", default=r".\out\nist_ch\GKSL_HYPERGRID_SCAN_V1.md")
    ap.add_argument("--best_scorecard_csv", default=r".\out\nist_ch\MODEL_SCORECARD_GKSL_DYNAMIC_V3.csv")
    ap.add_argument("--best_scorecard_md", default=r".\out\nist_ch\MODEL_SCORECARD_GKSL_DYNAMIC_V3.md")
    ap.add_argument("--best_params_json", default=r".\out\nist_ch\model_params_gksl_dynamic_v3_best.json")
    ap.add_argument("--best_report_json", default=r".\out\nist_ch\gksl_dynamic_v3_best.report.json")
    ap.add_argument("--scan_records_json", default=r".\out\nist_ch\gksl_hypergrid_scan_records_v1.json")
    ap.add_argument("--center_slot", type=int, default=6)
    ap.add_argument("--chunk", type=int, default=2_000_000)
    ap.add_argument("--profile_scope_values", default="by_channel")
    ap.add_argument("--profile_form_values", default="tilt_abs_quad,tilt_abs,tilt_quad,abs_quad,linear_abs_quad")
    ap.add_argument("--gamma_values", default="0,1e-6,1e-4,1e-3,1e-2,1e-1,1")
    ap.add_argument("--L0_values", default="1e-3,1,1e3,1e6")
    ap.add_argument("--dm2", type=float, default=0.0025)
    ap.add_argument("--theta_deg", type=float, default=45.0)
    ap.add_argument("--E_GeV", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--n_cm3", type=float, default=1.0e18)
    ap.add_argument("--visibility_ref", type=float, default=0.9)
    ap.add_argument("--v_cm_s", type=float, default=3.0e10)
    ap.add_argument("--sensitivity_min_per_1M", type=float, default=0.02)
    args = ap.parse_args()

    provider_mod = _load_module(Path(args.provider), "gksl_predictive_provider_v3")
    init_mod = _load_module(Path(args.init_module), "gksl_predictive_init_v3")
    compute_probabilities = provider_mod.compute_probabilities
    collect_all_run_rates = init_mod.collect_all_run_rates
    build_bundle_from_rates = init_mod.build_gksl_param_bundle_from_rates

    in_dir = Path(args.in_dir)
    rates_by_run, run_meta = collect_all_run_rates(in_dir, int(args.chunk))
    real_runs = sorted(run_meta.keys())
    if not real_runs:
        raise SystemExit("No real runs available for scan.")

    gamma_values = _parse_float_list(args.gamma_values)
    L0_values = _parse_float_list(args.L0_values)
    profile_forms = _parse_text_list(args.profile_form_values)
    profile_scopes = _parse_text_list(args.profile_scope_values)

    by_config_records: Dict[str, List[Dict[str, Any]]] = {}
    scan_rows: List[Dict[str, Any]] = []
    full_record_dump: Dict[str, Any] = {"configs": {}}

    for scope in profile_scopes:
        for form in profile_forms:
            for L0 in L0_values:
                for gamma in gamma_values:
                    config_id = f"scope={scope}|form={form}|L0={L0:.6g}|gamma={gamma:.6g}"
                    records: List[Dict[str, Any]] = []
                    for holdout_run in real_runs:
                        gksl = {
                            "dm2": float(args.dm2),
                            "theta_deg": float(args.theta_deg),
                            "L0_km": float(L0),
                            "E_GeV": float(args.E_GeV),
                            "steps": int(args.steps),
                            "gamma_km_inv": float(gamma),
                            "use_microphysics": False,
                            "n_cm3": float(args.n_cm3),
                            "visibility_ref": float(args.visibility_ref),
                            "v_cm_s": float(args.v_cm_s),
                        }
                        bundle, report = build_bundle_from_rates(
                            rates_by_run=rates_by_run,
                            run_meta=run_meta,
                            in_dir=in_dir,
                            center_slot=int(args.center_slot),
                            profile_scope=scope,
                            profile_form=form,
                            train_runs=[r for r in real_runs if r != holdout_run],
                            holdout_runs=[holdout_run],
                            gksl=gksl,
                        )
                        for sp in [run_meta[holdout_run]["summary_path"], in_dir / f"run{holdout_run}_slots5_7.summary.json", in_dir / f"run{holdout_run}_slots4_8.summary.json"]:
                            summary = json.loads(Path(sp).read_text(encoding="utf-8"))
                            counts_path = Path(sp).with_name(Path(sp).name.replace('.summary.json', '.counts.csv'))
                            rows = []
                            with counts_path.open("r", encoding="utf-8", newline="") as f:
                                rdr = csv.DictReader(f)
                                rows = list(rdr)
                            N = {f"{int(r['a_set'])}{int(r['b_set'])}": int(float(r.get('trials_valid', r.get('trials', '0')))) for r in rows}
                            N_valid = sum(N.values())
                            run_params = dict(bundle.get("defaults", {}))
                            run_params.update(bundle.get("runs", {}).get(holdout_run, {}))
                            run_ctx = {
                                "run_id": holdout_run,
                                "slots": list(summary.get("slots", [])),
                                "bitmask_hex": summary.get("bitmask_hex", ""),
                                "N_valid_by_setting": N,
                                "trials_valid": N_valid,
                                "h5_path": str(summary.get("h5_path", "")),
                                "params": run_params,
                            }
                            probs = compute_probabilities(run_ctx)
                            J_model = _compute_J_from_probs(N, probs)
                            J_data = int(summary.get("J", 0))
                            j_data_per_1M = float(J_data) * 1e6 / N_valid if N_valid else 0.0
                            j_model_per_1M = float(J_model) * 1e6 / N_valid if N_valid else 0.0
                            records.append({
                                "config_id": config_id,
                                "holdout_run": holdout_run,
                                "run_id": holdout_run,
                                "window": _window_label(list(summary.get("slots", []))),
                                "slots": _slots_spec(list(summary.get("slots", []))),
                                "trials_valid": N_valid,
                                "J_data": J_data,
                                "J_model": float(J_model),
                                "delta_J": float(J_model - J_data),
                                "j_data_per_1M": j_data_per_1M,
                                "j_model_per_1M": j_model_per_1M,
                                "delta_j_per_1M": float(j_model_per_1M - j_data_per_1M),
                                "sign_ok": "YES" if (J_model > 0) == (J_data > 0) else "NO",
                                "provider": probs.get("__provider_label__", str(Path(args.provider))),
                                "profile_scope": scope,
                                "profile_form": form,
                                "L0_km": float(L0),
                                "gamma_km_inv": float(gamma),
                                "gamma_fit_km_inv": float(report.get("gamma_km_inv", gamma)),
                            })
                    metrics = _score_candidate(records)
                    by_config_records[config_id] = records
                    full_record_dump["configs"][config_id] = records
                    scan_rows.append({
                        "config_id": config_id,
                        "profile_scope": scope,
                        "profile_form": form,
                        "L0_km": float(L0),
                        "gamma_km_inv": float(gamma),
                        **metrics,
                    })

    baseline_map: Dict[Tuple[str, str, float], Dict[str, Any]] = {}
    for row in scan_rows:
        key = (str(row["profile_scope"]), str(row["profile_form"]), float(row["L0_km"]))
        if abs(float(row["gamma_km_inv"])) < 1.0e-30:
            baseline_map[key] = row

    baseline_preds: Dict[str, Dict[Tuple[str, str], float]] = {}
    for config_id, recs in by_config_records.items():
        baseline_preds[config_id] = {(r["holdout_run"], r["window"]): float(r["j_model_per_1M"]) for r in recs}

    for row in scan_rows:
        key = (str(row["profile_scope"]), str(row["profile_form"]), float(row["L0_km"]))
        base = baseline_map.get(key)
        shift = 0.0
        if base is not None:
            base_id = str(base["config_id"])
            cur_id = str(row["config_id"])
            deltas = []
            for hk, val in baseline_preds[cur_id].items():
                if hk in baseline_preds[base_id]:
                    deltas.append(abs(float(val) - float(baseline_preds[base_id][hk])))
            shift = mean(deltas) if deltas else 0.0
        row["gamma_shift_mean_per_1M"] = float(shift)
        row["dynamic_sensitive"] = "YES" if shift >= float(args.sensitivity_min_per_1M) else "NO"

    eligible = [r for r in scan_rows if r["dynamic_sensitive"] == "YES" and float(r["sign_rate"]) >= 0.999]
    pool = eligible if eligible else scan_rows
    best = min(pool, key=lambda r: (float(r["mae_wide_per_1M"]), float(r["rmse_wide_per_1M"]), -float(r.get("gamma_shift_mean_per_1M", 0.0))))
    best_id = str(best["config_id"])
    best_records = by_config_records[best_id]

    scan_rows.sort(key=lambda r: (float(r["mae_wide_per_1M"]), -float(r["gamma_shift_mean_per_1M"])))
    _write_csv(Path(args.out_csv), scan_rows)

    md_lines = ["# NIST CH GKSL hypergrid scan", "", f"Best config: {best_id}", "", "| profile_scope | profile_form | L0_km | gamma_km_inv | mae_wide_per_1M | rmse_wide_per_1M | gamma_shift_mean_per_1M | dynamic_sensitive | sign_rate |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in scan_rows[:40]:
        md_lines.append(
            f"| {row['profile_scope']} | {row['profile_form']} | {float(row['L0_km']):.6g} | {float(row['gamma_km_inv']):.6g} | {float(row['mae_wide_per_1M']):.6g} | {float(row['rmse_wide_per_1M']):.6g} | {float(row['gamma_shift_mean_per_1M']):.6g} | {row['dynamic_sensitive']} | {float(row['sign_rate']):.3f} |"
        )
    Path(args.out_md).write_text("\n".join(md_lines), encoding="utf-8")

    _write_csv(Path(args.best_scorecard_csv), best_records)
    best_md_headers = ["holdout_run", "run_id", "window", "slots", "J_data", "J_model", "delta_J", "delta_j_per_1M", "sign_ok", "profile_form", "L0_km", "gamma_km_inv"]
    best_md = ["# NIST CH best dynamic-sensitive GKSL scorecard", "", f"Best config: {best_id}", "", "| " + " | ".join(best_md_headers) + " |", "| " + " | ".join(["---"] * len(best_md_headers)) + " |"]
    for r in best_records:
        best_md.append("| " + " | ".join(str(r[h]).replace("|", "\\|") for h in best_md_headers) + " |")
    Path(args.best_scorecard_md).write_text("\n".join(best_md), encoding="utf-8")

    best_bundle_info = {
        "best_config": best,
        "best_records": best_records,
    }
    Path(args.best_params_json).write_text(json.dumps(best_bundle_info, indent=2), encoding="utf-8")
    Path(args.best_report_json).write_text(json.dumps({"best_config": best, "top10": scan_rows[:10]}, indent=2), encoding="utf-8")
    Path(args.scan_records_json).write_text(json.dumps(full_record_dump, indent=2), encoding="utf-8")

    print("[OK] wrote:", str(args.out_csv))
    print("[OK] wrote:", str(args.out_md))
    print("[OK] wrote:", str(args.best_scorecard_csv))
    print("[OK] wrote:", str(args.best_scorecard_md))
    print("best:", best_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
