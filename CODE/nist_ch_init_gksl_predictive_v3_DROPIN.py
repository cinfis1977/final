#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH GKSL-modulated predictive init — DROP-IN v3

Adds profile-form support and reusable cached single-slot extraction so a
systematic gamma/L0/profile scan can be run without re-reading HDF5 for every
candidate.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

try:
    import h5py  # type: ignore
except Exception as e:
    raise SystemExit("h5py is required. Install: pip install h5py") from e


KEYS = ("00", "01", "10", "11")
CHANNELS = ("pp", "p0", "0p")
FORMS = ("tilt_abs_quad", "tilt_abs", "tilt_quad", "abs_quad", "linear_abs_quad")


def _clip01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return float(x)


def _safe_rate(num: int, den: int) -> float:
    return (float(num) / float(den)) if den > 0 else 0.0


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_training_stub(summary: Dict[str, Any]) -> bool:
    h5 = str(summary.get("h5_path", ""))
    if "training" in h5.lower():
        return True
    scanned = int(summary.get("processed_trials_total_scanned", summary.get("processed_trials_scanned", 0)) or 0)
    return scanned < 100000


def _parse_run_list(spec: str) -> List[str]:
    if not spec:
        return []
    return sorted({part.strip() for part in spec.split(",") if part.strip()})


def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(10):
        if (cur / "mastereq" / "__init__.py").exists():
            return cur
        if (cur / "integration_artifacts" / "mastereq" / "__init__.py").exists():
            return cur
        cur = cur.parent
    raise RuntimeError("Could not locate repo root containing mastereq package.")


def _ensure_repo_on_syspath() -> None:
    here = Path(__file__).resolve()
    root = _find_repo_root(here.parent)
    entry = str(root) if (root / "mastereq" / "__init__.py").exists() else str(root / "integration_artifacts")
    if entry not in sys.path:
        sys.path.insert(0, entry)


def _resolve_gamma(gksl: Dict[str, Any]) -> float:
    gamma = gksl.get("gamma_km_inv", None)
    if gamma is not None:
        return max(0.0, float(gamma))
    _ensure_repo_on_syspath()
    from mastereq.microphysics import gamma_km_inv_from_n_sigma_v, sigma_entanglement_reference_cm2

    E_GeV = float(gksl.get("E_GeV", 1.0))
    visibility_ref = float(gksl.get("visibility_ref", 0.9))
    sigma = sigma_entanglement_reference_cm2(E_GeV, visibility_ref)
    return max(0.0, float(gamma_km_inv_from_n_sigma_v(float(gksl.get("n_cm3", 1.0e18)), float(sigma), float(gksl.get("v_cm_s", 3.0e10)))))


def _dataset(h5: Any, path: str) -> Any:
    return h5[path] if path in h5 else h5["/" + path]


def _discover_runs(in_dir: Path) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for sp in sorted(in_dir.glob("run*_slot6.summary.json")):
        m = re.search(r"run(\d{2}_\d{2})_slot6\.summary\.json$", sp.name)
        if not m:
            continue
        run_id = m.group(1)
        summary = _read_json(sp)
        h5_path = Path(str(summary.get("h5_path", "")))
        if not h5_path.is_absolute():
            h5_path = (Path.cwd() / h5_path).resolve()
        out[run_id] = {
            "run_id": run_id,
            "summary_path": sp,
            "summary": summary,
            "h5_path": h5_path,
            "is_training_stub": _is_training_stub(summary),
        }
    if not out:
        raise SystemExit(f"No run*_slot6.summary.json found in {in_dir}")
    return out


def map_settings_to_01_auto(arr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    a = np.asarray(arr).astype(np.int32, copy=False)
    u = np.unique(a)
    if set(u.tolist()) <= {0, 1}:
        return a.astype(np.int8, copy=False), np.ones(a.shape[0], dtype=bool)
    if set(u.tolist()) <= {0, 1, 2, 3} and (1 in u or 2 in u or 3 in u):
        out = np.full(a.shape[0], -1, dtype=np.int8)
        out[a == 1] = 0
        out[a == 2] = 1
        valid = out >= 0
        return out, valid
    if len(u) == 2:
        u_sorted = sorted(u.tolist())
        mp = {u_sorted[0]: 0, u_sorted[1]: 1}
        out = np.vectorize(lambda v: mp[int(v)])(a).astype(np.int8)
        return out, np.ones(a.shape[0], dtype=bool)
    out = np.full(a.shape[0], -1, dtype=np.int8)
    return out, np.zeros(a.shape[0], dtype=bool)


def _empty_slot_payload() -> Dict[int, Dict[str, Dict[str, int]]]:
    out: Dict[int, Dict[str, Dict[str, int]]] = {}
    for slot in range(1, 17):
        out[slot] = {
            "N": {k: 0 for k in KEYS},
            "pp": {k: 0 for k in KEYS},
            "p0": {k: 0 for k in KEYS},
            "0p": {k: 0 for k in KEYS},
        }
    return out


def _collect_single_slot_channels(h5_path: Path, chunk: int) -> Dict[int, Dict[str, Dict[str, int]]]:
    out = _empty_slot_payload()
    key_order = ["00", "01", "10", "11"]
    with h5py.File(str(h5_path), "r") as h5:
        Aset = _dataset(h5, "alice/settings")
        Bset = _dataset(h5, "bob/settings")
        Aclk = _dataset(h5, "alice/clicks")
        Bclk = _dataset(h5, "bob/clicks")
        N = min(int(Aset.shape[0]), int(Bset.shape[0]), int(Aclk.shape[0]), int(Bclk.shape[0]))
        slot_masks = {slot: np.uint16(1 << (slot - 1)) for slot in range(1, 17)}

        for s in range(0, N, int(chunk)):
            e = min(N, s + int(chunk))
            a_raw = np.asarray(Aset[s:e], dtype=np.int32)
            b_raw = np.asarray(Bset[s:e], dtype=np.int32)
            a_set, a_valid = map_settings_to_01_auto(a_raw)
            b_set, b_valid = map_settings_to_01_auto(b_raw)
            valid = a_valid & b_valid
            if not np.any(valid):
                continue
            a_set = a_set[valid]
            b_set = b_set[valid]
            a_bits = np.asarray(Aclk[s:e], dtype=np.uint16)[valid]
            b_bits = np.asarray(Bclk[s:e], dtype=np.uint16)[valid]
            setting_idx = (a_set.astype(np.int8) << 1) | b_set.astype(np.int8)
            totals = np.bincount(setting_idx, minlength=4)
            for slot in range(1, 17):
                mask = slot_masks[slot]
                a_on = (a_bits & mask) != 0
                b_on = (b_bits & mask) != 0
                pp_counts = np.bincount(setting_idx[a_on & b_on], minlength=4)
                p0_counts = np.bincount(setting_idx[a_on & (~b_on)], minlength=4)
                op_counts = np.bincount(setting_idx[(~a_on) & b_on], minlength=4)
                for idx, k in enumerate(key_order):
                    out[slot]["N"][k] += int(totals[idx])
                    out[slot]["pp"][k] += int(pp_counts[idx])
                    out[slot]["p0"][k] += int(p0_counts[idx])
                    out[slot]["0p"][k] += int(op_counts[idx])
    return out


def _rates_from_counts(slot_counts: Dict[int, Dict[str, Dict[str, int]]]) -> Dict[int, Dict[str, Dict[str, float]]]:
    out: Dict[int, Dict[str, Dict[str, float]]] = {}
    for slot, payload in slot_counts.items():
        out[slot] = {}
        for channel in CHANNELS:
            out[slot][channel] = {k: _clip01(_safe_rate(int(payload[channel][k]), int(payload["N"][k]))) for k in KEYS}
    return out


def collect_all_run_rates(in_dir: Path, chunk: int) -> Tuple[Dict[str, Dict[int, Dict[str, Dict[str, float]]]], Dict[str, Dict[str, Any]]]:
    runs = _discover_runs(in_dir)
    rates_by_run: Dict[str, Dict[int, Dict[str, Dict[str, float]]]] = {}
    for run_id, meta in runs.items():
        if meta["is_training_stub"]:
            continue
        h5_path = Path(meta["h5_path"])
        if not h5_path.exists():
            raise SystemExit(f"HDF5 not found for run {run_id}: {h5_path}")
        rates_by_run[run_id] = _rates_from_counts(_collect_single_slot_channels(h5_path, chunk=chunk))
    run_meta = {rid: meta for rid, meta in runs.items() if not meta["is_training_stub"]}
    return rates_by_run, run_meta


def _feature_matrix(form: str, gamma_km_inv: float, d: int) -> List[float]:
    g = float(gamma_km_inv)
    dd = float(d)
    if form == "tilt_abs_quad":
        return [dd, -g * abs(dd), -g * dd * dd]
    if form == "tilt_abs":
        return [dd, -g * abs(dd)]
    if form == "tilt_quad":
        return [dd, -g * dd * dd]
    if form == "abs_quad":
        return [-g * abs(dd), -g * dd * dd]
    if form == "linear_abs_quad":
        return [dd, dd, -g * abs(dd), -g * dd * dd]
    raise ValueError(f"Unsupported form: {form}")


def _fit_form(samples: List[Tuple[int, float]], form: str, gamma_km_inv: float) -> Dict[str, float]:
    good = []
    for d, ratio in samples:
        if d == 0:
            continue
        r = float(ratio)
        if not math.isfinite(r) or r <= 0.0:
            continue
        good.append((int(d), min(max(r, 1.0e-12), 1.0e12)))
    if len(good) < 2:
        return {"tilt": 0.0, "linear_km": 0.0, "abs_km": 0.0, "quad_km": 0.0}
    X = []
    y = []
    for d, r in good:
        X.append(_feature_matrix(form, gamma_km_inv, d))
        y.append(math.log(r))
    Xa = np.asarray(X, dtype=float)
    ya = np.asarray(y, dtype=float)
    try:
        coef, *_ = np.linalg.lstsq(Xa, ya, rcond=None)
    except Exception:
        coef = np.zeros(Xa.shape[1], dtype=float)
    coef = np.asarray(coef, dtype=float)
    out = {"tilt": 0.0, "linear_km": 0.0, "abs_km": 0.0, "quad_km": 0.0}
    if form == "tilt_abs_quad":
        out["tilt"] = float(coef[0])
        out["abs_km"] = max(0.0, float(coef[1]))
        out["quad_km"] = max(0.0, float(coef[2]))
    elif form == "tilt_abs":
        out["tilt"] = float(coef[0])
        out["abs_km"] = max(0.0, float(coef[1]))
    elif form == "tilt_quad":
        out["tilt"] = float(coef[0])
        out["quad_km"] = max(0.0, float(coef[1]))
    elif form == "abs_quad":
        out["abs_km"] = max(0.0, float(coef[0]))
        out["quad_km"] = max(0.0, float(coef[1]))
    elif form == "linear_abs_quad":
        out["tilt"] = float(coef[0])
        out["linear_km"] = float(coef[1])
        out["abs_km"] = max(0.0, float(coef[2]))
        out["quad_km"] = max(0.0, float(coef[3]))
    for k, v in list(out.items()):
        if not math.isfinite(v):
            out[k] = 0.0
    return out


def _profile_samples(rates_by_run: Dict[str, Dict[int, Dict[str, Dict[str, float]]]], train_runs: Iterable[str], center_slot: int, channel: str, scope: str, setting: str | None = None) -> List[Tuple[int, float]]:
    samples: List[Tuple[int, float]] = []
    for run_id in train_runs:
        slot_map = rates_by_run[run_id]
        if scope == "by_channel_setting":
            if setting is None:
                continue
            seed = float(slot_map[center_slot][channel][setting])
            if seed <= 0.0:
                continue
            for slot in sorted(slot_map.keys()):
                samples.append((slot - center_slot, float(slot_map[slot][channel][setting]) / seed))
        else:
            for k in KEYS:
                seed = float(slot_map[center_slot][channel][k])
                if seed <= 0.0:
                    continue
                for slot in sorted(slot_map.keys()):
                    samples.append((slot - center_slot, float(slot_map[slot][channel][k]) / seed))
    return samples


def _fit_profiles(rates_by_run: Dict[str, Dict[int, Dict[str, Dict[str, float]]]], train_runs: List[str], center_slot: int, profile_scope: str, profile_form: str, gamma_km_inv: float) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    profiles: Dict[str, Any] = {}
    report: Dict[str, Any] = {}
    for channel in CHANNELS:
        if profile_scope == "by_channel_setting":
            profiles[channel] = {}
            report[channel] = {}
            for k in KEYS:
                samples = _profile_samples(rates_by_run, train_runs, center_slot, channel, profile_scope, setting=k)
                fit = _fit_form(samples, profile_form, gamma_km_inv)
                profiles[channel][k] = fit
                report[channel][k] = {"n_samples": len(samples), "fit": fit}
        else:
            samples = _profile_samples(rates_by_run, train_runs, center_slot, channel, profile_scope)
            fit = _fit_form(samples, profile_form, gamma_km_inv)
            profiles[channel] = fit
            report[channel] = {"n_samples": len(samples), "fit": fit}
    return profiles, report


def _empirical_window_counts(in_dir: Path, run_id: str, tag: str) -> Dict[str, Any]:
    path = in_dir / f"run{run_id}_{tag}.counts.csv"
    if not path.exists():
        return {}
    out = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            k = f"{int(row['a_set'])}{int(row['b_set'])}"
            n = int(float(row.get("trials_valid", row.get("trials", "0"))))
            a = int(float(row.get("alice_detect", "0")))
            b = int(float(row.get("bob_detect", "0")))
            ab = int(float(row.get("both_detect", "0")))
            out[k] = {"N": n, "pp": _clip01(_safe_rate(ab, n)), "p0": _clip01(_safe_rate(max(0, a - ab), n)), "0p": _clip01(_safe_rate(max(0, b - ab), n))}
    return out


def _predict_window(seed: float, slots: Iterable[int], center_slot: int, profile: Dict[str, float], profile_form: str, gamma_km_inv: float) -> float:
    prod = 1.0
    seed = _clip01(seed)
    for slot in slots:
        d = float(int(slot) - int(center_slot))
        tilt = float(profile.get("tilt", 0.0))
        linear = float(profile.get("linear_km", 0.0))
        abs_km = max(0.0, float(profile.get("abs_km", 0.0)))
        quad_km = max(0.0, float(profile.get("quad_km", 0.0)))
        if profile_form == "tilt_abs_quad":
            log_scale = tilt * d - gamma_km_inv * (abs_km * abs(d) + quad_km * d * d)
        elif profile_form == "tilt_abs":
            log_scale = tilt * d - gamma_km_inv * (abs_km * abs(d))
        elif profile_form == "tilt_quad":
            log_scale = tilt * d - gamma_km_inv * (quad_km * d * d)
        elif profile_form == "abs_quad":
            log_scale = -gamma_km_inv * (abs_km * abs(d) + quad_km * d * d)
        elif profile_form == "linear_abs_quad":
            log_scale = tilt * d + linear * d - gamma_km_inv * (abs_km * abs(d) + quad_km * d * d)
        else:
            raise ValueError(f"Unsupported form: {profile_form}")
        p = _clip01(seed * math.exp(max(-50.0, min(50.0, log_scale))))
        prod *= (1.0 - p)
    return _clip01(1.0 - prod)


def build_gksl_param_bundle_from_rates(*, rates_by_run: Dict[str, Dict[int, Dict[str, Dict[str, float]]]], run_meta: Dict[str, Dict[str, Any]], in_dir: Path, center_slot: int, profile_scope: str, profile_form: str, train_runs: List[str], holdout_runs: List[str], gksl: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    all_runs = sorted(run_meta.keys())
    if not train_runs:
        train_runs = [r for r in all_runs if r not in holdout_runs]
    train_runs = [r for r in train_runs if r in rates_by_run]
    holdout_runs = [r for r in holdout_runs if r in rates_by_run]
    if not train_runs:
        raise SystemExit("No training runs left after applying holdout/train filters.")
    if profile_form not in FORMS:
        raise SystemExit(f"Unsupported profile_form: {profile_form}")

    gamma_km_inv = _resolve_gamma(gksl)
    profiles, fit_report = _fit_profiles(rates_by_run, train_runs, center_slot, profile_scope, profile_form, gamma_km_inv)

    bundle: Dict[str, Any] = {
        "defaults": {
            "bridge_version": "GKSL_PREDICTIVE_V3 (holdout bridge)",
            "note": "Uses exact slot6 seeds plus training-only profile fit; target wide windows are excluded from calibration.",
            "center_slot": int(center_slot),
            "profile_scope": str(profile_scope),
            "profile_form": str(profile_form),
            "train_runs": train_runs,
            "holdout_runs": holdout_runs,
            "gksl": dict(gksl, gamma_km_inv=gamma_km_inv),
            "profiles": profiles,
        },
        "runs": {},
    }

    window_eval: Dict[str, Any] = {}
    for run_id in all_runs:
        rates = rates_by_run[run_id]
        bundle["runs"][run_id] = {
            "seed_source": "exact single-slot counts from original HDF5 at center_slot",
            "p_pp_seed_by_setting": {k: float(rates[center_slot]["pp"][k]) for k in KEYS},
            "p_p0_seed_by_setting": {k: float(rates[center_slot]["p0"][k]) for k in KEYS},
            "p_0p_seed_by_setting": {k: float(rates[center_slot]["0p"][k]) for k in KEYS},
        }
        per_run = {}
        for tag, slots in (("slot6", [6]), ("slots5_7", [5, 6, 7]), ("slots4_8", [4, 5, 6, 7, 8])):
            emp = _empirical_window_counts(in_dir, run_id, tag)
            if not emp:
                continue
            per_run[tag] = {}
            for channel in CHANNELS:
                per_run[tag][channel] = {}
                for k in KEYS:
                    profile = profiles[channel][k] if profile_scope == "by_channel_setting" else profiles[channel]
                    pred = _predict_window(float(bundle["runs"][run_id][f"p_{channel}_seed_by_setting"][k]), slots, center_slot, profile, profile_form, gamma_km_inv)
                    per_run[tag][channel][k] = {"pred": pred, "emp": float(emp.get(k, {}).get(channel, 0.0)), "delta": pred - float(emp.get(k, {}).get(channel, 0.0))}
        window_eval[run_id] = per_run

    report = {
        "kind": "GKSL_PREDICTIVE_V3 init report",
        "train_runs": train_runs,
        "holdout_runs": holdout_runs,
        "gamma_km_inv": gamma_km_inv,
        "profile_form": profile_form,
        "profile_scope": profile_scope,
        "gksl": dict(gksl, gamma_km_inv=gamma_km_inv),
        "fit_report": fit_report,
        "window_eval": window_eval,
    }
    return bundle, report


def build_gksl_param_bundle(*, in_dir: Path, center_slot: int, chunk: int, profile_scope: str, profile_form: str, train_runs: List[str], holdout_runs: List[str], gksl: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    rates_by_run, run_meta = collect_all_run_rates(in_dir, chunk)
    return build_gksl_param_bundle_from_rates(rates_by_run=rates_by_run, run_meta=run_meta, in_dir=in_dir, center_slot=center_slot, profile_scope=profile_scope, profile_form=profile_form, train_runs=train_runs, holdout_runs=holdout_runs, gksl=gksl)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--out_json", default=r".\out\nist_ch\model_params_gksl_predictive_v3.json")
    ap.add_argument("--chunk", type=int, default=2_000_000)
    ap.add_argument("--center_slot", type=int, default=6)
    ap.add_argument("--profile_scope", default="by_channel", choices=["by_channel", "by_channel_setting"])
    ap.add_argument("--profile_form", default="tilt_abs_quad", choices=list(FORMS))
    ap.add_argument("--train_runs", default="")
    ap.add_argument("--holdout_runs", default="")
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

    bundle, report = build_gksl_param_bundle(
        in_dir=Path(args.in_dir),
        center_slot=int(args.center_slot),
        chunk=int(args.chunk),
        profile_scope=str(args.profile_scope),
        profile_form=str(args.profile_form),
        train_runs=_parse_run_list(args.train_runs),
        holdout_runs=_parse_run_list(args.holdout_runs),
        gksl=gksl,
    )
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    report_path = out_json.parent / "gksl_predictive_v3_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[OK] wrote:", str(out_json))
    print("[OK] wrote:", str(report_path))
    print("train_runs:", report["train_runs"])
    print("holdout_runs:", report["holdout_runs"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
