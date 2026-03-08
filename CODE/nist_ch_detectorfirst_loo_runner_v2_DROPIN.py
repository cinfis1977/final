#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH detector-first leave-one-run-out runner — DROP-IN v2
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_N(path: Path) -> Dict[str, int]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        return {f"{int(r['a_set'])}{int(r['b_set'])}": int(float(r.get('trials_valid', r.get('trials', '0')))) for r in rdr}


def _window_label(slots: List[int]) -> str:
    if len(slots) == 1:
        return f"slot{slots[0]}"
    return f"slots{slots[0]}-{slots[-1]}"


def _slots_spec(slots: List[int]) -> str:
    if len(slots) == 1:
        return str(slots[0])
    return f"{slots[0]}-{slots[-1]}"


def _compute_J(N: Dict[str, int], probs: Dict[str, Any]) -> float:
    return float(N['00'] * probs['P_pp']['00'] - N['01'] * probs['P_p0']['01'] - N['10'] * probs['P_0p']['10'] - N['11'] * probs['P_pp']['11'])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--provider", default=r".\CODE\ch_model_prob_provider_v1_GKSL_DETECTORFIRST_V2_DROPIN.py")
    ap.add_argument("--init_module", default=r".\CODE\nist_ch_init_gksl_detectorfirst_v2_DROPIN.py")
    ap.add_argument("--out_csv", default=r".\out\nist_ch\MODEL_SCORECARD_GKSL_DETECTORFIRST_V2.csv")
    ap.add_argument("--out_md", default=r".\out\nist_ch\MODEL_SCORECARD_GKSL_DETECTORFIRST_V2.md")
    ap.add_argument("--profile_form", default="tilt_abs_quad")
    ap.add_argument("--dm2", type=float, default=0.0025)
    ap.add_argument("--theta_deg", type=float, default=45.0)
    ap.add_argument("--L0_km", type=float, default=1.0)
    ap.add_argument("--E_GeV", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--gamma_km_inv", type=float, default=1.0)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    provider = _load_module(Path(args.provider), "detectorfirst_provider_v2")
    init_mod = _load_module(Path(args.init_module), "detectorfirst_init_v2")
    real_runs = init_mod.discover_real_runs(in_dir)
    rates, meta = init_mod.collect_window_rates_and_meta(in_dir)

    rows: List[Dict[str, Any]] = []
    for holdout in real_runs:
        gksl = {"dm2": float(args.dm2), "theta_deg": float(args.theta_deg), "L0_km": float(args.L0_km), "E_GeV": float(args.E_GeV), "steps": int(args.steps), "gamma_km_inv": float(args.gamma_km_inv), "use_microphysics": False}
        bundle, _report = init_mod.build_detectorfirst_v2_bundle(rates, meta, [r for r in real_runs if r != holdout], [holdout], str(args.profile_form), gksl)
        for tag in ("slot6", "slots5_7", "slots4_8"):
            summary = _read_json(in_dir / f"run{holdout}_{tag}.summary.json")
            N = _read_N(in_dir / f"run{holdout}_{tag}.counts.csv")
            N_valid = sum(N.values())
            params = dict(bundle["defaults"])
            params.update(bundle["runs"][holdout])
            probs = provider.compute_probabilities({"run_id": holdout, "slots": list(summary.get('slots', [])), "bitmask_hex": summary.get('bitmask_hex', ''), "N_valid_by_setting": N, "trials_valid": N_valid, "h5_path": str(summary.get('h5_path', '')), "params": params})
            J_model = _compute_J(N, probs)
            J_data = int(summary.get("J", 0))
            jd = float(J_data) * 1e6 / N_valid if N_valid else 0.0
            jm = float(J_model) * 1e6 / N_valid if N_valid else 0.0
            rows.append({
                "holdout_run": holdout,
                "window": _window_label(list(summary.get('slots', []))),
                "slots": _slots_spec(list(summary.get('slots', []))),
                "trials_valid": N_valid,
                "J_data": J_data,
                "J_model": float(J_model),
                "delta_J": float(J_model - J_data),
                "j_data_per_1M": jd,
                "j_model_per_1M": jm,
                "delta_j_per_1M": float(jm - jd),
                "sign_ok": "YES" if (J_model > 0) == (J_data > 0) else "NO",
                "provider": probs.get("__provider_label__", ""),
                "profile_form": args.profile_form,
                "L0_km": float(args.L0_km),
                "gamma_km_inv": float(args.gamma_km_inv),
            })

    rows.sort(key=lambda r: (r['holdout_run'], r['window']))
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    out_md = Path(args.out_md)
    headers = ["holdout_run", "window", "J_data", "J_model", "delta_j_per_1M", "sign_ok", "profile_form", "L0_km", "gamma_km_inv"]
    md = ["# NIST CH detector-first GKSL LOO scorecard v2", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        md.append("| " + " | ".join(str(r[h]).replace('|', '\\|') for h in headers) + " |")
    out_md.write_text("\n".join(md), encoding='utf-8')
    print("[OK] wrote:", str(out_csv))
    print("[OK] wrote:", str(out_md))
    print("rows:", len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
