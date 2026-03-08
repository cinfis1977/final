#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH GKSL detector-first init — DROP-IN v1

Fits GLOBAL channel parameters from training runs only.
No target-run empirical seed is used by the provider.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from itertools import product
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Tuple


KEYS = ("00", "01", "10", "11")
CHANNELS = ("pp", "p0", "0p")
FORMS = ("tilt_abs_quad", "tilt_abs", "tilt_quad", "abs_quad")
WINDOWS = {"slot6": [6], "slots5_7": [5, 6, 7], "slots4_8": [4, 5, 6, 7, 8]}


def _clip01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return float(x)


def _safe_rate(num: int, den: int) -> float:
    return float(num) / float(den) if den > 0 else 0.0


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_training_stub(summary: Dict[str, Any]) -> bool:
    h5 = str(summary.get("h5_path", ""))
    if "training" in h5.lower():
        return True
    scanned = int(summary.get("processed_trials_total_scanned", summary.get("processed_trials_scanned", 0)) or 0)
    return scanned < 100000


def discover_real_runs(in_dir: Path) -> List[str]:
    out = []
    for sp in sorted(in_dir.glob("run*_slot6.summary.json")):
        if _is_training_stub(_read_json(sp)):
            continue
        out.append(sp.name.replace("run", "").replace("_slot6.summary.json", ""))
    return sorted(set(out))


def _read_counts(path: Path) -> Dict[str, Dict[str, int]]:
    out = {"N": {k: 0 for k in KEYS}, "A": {k: 0 for k in KEYS}, "B": {k: 0 for k in KEYS}, "AB": {k: 0 for k in KEYS}}
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            k = f"{int(row['a_set'])}{int(row['b_set'])}"
            out["N"][k] = int(float(row.get("trials_valid", row.get("trials", "0"))))
            out["A"][k] = int(float(row.get("alice_detect", "0")))
            out["B"][k] = int(float(row.get("bob_detect", "0")))
            out["AB"][k] = int(float(row.get("both_detect", "0")))
    return out


def collect_window_rates(in_dir: Path) -> Dict[str, Dict[str, Dict[str, Dict[str, float]]]]:
    out: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    for run_id in discover_real_runs(in_dir):
        out[run_id] = {}
        for tag in WINDOWS:
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
            out[run_id][tag] = {
                "pp": {k: _clip01(_safe_rate(pp[k], N[k])) for k in KEYS},
                "p0": {k: _clip01(_safe_rate(p0[k], N[k])) for k in KEYS},
                "0p": {k: _clip01(_safe_rate(op[k], N[k])) for k in KEYS},
            }
    return out


def _infer_eff(p1: float, pw: float) -> float | None:
    p1 = _clip01(p1)
    pw = _clip01(pw)
    if p1 <= 0.0 or p1 >= 1.0 or pw <= 0.0 or pw >= 1.0:
        return None
    den = math.log(max(1e-300, 1.0 - p1))
    if den == 0.0:
        return None
    eff = math.log(max(1e-300, 1.0 - pw)) / den
    if not math.isfinite(eff) or eff < 0.0:
        return None
    return float(eff)


def _profile_scale(d: float, form: str, cfg: Dict[str, float], gamma: float) -> float:
    tilt = float(cfg.get("tilt", 0.0))
    abs_km = max(0.0, float(cfg.get("abs_km", 0.0)))
    quad_km = max(0.0, float(cfg.get("quad_km", 0.0)))
    if form == "tilt_abs":
        log_scale = tilt * d - gamma * abs_km * abs(d)
    elif form == "tilt_quad":
        log_scale = tilt * d - gamma * quad_km * d * d
    elif form == "abs_quad":
        log_scale = -gamma * (abs_km * abs(d) + quad_km * d * d)
    else:
        log_scale = tilt * d - gamma * (abs_km * abs(d) + quad_km * d * d)
    return float(math.exp(max(-50.0, min(50.0, log_scale))))


def _window_prob(base_rate: float, offsets: Iterable[int], form: str, cfg: Dict[str, float], gamma: float) -> float:
    prod = 1.0
    for d in offsets:
        prod *= (1.0 - _clip01(base_rate * _profile_scale(float(d), form, cfg, gamma)))
    return _clip01(1.0 - prod)


def _fit_cfg(train_p1: List[float], targets: List[Tuple[float, float]], form: str, gamma: float) -> Dict[str, float]:
    base_rate = _clip01(median(train_p1) if train_p1 else 0.0)
    tilt_grid = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]
    amp_grid = [0.0, 1.0e-3, 1.0e-2, 1.0e-1, 1.0, 10.0, 100.0]
    best = {"base_rate": base_rate, "tilt": 0.0, "linear_km": 0.0, "abs_km": 0.0, "quad_km": 0.0}
    best_err = float("inf")
    if form == "tilt_abs":
        grid = product(tilt_grid, amp_grid)
    elif form == "tilt_quad":
        grid = product(tilt_grid, amp_grid)
    elif form == "abs_quad":
        grid = product(amp_grid, amp_grid)
    else:
        grid = product(tilt_grid, amp_grid, amp_grid)
    offs3 = [-1, 0, 1]
    offs5 = [-2, -1, 0, 1, 2]
    for vals in grid:
        if form == "tilt_abs":
            cfg = {"base_rate": base_rate, "tilt": vals[0], "linear_km": 0.0, "abs_km": vals[1], "quad_km": 0.0}
        elif form == "tilt_quad":
            cfg = {"base_rate": base_rate, "tilt": vals[0], "linear_km": 0.0, "abs_km": 0.0, "quad_km": vals[1]}
        elif form == "abs_quad":
            cfg = {"base_rate": base_rate, "tilt": 0.0, "linear_km": 0.0, "abs_km": vals[0], "quad_km": vals[1]}
        else:
            cfg = {"base_rate": base_rate, "tilt": vals[0], "linear_km": 0.0, "abs_km": vals[1], "quad_km": vals[2]}
        err = 0.0
        for p3, p5 in targets:
            pred3 = _window_prob(base_rate, offs3, form, cfg, gamma)
            pred5 = _window_prob(base_rate, offs5, form, cfg, gamma)
            err += (pred3 - p3) ** 2 + (pred5 - p5) ** 2
        if err < best_err:
            best_err = err
            best = dict(cfg)
    return best


def build_detectorfirst_bundle(window_rates: Dict[str, Dict[str, Dict[str, Dict[str, float]]]], train_runs: List[str], holdout_runs: List[str], profile_form: str, gksl: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    all_runs = sorted(window_rates.keys())
    if not train_runs:
        train_runs = [r for r in all_runs if r not in holdout_runs]
    gamma = max(0.0, float(gksl.get("gamma_km_inv", 0.0) or 0.0))
    global_params: Dict[str, Dict[str, Dict[str, float]]] = {}
    report: Dict[str, Any] = {"train_runs": train_runs, "holdout_runs": holdout_runs, "profile_form": profile_form, "gksl": gksl, "fits": {}}
    for channel in CHANNELS:
        global_params[channel] = {}
        report["fits"][channel] = {}
        for k in KEYS:
            p1s = [float(window_rates[r]["slot6"][channel][k]) for r in train_runs]
            targets = [(float(window_rates[r]["slots5_7"][channel][k]), float(window_rates[r]["slots4_8"][channel][k])) for r in train_runs]
            fit = _fit_cfg(p1s, targets, profile_form, gamma)
            global_params[channel][k] = fit
            report["fits"][channel][k] = fit
    bundle = {
        "defaults": {
            "bridge_version": "GKSL_DETECTORFIRST_V1",
            "center_slot": 6,
            "profile_form": profile_form,
            "gksl": dict(gksl),
            "global_channel_params": global_params,
            "train_runs": train_runs,
            "holdout_runs": holdout_runs,
        },
        "runs": {},
    }
    return bundle, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--out_json", default=r".\out\nist_ch\model_params_gksl_detectorfirst_v1.json")
    ap.add_argument("--train_runs", default="")
    ap.add_argument("--holdout_runs", default="")
    ap.add_argument("--profile_form", default="tilt_abs_quad", choices=list(FORMS))
    ap.add_argument("--dm2", type=float, default=0.0025)
    ap.add_argument("--theta_deg", type=float, default=45.0)
    ap.add_argument("--L0_km", type=float, default=1.0)
    ap.add_argument("--E_GeV", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--gamma_km_inv", type=float, default=1.0)
    args = ap.parse_args()

    window_rates = collect_window_rates(Path(args.in_dir))
    gksl = {"dm2": float(args.dm2), "theta_deg": float(args.theta_deg), "L0_km": float(args.L0_km), "E_GeV": float(args.E_GeV), "steps": int(args.steps), "gamma_km_inv": float(args.gamma_km_inv), "use_microphysics": False}
    train_runs = [x.strip() for x in args.train_runs.split(",") if x.strip()]
    holdout_runs = [x.strip() for x in args.holdout_runs.split(",") if x.strip()]
    bundle, report = build_detectorfirst_bundle(window_rates, train_runs, holdout_runs, str(args.profile_form), gksl)
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    rep = out_json.parent / "gksl_detectorfirst_v1_report.json"
    rep.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[OK] wrote:", str(out_json))
    print("[OK] wrote:", str(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
