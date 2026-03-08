#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH probability accounting audit — DROP-IN v1

Purpose
-------
Audit a CH provider under strict leave-one-run-out and diagnose failures before
moving to heavier trial-level hazard machinery.

Current focus
-------------
This runner is built to inspect detector-first providers such as:
- ch_model_prob_provider_v1_GKSL_DETECTORFIRST_V2_DROPIN.py
- nist_ch_init_gksl_detectorfirst_v2_DROPIN.py

Checks
------
1) Probability bounds:
   0 <= P_pp, P_p0, P_0p <= 1
2) Channel accounting:
   P_pp + P_p0 <= 1
   P_pp + P_0p <= 1
   P_pp + P_p0 + P_0p <= 1
3) Window monotonicity:
   slot6 <= slots5-7 <= slots4-8 for each channel/setting
4) Slot6 anchor error versus empirical slot6 channels
5) (1,1) pair suppression diagnostics

Outputs
-------
- audit JSON
- audit Markdown
- per-setting CSV
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


KEYS = ("00", "01", "10", "11")
CHANNELS = ("pp", "p0", "0p")
WINDOW_ORDER = ("slot6", "slots5-7", "slots4-8")
TAG_BY_WINDOW = {
    "slot6": "slot6",
    "slots5-7": "slots5_7",
    "slots4-8": "slots4_8",
}


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


def _empirical_channels(in_dir: Path, run_id: str, tag: str) -> Dict[str, Any]:
    counts = _read_counts(in_dir / f"run{run_id}_{tag}.counts.csv")
    summary = _read_json(in_dir / f"run{run_id}_{tag}.summary.json")
    ch = dict(summary.get("CH_terms", {}) or {})
    N = counts["N"]
    A = counts["A"]
    B = counts["B"]
    AB = counts["AB"]
    pp = {k: max(0, int(AB.get(k, 0))) for k in KEYS}
    p0 = {k: max(0, int(A.get(k, 0)) - int(AB.get(k, 0))) for k in KEYS}
    op = {k: max(0, int(B.get(k, 0)) - int(AB.get(k, 0))) for k in KEYS}
    if "N_pp_ab" in ch:
        pp["00"] = int(ch["N_pp_ab"])
    if "N_pp_apbp" in ch:
        pp["11"] = int(ch["N_pp_apbp"])
    if "N_p0_abp" in ch:
        p0["01"] = int(ch["N_p0_abp"])
    if "N_0p_apb" in ch:
        op["10"] = int(ch["N_0p_apb"])
    return {
        "pp": {k: _clip01(pp[k] / max(1, N[k])) for k in KEYS},
        "p0": {k: _clip01(p0[k] / max(1, N[k])) for k in KEYS},
        "0p": {k: _clip01(op[k] / max(1, N[k])) for k in KEYS},
        "N": N,
    }


def _window_label(slots: List[int]) -> str:
    if len(slots) == 1:
        return f"slot{slots[0]}"
    return f"slots{slots[0]}-{slots[-1]}"


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
    ap.add_argument("--out_json", default=r".\out\nist_ch\PROBABILITY_ACCOUNTING_AUDIT_V1.json")
    ap.add_argument("--out_md", default=r".\out\nist_ch\PROBABILITY_ACCOUNTING_AUDIT_V1.md")
    ap.add_argument("--out_csv", default=r".\out\nist_ch\PROBABILITY_ACCOUNTING_AUDIT_V1.csv")
    ap.add_argument("--profile_form", default="tilt_abs_quad")
    ap.add_argument("--dm2", type=float, default=0.0025)
    ap.add_argument("--theta_deg", type=float, default=45.0)
    ap.add_argument("--L0_km", type=float, default=1.0)
    ap.add_argument("--E_GeV", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--gamma_km_inv", type=float, default=1.0)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    provider_mod = _load_module(Path(args.provider), "prob_audit_provider")
    init_mod = _load_module(Path(args.init_module), "prob_audit_init")
    real_runs = init_mod.discover_real_runs(in_dir)

    per_setting_rows: List[Dict[str, Any]] = []
    run_window_summary: List[Dict[str, Any]] = []

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

        model_by_window: Dict[str, Dict[str, Dict[str, float]]] = {}
        emp_by_window: Dict[str, Dict[str, Dict[str, float]]] = {}

        for tag in ("slot6", "slots5_7", "slots4_8"):
            summary = _read_json(in_dir / f"run{holdout_run}_{tag}.summary.json")
            slots = list(summary.get("slots", []))
            window = _window_label(slots)
            emp = _empirical_channels(in_dir, holdout_run, tag)
            emp_by_window[window] = emp
            run_ctx = {
                "run_id": holdout_run,
                "slots": slots,
                "bitmask_hex": summary.get("bitmask_hex", ""),
                "N_valid_by_setting": emp["N"],
                "trials_valid": sum(emp["N"].values()),
                "h5_path": str(summary.get("h5_path", "")),
                "params": params,
            }
            probs = provider_mod.compute_probabilities(run_ctx)
            model_by_window[window] = {
                "pp": {k: float(probs["P_pp"][k]) for k in KEYS},
                "p0": {k: float(probs["P_p0"][k]) for k in KEYS},
                "0p": {k: float(probs["P_0p"][k]) for k in KEYS},
            }

        for window in WINDOW_ORDER:
            mw = model_by_window[window]
            ew = emp_by_window[window]
            bounds_ok = True
            accounting_ok = True
            suppression_pp_11_lt_00 = True
            slot6_anchor_abs = []
            for k in KEYS:
                ppp = float(mw["pp"][k])
                pp0 = float(mw["p0"][k])
                p0p = float(mw["0p"][k])
                if not (0.0 <= ppp <= 1.0 and 0.0 <= pp0 <= 1.0 and 0.0 <= p0p <= 1.0):
                    bounds_ok = False
                if ppp + pp0 > 1.0 + 1e-12 or ppp + p0p > 1.0 + 1e-12 or ppp + pp0 + p0p > 1.0 + 1e-12:
                    accounting_ok = False
                if k == "11" and ppp >= float(mw["pp"]["00"]):
                    suppression_pp_11_lt_00 = False
                if window == "slot6":
                    for ch in CHANNELS:
                        slot6_anchor_abs.append(abs(float(mw[ch][k]) - float(ew[ch][k])))
                per_setting_rows.append({
                    "holdout_run": holdout_run,
                    "window": window,
                    "setting": k,
                    "P_pp": ppp,
                    "P_p0": pp0,
                    "P_0p": p0p,
                    "P_A_plus": ppp + pp0,
                    "P_B_plus": ppp + p0p,
                    "emp_pp": float(ew["pp"][k]),
                    "emp_p0": float(ew["p0"][k]),
                    "emp_0p": float(ew["0p"][k]),
                    "abs_err_pp": abs(ppp - float(ew["pp"][k])),
                    "abs_err_p0": abs(pp0 - float(ew["p0"][k])),
                    "abs_err_0p": abs(p0p - float(ew["0p"][k])),
                    "bounds_ok": "YES" if (0.0 <= ppp <= 1.0 and 0.0 <= pp0 <= 1.0 and 0.0 <= p0p <= 1.0) else "NO",
                    "accounting_ok": "YES" if (ppp + pp0 <= 1.0 + 1e-12 and ppp + p0p <= 1.0 + 1e-12 and ppp + pp0 + p0p <= 1.0 + 1e-12) else "NO",
                })
            run_window_summary.append({
                "holdout_run": holdout_run,
                "window": window,
                "bounds_ok": "YES" if bounds_ok else "NO",
                "accounting_ok": "YES" if accounting_ok else "NO",
                "suppression_pp11_lt_pp00": "YES" if suppression_pp_11_lt_00 else "NO",
                "slot6_anchor_mae": mean(slot6_anchor_abs) if slot6_anchor_abs else float("nan"),
            })

        # monotonicity by channel/setting
        for ch in CHANNELS:
            for k in KEYS:
                vals = [float(model_by_window[w][ch][k]) for w in WINDOW_ORDER]
                mono_ok = vals[0] <= vals[1] + 1e-12 and vals[1] <= vals[2] + 1e-12
                run_window_summary.append({
                    "holdout_run": holdout_run,
                    "window": f"monotonic_{ch}_{k}",
                    "bounds_ok": "YES",
                    "accounting_ok": "YES",
                    "suppression_pp11_lt_pp00": "YES",
                    "slot6_anchor_mae": float("nan") if mono_ok else -1.0,
                })

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_setting_rows[0].keys()))
        w.writeheader()
        for r in per_setting_rows:
            w.writerow(r)

    summary = {
        "provider": str(args.provider),
        "init_module": str(args.init_module),
        "profile_form": str(args.profile_form),
        "gksl": {
            "dm2": float(args.dm2),
            "theta_deg": float(args.theta_deg),
            "L0_km": float(args.L0_km),
            "E_GeV": float(args.E_GeV),
            "steps": int(args.steps),
            "gamma_km_inv": float(args.gamma_km_inv),
        },
        "summary_rows": run_window_summary,
        "global": {
            "all_bounds_ok": all(r["bounds_ok"] == "YES" for r in run_window_summary if not str(r["window"]).startswith("monotonic_")),
            "all_accounting_ok": all(r["accounting_ok"] == "YES" for r in run_window_summary if not str(r["window"]).startswith("monotonic_")),
            "all_pp11_suppressed": all(r["suppression_pp11_lt_pp00"] == "YES" for r in run_window_summary if not str(r["window"]).startswith("monotonic_")),
            "monotonic_failures": sum(1 for r in run_window_summary if str(r["window"]).startswith("monotonic_") and float(r["slot6_anchor_mae"]) < 0.0),
            "slot6_anchor_mae_mean": mean([float(r["slot6_anchor_mae"]) for r in run_window_summary if r["window"] == "slot6"]) if any(r["window"] == "slot6" for r in run_window_summary) else float("nan"),
        },
    }

    out_json = Path(args.out_json)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = [
        "# NIST CH probability accounting audit",
        "",
        f"- provider: {args.provider}",
        f"- profile_form: {args.profile_form}",
        f"- gamma_km_inv: {float(args.gamma_km_inv):.6g}",
        f"- L0_km: {float(args.L0_km):.6g}",
        "",
        "## Global",
        f"- all_bounds_ok: {'YES' if summary['global']['all_bounds_ok'] else 'NO'}",
        f"- all_accounting_ok: {'YES' if summary['global']['all_accounting_ok'] else 'NO'}",
        f"- all_pp11_suppressed: {'YES' if summary['global']['all_pp11_suppressed'] else 'NO'}",
        f"- monotonic_failures: {summary['global']['monotonic_failures']}",
        f"- slot6_anchor_mae_mean: {summary['global']['slot6_anchor_mae_mean']:.6g}",
        "",
        "## Run/window summary",
        "| holdout_run | window | bounds_ok | accounting_ok | suppression_pp11_lt_pp00 | slot6_anchor_mae |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in run_window_summary:
        md.append(
            f"| {r['holdout_run']} | {r['window']} | {r['bounds_ok']} | {r['accounting_ok']} | {r['suppression_pp11_lt_pp00']} | {r['slot6_anchor_mae']} |"
        )
    Path(args.out_md).write_text("\n".join(md), encoding="utf-8")

    print("[OK] wrote:", str(out_csv))
    print("[OK] wrote:", str(out_json))
    print("[OK] wrote:", str(args.out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
