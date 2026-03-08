#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH GKSL window-grid scan — DROP-IN v1

Fast systematic scan using only existing slot6 / 5-7 / 4-8 empirical files.
This is the practical route for selecting a dynamically sensitive holdout bridge.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def _compute_J(N: Dict[str, int], probs: Dict[str, Any]) -> float:
    P_pp = probs["P_pp"]
    P_p0 = probs["P_p0"]
    P_0p = probs["P_0p"]
    return float(N["00"] * P_pp["00"] - N["01"] * P_p0["01"] - N["10"] * P_0p["10"] - N["11"] * P_pp["11"])


def _parse_float_list(spec: str) -> List[float]:
    return [float(x.strip()) for x in spec.split(",") if x.strip()]


def _parse_text_list(spec: str) -> List[str]:
    return [x.strip() for x in spec.split(",") if x.strip()]


def _read_counts(path: Path) -> Dict[str, int]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        return {f"{int(r['a_set'])}{int(r['b_set'])}": int(float(r.get('trials_valid', r.get('trials', '0')))) for r in rdr}


def _score(records: List[Dict[str, Any]]) -> Dict[str, float]:
    wide = [abs(float(r["delta_j_per_1M"])) for r in records if r["window"] != "slot6"]
    allv = [abs(float(r["delta_j_per_1M"])) for r in records]
    return {
        "mae_all_per_1M": mean(allv) if allv else float("nan"),
        "mae_wide_per_1M": mean(wide) if wide else float("nan"),
        "rmse_wide_per_1M": math.sqrt(mean([float(r["delta_j_per_1M"]) ** 2 for r in records if r["window"] != "slot6"])) if wide else float("nan"),
        "sign_rate": mean([1.0 if r["sign_ok"] == "YES" else 0.0 for r in records]) if records else 0.0,
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
    ap.add_argument("--init_module", default=r".\CODE\nist_ch_init_gksl_windowfit_v1_DROPIN.py")
    ap.add_argument("--out_csv", default=r".\out\nist_ch\GKSL_WINDOWGRID_SCAN_V1.csv")
    ap.add_argument("--out_md", default=r".\out\nist_ch\GKSL_WINDOWGRID_SCAN_V1.md")
    ap.add_argument("--best_scorecard_csv", default=r".\out\nist_ch\MODEL_SCORECARD_GKSL_DYNAMIC_WINDOWFIT_V1.csv")
    ap.add_argument("--best_scorecard_md", default=r".\out\nist_ch\MODEL_SCORECARD_GKSL_DYNAMIC_WINDOWFIT_V1.md")
    ap.add_argument("--best_params_json", default=r".\out\nist_ch\model_params_gksl_dynamic_windowfit_v1_best.json")
    ap.add_argument("--best_report_json", default=r".\out\nist_ch\gksl_dynamic_windowfit_v1_best.report.json")
    ap.add_argument("--gamma_values", default="0,1e-4,1e-3,1e-2,1e-1,1")
    ap.add_argument("--L0_values", default="1e-3,1,1e3,1e6")
    ap.add_argument("--profile_form_values", default="tilt_abs_quad,tilt_abs,tilt_quad,abs_quad")
    ap.add_argument("--dm2", type=float, default=0.0025)
    ap.add_argument("--theta_deg", type=float, default=45.0)
    ap.add_argument("--E_GeV", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--sensitivity_min_per_1M", type=float, default=0.02)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    provider = _load_module(Path(args.provider), "provider_v3_windowgrid")
    init_mod = _load_module(Path(args.init_module), "init_windowfit_v1")
    compute_probabilities = provider.compute_probabilities
    collect_window_rates = init_mod.collect_window_rates
    build_windowfit_bundle = init_mod.build_windowfit_bundle

    window_rates = collect_window_rates(in_dir)
    real_runs = sorted(window_rates.keys())
    gamma_values = _parse_float_list(args.gamma_values)
    L0_values = _parse_float_list(args.L0_values)
    forms = _parse_text_list(args.profile_form_values)

    by_config: Dict[str, List[Dict[str, Any]]] = {}
    scan_rows: List[Dict[str, Any]] = []

    for form in forms:
        for L0 in L0_values:
            for gamma in gamma_values:
                config_id = f"form={form}|L0={L0:.6g}|gamma={gamma:.6g}"
                records: List[Dict[str, Any]] = []
                for holdout in real_runs:
                    gksl = {"dm2": float(args.dm2), "theta_deg": float(args.theta_deg), "L0_km": float(L0), "E_GeV": float(args.E_GeV), "steps": int(args.steps), "gamma_km_inv": float(gamma), "use_microphysics": False}
                    bundle, report = build_windowfit_bundle(in_dir, window_rates, [r for r in real_runs if r != holdout], [holdout], form, gksl)
                    for tag in ("slot6", "slots5_7", "slots4_8"):
                        summary = json.loads((in_dir / f"run{holdout}_{tag}.summary.json").read_text(encoding="utf-8"))
                        N = _read_counts(in_dir / f"run{holdout}_{tag}.counts.csv")
                        N_valid = sum(N.values())
                        params = dict(bundle["defaults"])
                        params.update(bundle["runs"][holdout])
                        probs = compute_probabilities({"run_id": holdout, "slots": list(summary.get("slots", [])), "bitmask_hex": summary.get("bitmask_hex", ""), "N_valid_by_setting": N, "trials_valid": N_valid, "h5_path": str(summary.get("h5_path", "")), "params": params})
                        J_model = _compute_J(N, probs)
                        J_data = int(summary.get("J", 0))
                        j_data_per_1M = float(J_data) * 1e6 / N_valid if N_valid else 0.0
                        j_model_per_1M = float(J_model) * 1e6 / N_valid if N_valid else 0.0
                        records.append({
                            "config_id": config_id,
                            "holdout_run": holdout,
                            "window": tag.replace("slots", "slots").replace("slot6", "slot6").replace("_", "-"),
                            "J_data": J_data,
                            "J_model": float(J_model),
                            "delta_J": float(J_model - J_data),
                            "j_data_per_1M": j_data_per_1M,
                            "j_model_per_1M": j_model_per_1M,
                            "delta_j_per_1M": float(j_model_per_1M - j_data_per_1M),
                            "sign_ok": "YES" if (J_model > 0) == (J_data > 0) else "NO",
                            "profile_form": form,
                            "L0_km": float(L0),
                            "gamma_km_inv": float(gamma),
                            "provider": probs.get("__provider_label__", ""),
                        })
                by_config[config_id] = records
                metrics = _score(records)
                scan_rows.append({"config_id": config_id, "profile_form": form, "L0_km": float(L0), "gamma_km_inv": float(gamma), **metrics})

    baseline = {(r["profile_form"], float(r["L0_km"])): r for r in scan_rows if abs(float(r["gamma_km_inv"])) < 1e-30}
    pred_map = {cid: {(r["holdout_run"], r["window"]): float(r["j_model_per_1M"]) for r in recs} for cid, recs in by_config.items()}
    for row in scan_rows:
        base = baseline.get((row["profile_form"], float(row["L0_km"])))
        shift = 0.0
        if base is not None:
            cur = pred_map[row["config_id"]]
            ref = pred_map[base["config_id"]]
            vals = [abs(cur[k] - ref[k]) for k in cur if k in ref]
            shift = mean(vals) if vals else 0.0
        row["gamma_shift_mean_per_1M"] = float(shift)
        row["dynamic_sensitive"] = "YES" if shift >= float(args.sensitivity_min_per_1M) else "NO"

    eligible = [r for r in scan_rows if r["dynamic_sensitive"] == "YES" and float(r["sign_rate"]) >= 0.999]
    pool = eligible if eligible else scan_rows
    best = min(pool, key=lambda r: (float(r["mae_wide_per_1M"]), float(r["rmse_wide_per_1M"]), -float(r["gamma_shift_mean_per_1M"])))
    best_records = by_config[best["config_id"]]

    scan_rows.sort(key=lambda r: (float(r["mae_wide_per_1M"]), -float(r["gamma_shift_mean_per_1M"])))
    _write_csv(Path(args.out_csv), scan_rows)
    _write_csv(Path(args.best_scorecard_csv), best_records)

    Path(args.out_md).write_text("\n".join([
        "# NIST CH GKSL window-grid scan",
        "",
        f"Best config: {best['config_id']}",
        "",
        "| profile_form | L0_km | gamma_km_inv | mae_wide_per_1M | rmse_wide_per_1M | gamma_shift_mean_per_1M | dynamic_sensitive | sign_rate |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        *[
            f"| {r['profile_form']} | {float(r['L0_km']):.6g} | {float(r['gamma_km_inv']):.6g} | {float(r['mae_wide_per_1M']):.6g} | {float(r['rmse_wide_per_1M']):.6g} | {float(r['gamma_shift_mean_per_1M']):.6g} | {r['dynamic_sensitive']} | {float(r['sign_rate']):.3f} |"
            for r in scan_rows[:30]
        ]
    ]), encoding="utf-8")
    Path(args.best_scorecard_md).write_text("\n".join([
        "# NIST CH best dynamic-sensitive windowfit scorecard",
        "",
        f"Best config: {best['config_id']}",
        "",
        "| holdout_run | window | J_data | J_model | delta_J | delta_j_per_1M | sign_ok |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *[
            f"| {r['holdout_run']} | {r['window']} | {r['J_data']} | {r['J_model']:.6g} | {r['delta_J']:.6g} | {r['delta_j_per_1M']:.6g} | {r['sign_ok']} |"
            for r in best_records
        ]
    ]), encoding="utf-8")

    final_gksl = {"dm2": float(args.dm2), "theta_deg": float(args.theta_deg), "L0_km": float(best['L0_km']), "E_GeV": float(args.E_GeV), "steps": int(args.steps), "gamma_km_inv": float(best['gamma_km_inv']), "use_microphysics": False}
    best_bundle, best_report = build_windowfit_bundle(in_dir, window_rates, real_runs, [], str(best['profile_form']), final_gksl)
    Path(args.best_params_json).write_text(json.dumps(best_bundle, indent=2), encoding="utf-8")
    Path(args.best_report_json).write_text(json.dumps({"best_config": best, "best_fit_report": best_report, "top10": scan_rows[:10]}, indent=2), encoding="utf-8")

    print("[OK] wrote:", str(args.out_csv))
    print("[OK] wrote:", str(args.out_md))
    print("[OK] wrote:", str(args.best_scorecard_csv))
    print("[OK] wrote:", str(args.best_scorecard_md))
    print("[OK] wrote:", str(args.best_params_json))
    print("[OK] wrote:", str(args.best_report_json))
    print("best:", best["config_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
