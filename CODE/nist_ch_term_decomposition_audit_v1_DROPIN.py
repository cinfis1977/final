#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH term decomposition audit — DROP-IN v1

Purpose
-------
Decompose modeled versus empirical CH contributions by term under strict LOO.
This is intended to diagnose wide-window failures after probability-accounting
sanity checks have already passed.

Terms
-----
J = N_pp(00) - N_p0(01) - N_0p(10) - N_pp(11)

Outputs
-------
- per-run/window term decomposition CSV
- JSON summary with dominant failure drivers
- Markdown summary
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple


KEYS = ("00", "01", "10", "11")
WINDOWS = ("slot6", "slots5-7", "slots4-8")
TERM_SPEC = {
    "N_pp_00": ("00", "pp", +1.0),
    "N_p0_01": ("01", "p0", -1.0),
    "N_0p_10": ("10", "0p", -1.0),
    "N_pp_11": ("11", "pp", -1.0),
}


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_counts(path: Path) -> Dict[str, Dict[str, int]]:
    out = {"N": {}, "A": {}, "B": {}, "AB": {}}
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            k = f"{int(row['a_set'])}{int(row['b_set'])}"
            out["N"][k] = int(float(row.get("trials_valid", row.get("trials", "0"))))
            out["A"][k] = int(float(row.get("alice_detect", "0")))
            out["B"][k] = int(float(row.get("bob_detect", "0")))
            out["AB"][k] = int(float(row.get("both_detect", "0")))
    return out


def _window_label(slots: List[int]) -> str:
    if len(slots) == 1:
        return f"slot{slots[0]}"
    return f"slots{slots[0]}-{slots[-1]}"


def _empirical_term_counts(in_dir: Path, run_id: str, tag: str) -> Dict[str, Any]:
    counts = _read_counts(in_dir / f"run{run_id}_{tag}.counts.csv")
    summary = _read_json(in_dir / f"run{run_id}_{tag}.summary.json")
    ch = dict(summary.get("CH_terms", {}) or {})
    A = counts["A"]
    B = counts["B"]
    AB = counts["AB"]
    N = counts["N"]

    pp = {k: max(0, int(AB.get(k, 0))) for k in KEYS}
    p0 = {k: max(0, int(A.get(k, 0)) - int(AB.get(k, 0))) for k in KEYS}
    op = {k: max(0, int(B.get(k, 0)) - int(AB.get(k, 0))) for k in KEYS}

    if "N_pp_ab" in ch:
        pp["00"] = int(ch["N_pp_ab"])
    if "N_p0_abp" in ch:
        p0["01"] = int(ch["N_p0_abp"])
    if "N_0p_apb" in ch:
        op["10"] = int(ch["N_0p_apb"])
    if "N_pp_apbp" in ch:
        pp["11"] = int(ch["N_pp_apbp"])

    terms = {
        "N_pp_00": float(pp["00"]),
        "N_p0_01": float(p0["01"]),
        "N_0p_10": float(op["10"]),
        "N_pp_11": float(pp["11"]),
    }
    j_data = terms["N_pp_00"] - terms["N_p0_01"] - terms["N_0p_10"] - terms["N_pp_11"]
    return {"terms": terms, "N": N, "j_data": j_data, "slots": list(summary.get("slots", [])), "bitmask_hex": summary.get("bitmask_hex", ""), "h5_path": str(summary.get("h5_path", ""))}


def _build_bundle(init_mod: Any, in_dir: Path, holdout_run: str, profile_form: str, dm2: float, theta_deg: float, L0_km: float, E_GeV: float, steps: int, gamma_km_inv: float):
    if hasattr(init_mod, "collect_window_rates_and_meta") and hasattr(init_mod, "build_detectorfirst_v2_bundle"):
        rates, meta = init_mod.collect_window_rates_and_meta(in_dir)
        real_runs = init_mod.discover_real_runs(in_dir)
        gksl = {"dm2": dm2, "theta_deg": theta_deg, "L0_km": L0_km, "E_GeV": E_GeV, "steps": steps, "gamma_km_inv": gamma_km_inv, "use_microphysics": False}
        return init_mod.build_detectorfirst_v2_bundle(rates, meta, [r for r in real_runs if r != holdout_run], [holdout_run], profile_form, gksl)
    raise SystemExit("Unsupported init module for this audit runner.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--provider", default=r".\CODE\ch_model_prob_provider_v1_GKSL_DETECTORFIRST_V2_DROPIN.py")
    ap.add_argument("--init_module", default=r".\CODE\nist_ch_init_gksl_detectorfirst_v2_DROPIN.py")
    ap.add_argument("--out_csv", default=r".\out\nist_ch\TERM_DECOMPOSITION_AUDIT_V1.csv")
    ap.add_argument("--out_json", default=r".\out\nist_ch\TERM_DECOMPOSITION_AUDIT_V1.json")
    ap.add_argument("--out_md", default=r".\out\nist_ch\TERM_DECOMPOSITION_AUDIT_V1.md")
    ap.add_argument("--profile_form", default="tilt_abs_quad")
    ap.add_argument("--dm2", type=float, default=0.0025)
    ap.add_argument("--theta_deg", type=float, default=45.0)
    ap.add_argument("--L0_km", type=float, default=1.0)
    ap.add_argument("--E_GeV", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--gamma_km_inv", type=float, default=1.0)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    provider_mod = _load_module(Path(args.provider), "term_audit_provider")
    init_mod = _load_module(Path(args.init_module), "term_audit_init")
    real_runs = init_mod.discover_real_runs(in_dir)

    rows: List[Dict[str, Any]] = []
    summaries: List[Dict[str, Any]] = []

    for holdout_run in real_runs:
        bundle, _report = _build_bundle(
            init_mod,
            in_dir,
            holdout_run,
            str(args.profile_form),
            float(args.dm2),
            float(args.theta_deg),
            float(args.L0_km),
            float(args.E_GeV),
            int(args.steps),
            float(args.gamma_km_inv),
        )
        params = dict(bundle.get("defaults", {}))
        params.update(bundle.get("runs", {}).get(holdout_run, {}))

        slot6_model_terms: Dict[str, float] | None = None
        slot6_emp_terms: Dict[str, float] | None = None

        for tag in ("slot6", "slots5_7", "slots4_8"):
            emp = _empirical_term_counts(in_dir, holdout_run, tag)
            window = _window_label(emp["slots"])
            run_ctx = {
                "run_id": holdout_run,
                "slots": emp["slots"],
                "bitmask_hex": emp["bitmask_hex"],
                "N_valid_by_setting": emp["N"],
                "trials_valid": sum(emp["N"].values()),
                "h5_path": emp["h5_path"],
                "params": params,
            }
            probs = provider_mod.compute_probabilities(run_ctx)

            model_terms: Dict[str, float] = {}
            for term_name, (setting, channel, _sign) in TERM_SPEC.items():
                pmap = {"pp": probs["P_pp"], "p0": probs["P_p0"], "0p": probs["P_0p"]}[channel]
                model_terms[term_name] = float(emp["N"][setting]) * float(pmap[setting])

            if window == "slot6":
                slot6_model_terms = dict(model_terms)
                slot6_emp_terms = dict(emp["terms"])

            j_model = model_terms["N_pp_00"] - model_terms["N_p0_01"] - model_terms["N_0p_10"] - model_terms["N_pp_11"]
            j_data = float(emp["j_data"])
            deltas = {term: model_terms[term] - float(emp["terms"][term]) for term in TERM_SPEC}
            dominant_term = max(deltas.items(), key=lambda kv: abs(kv[1]))[0]

            row = {
                "holdout_run": holdout_run,
                "window": window,
                "J_data": j_data,
                "J_model": j_model,
                "J_delta": j_model - j_data,
                "dominant_term": dominant_term,
            }
            for term in TERM_SPEC:
                row[f"emp_{term}"] = float(emp["terms"][term])
                row[f"model_{term}"] = model_terms[term]
                row[f"delta_{term}"] = deltas[term]
                if slot6_model_terms is not None and slot6_emp_terms is not None and window != "slot6":
                    base_m = float(slot6_model_terms[term])
                    base_e = float(slot6_emp_terms[term])
                    row[f"growth_model_{term}"] = model_terms[term] / base_m if abs(base_m) > 1e-12 else float("nan")
                    row[f"growth_emp_{term}"] = float(emp["terms"][term]) / base_e if abs(base_e) > 1e-12 else float("nan")
                else:
                    row[f"growth_model_{term}"] = 1.0 if window == "slot6" else float("nan")
                    row[f"growth_emp_{term}"] = 1.0 if window == "slot6" else float("nan")
            rows.append(row)

            summaries.append({
                "holdout_run": holdout_run,
                "window": window,
                "J_data": j_data,
                "J_model": j_model,
                "J_delta": j_model - j_data,
                "dominant_term": dominant_term,
                "dominant_delta": deltas[dominant_term],
            })

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    wide_rows = [r for r in summaries if r["window"] != "slot6"]
    dominant_counts: Dict[str, int] = {}
    for r in wide_rows:
        dominant_counts[r["dominant_term"]] = dominant_counts.get(r["dominant_term"], 0) + 1

    global_summary = {
        "provider": str(args.provider),
        "profile_form": str(args.profile_form),
        "gksl": {
            "gamma_km_inv": float(args.gamma_km_inv),
            "L0_km": float(args.L0_km),
        },
        "dominant_term_counts_wide": dominant_counts,
        "mean_abs_J_delta_slot6": mean(abs(float(r["J_delta"])) for r in summaries if r["window"] == "slot6"),
        "mean_abs_J_delta_wide": mean(abs(float(r["J_delta"])) for r in wide_rows),
        "rows": summaries,
    }

    out_json = Path(args.out_json)
    out_json.write_text(json.dumps(global_summary, indent=2), encoding="utf-8")

    md = [
        "# NIST CH term decomposition audit",
        "",
        f"- provider: {args.provider}",
        f"- profile_form: {args.profile_form}",
        f"- gamma_km_inv: {float(args.gamma_km_inv):.6g}",
        f"- L0_km: {float(args.L0_km):.6g}",
        "",
        "## Global",
        f"- mean_abs_J_delta_slot6: {global_summary['mean_abs_J_delta_slot6']:.6g}",
        f"- mean_abs_J_delta_wide: {global_summary['mean_abs_J_delta_wide']:.6g}",
        f"- dominant_term_counts_wide: {json.dumps(dominant_counts, sort_keys=True)}",
        "",
        "## Run/window summary",
        "| holdout_run | window | J_data | J_model | J_delta | dominant_term | dominant_delta |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in summaries:
        md.append(
            f"| {r['holdout_run']} | {r['window']} | {r['J_data']:.6g} | {r['J_model']:.6g} | {r['J_delta']:.6g} | {r['dominant_term']} | {r['dominant_delta']:.6g} |"
        )
    Path(args.out_md).write_text("\n".join(md), encoding="utf-8")

    print("[OK] wrote:", str(out_csv))
    print("[OK] wrote:", str(out_json))
    print("[OK] wrote:", str(out_md := Path(args.out_md)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
