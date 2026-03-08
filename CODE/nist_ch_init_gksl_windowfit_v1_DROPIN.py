#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH GKSL window-fit init — DROP-IN v1

Lightweight alternative to HDF5-wide scans.
Uses only the already-built empirical windows:
- slot6
- slots5_7
- slots4_8

It fits a strict-holdout predictive bridge from target run slot6 seeds plus a
training-only GKSL-modulated profile form.

The emitted params JSON is compatible with
`ch_model_prob_provider_v1_GKSL_PREDICTIVE_V3_DROPIN.py`.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from itertools import product
from pathlib import Path
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


def _discover_real_runs(in_dir: Path) -> List[str]:
    out = []
    for sp in sorted(in_dir.glob("run*_slot6.summary.json")):
        summary = _read_json(sp)
        if _is_training_stub(summary):
            continue
        stem = sp.name.replace("run", "").replace("_slot6.summary.json", "")
        out.append(stem)
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


def _channel_rates(in_dir: Path, run_id: str, tag: str) -> Dict[str, Dict[str, float]]:
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
        "pp": {k: _clip01(_safe_rate(pp[k], N[k])) for k in KEYS},
        "p0": {k: _clip01(_safe_rate(p0[k], N[k])) for k in KEYS},
        "0p": {k: _clip01(_safe_rate(op[k], N[k])) for k in KEYS},
    }


def collect_window_rates(in_dir: Path) -> Dict[str, Dict[str, Dict[str, Dict[str, float]]]]:
    out: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    for run_id in _discover_real_runs(in_dir):
        out[run_id] = {tag: _channel_rates(in_dir, run_id, tag) for tag in WINDOWS}
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
    return float(eff) if math.isfinite(eff) and eff >= 0.0 else None


def _window_offsets(tag: str) -> List[int]:
    slots = WINDOWS[tag]
    return [int(s) - 6 for s in slots]


def _profile_scale(d: int, form: str, profile: Dict[str, float], gksl: Dict[str, Any]) -> float:
    dd = float(d)
    gamma = max(0.0, float(gksl.get("gamma_km_inv", 0.0) or 0.0))
    tilt = float(profile.get("tilt", 0.0))
    linear = float(profile.get("linear_km", 0.0))
    abs_km = max(0.0, float(profile.get("abs_km", 0.0)))
    quad_km = max(0.0, float(profile.get("quad_km", 0.0)))
    if form == "tilt_abs_quad":
        log_scale = tilt * dd - gamma * (abs_km * abs(dd) + quad_km * dd * dd)
    elif form == "tilt_abs":
        log_scale = tilt * dd - gamma * (abs_km * abs(dd))
    elif form == "tilt_quad":
        log_scale = tilt * dd - gamma * (quad_km * dd * dd)
    elif form == "abs_quad":
        log_scale = -gamma * (abs_km * abs(dd) + quad_km * dd * dd)
    else:
        log_scale = tilt * dd + linear * dd - gamma * (abs_km * abs(dd) + quad_km * dd * dd)
    return float(math.exp(max(-50.0, min(50.0, log_scale))))


def _model_eff(offsets: Iterable[int], form: str, profile: Dict[str, float], gksl: Dict[str, Any]) -> float:
    return sum(_profile_scale(int(d), form, profile, gksl) for d in offsets)


def _fit_profile(samples: List[Tuple[float, float]], form: str, gksl: Dict[str, Any]) -> Dict[str, float]:
    # samples: (target_eff3, target_eff5)
    if not samples:
        return {"tilt": 0.0, "linear_km": 0.0, "abs_km": 0.0, "quad_km": 0.0}
    tilt_grid = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]
    abs_grid = [0.0, 1.0e-3, 1.0e-2, 1.0e-1, 1.0, 10.0, 100.0]
    quad_grid = [0.0, 1.0e-3, 1.0e-2, 1.0e-1, 1.0, 10.0, 100.0]
    best = {"tilt": 0.0, "linear_km": 0.0, "abs_km": 0.0, "quad_km": 0.0}
    best_err = float("inf")
    if form == "tilt_abs":
        grid = product(tilt_grid, abs_grid)
    elif form == "tilt_quad":
        grid = product(tilt_grid, quad_grid)
    elif form == "abs_quad":
        grid = product(abs_grid, quad_grid)
    else:
        grid = product(tilt_grid, abs_grid, quad_grid)

    offs3 = _window_offsets("slots5_7")
    offs5 = _window_offsets("slots4_8")
    for vals in grid:
        vv = list(vals)
        if form == "tilt_abs":
            profile = {"tilt": vv[0], "linear_km": 0.0, "abs_km": vv[1], "quad_km": 0.0}
        elif form == "tilt_quad":
            profile = {"tilt": vv[0], "linear_km": 0.0, "abs_km": 0.0, "quad_km": vv[1]}
        elif form == "abs_quad":
            profile = {"tilt": 0.0, "linear_km": 0.0, "abs_km": vv[0], "quad_km": vv[1]}
        else:
            profile = {"tilt": vv[0], "linear_km": 0.0, "abs_km": vv[1], "quad_km": vv[2]}
        eff3 = _model_eff(offs3, form, profile, gksl)
        eff5 = _model_eff(offs5, form, profile, gksl)
        err = 0.0
        for t3, t5 in samples:
            err += (eff3 - t3) ** 2 + (eff5 - t5) ** 2
        if err < best_err:
            best_err = err
            best = dict(profile)
    return best


def build_windowfit_bundle(in_dir: Path, window_rates: Dict[str, Dict[str, Dict[str, Dict[str, float]]]], train_runs: List[str], holdout_runs: List[str], profile_form: str, gksl: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if profile_form not in FORMS:
        raise SystemExit(f"Unsupported profile_form: {profile_form}")
    all_runs = sorted(window_rates.keys())
    if not train_runs:
        train_runs = [r for r in all_runs if r not in holdout_runs]
    report: Dict[str, Any] = {"train_runs": train_runs, "holdout_runs": holdout_runs, "profile_form": profile_form, "gksl": gksl, "fits": {}}
    profiles: Dict[str, Dict[str, float]] = {}
    for channel in CHANNELS:
        samples = []
        for run_id in train_runs:
            for k in KEYS:
                p1 = float(window_rates[run_id]["slot6"][channel][k])
                p3 = float(window_rates[run_id]["slots5_7"][channel][k])
                p5 = float(window_rates[run_id]["slots4_8"][channel][k])
                e3 = _infer_eff(p1, p3)
                e5 = _infer_eff(p1, p5)
                if e3 is None or e5 is None:
                    continue
                samples.append((e3, e5))
        fit = _fit_profile(samples, profile_form, gksl)
        profiles[channel] = fit
        report["fits"][channel] = {"n_samples": len(samples), "fit": fit}

    bundle = {
        "defaults": {
            "bridge_version": "GKSL_WINDOWFIT_V1 (holdout bridge)",
            "center_slot": 6,
            "profile_scope": "by_channel",
            "profile_form": profile_form,
            "train_runs": train_runs,
            "holdout_runs": holdout_runs,
            "gksl": dict(gksl),
            "profiles": profiles,
        },
        "runs": {},
    }
    for run_id in all_runs:
        bundle["runs"][run_id] = {
            "p_pp_seed_by_setting": dict(window_rates[run_id]["slot6"]["pp"]),
            "p_p0_seed_by_setting": dict(window_rates[run_id]["slot6"]["p0"]),
            "p_0p_seed_by_setting": dict(window_rates[run_id]["slot6"]["0p"]),
        }
    return bundle, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--out_json", default=r".\out\nist_ch\model_params_gksl_windowfit_v1.json")
    ap.add_argument("--train_runs", default="")
    ap.add_argument("--holdout_runs", default="")
    ap.add_argument("--profile_form", default="tilt_abs_quad", choices=list(FORMS))
    ap.add_argument("--dm2", type=float, default=0.0025)
    ap.add_argument("--theta_deg", type=float, default=45.0)
    ap.add_argument("--L0_km", type=float, default=1.0)
    ap.add_argument("--E_GeV", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--gamma_km_inv", type=float, default=0.0)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    window_rates = collect_window_rates(in_dir)
    gksl = {
        "dm2": float(args.dm2),
        "theta_deg": float(args.theta_deg),
        "L0_km": float(args.L0_km),
        "E_GeV": float(args.E_GeV),
        "steps": int(args.steps),
        "gamma_km_inv": float(args.gamma_km_inv),
        "use_microphysics": False,
    }
    train_runs = [x for x in args.train_runs.split(",") if x.strip()]
    holdout_runs = [x for x in args.holdout_runs.split(",") if x.strip()]
    bundle, report = build_windowfit_bundle(in_dir, window_rates, train_runs, holdout_runs, str(args.profile_form), gksl)
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    rep = out_json.parent / "gksl_windowfit_v1_report.json"
    rep.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[OK] wrote:", str(out_json))
    print("[OK] wrote:", str(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
