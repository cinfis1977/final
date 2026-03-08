#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH predictive slot-kernel init — DROP-IN v1

What this file is
-----------------
A new, non-destructive predictive bridge initializer.
It does NOT modify any existing code or reuse target wide-window CH outputs.

Core idea
---------
1) Read each run's original HDF5 through the `h5_path` already recorded in
   `out/nist_ch/run*_slot6.summary.json`.
2) Recompute exact single-slot CH channels for slots 1..16:
   - `pp`  = ++
   - `p0`  = +0
   - `0p`  = 0+
3) Learn a GLOBAL slot-dynamics profile from training runs only.
4) Store per-run `slot6` seeds plus the global profile in a params JSON.
5) Use the new provider:
   `ch_model_prob_provider_v1_PREDICTIVE_SLOTKERNEL_V1_DROPIN.py`
   to predict wider windows without reading target-run window outputs.

Model form
----------
For each channel, the per-slot probability is modeled as:

    p(slot) = p_seed(slot6) * exp(tilt * d - quad * d^2)

where `d = slot - center_slot`.

This is intentionally stricter than v5.1:
- target run contributes only its `slot6` seed,
- the window-growth profile comes only from training runs,
- no direct target `slots5_7` or `slots4_8` calibration is used.

Important honesty note
----------------------
This is a predictive dynamic bridge / runner initializer.
It is MORE honest than a calibrated closure, but it is still not a full
microphysical GKSL derivation of detection channels.
It is meant as the next disciplined step before a fully independent provider.

Example
-------
py -3 .\\CODE\\nist_ch_predictive_slotkernel_init_v1_DROPIN.py ^
    --in_dir ".\\out\\nist_ch" ^
    --holdout_runs "02_54" ^
    --out_json ".\\out\\nist_ch\\model_params_predictive_slotkernel_v1.json"
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

try:
    import h5py  # type: ignore
except Exception as e:
    raise SystemExit("h5py is required. Install: pip install h5py") from e


KEYS = ("00", "01", "10", "11")
CHANNELS = ("pp", "p0", "0p")


def _dataset(h5: Any, path: str) -> Any:
    return h5[path] if path in h5 else h5["/" + path]


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
    out = []
    for part in spec.split(","):
        tok = part.strip()
        if tok:
            out.append(tok)
    return sorted(set(out))


def _discover_runs(in_dir: Path) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for sp in sorted(in_dir.glob("run*_slot6.summary.json")):
        m = re.search(r"run(\d{2}_\d{2})_slot6\.summary\.json$", sp.name)
        if not m:
            continue
        run_id = m.group(1)
        summary = _read_json(sp)
        if _is_training_stub(summary):
            continue
        h5_path = Path(str(summary.get("h5_path", "")))
        if not h5_path.is_absolute():
            h5_path = (Path.cwd() / h5_path).resolve()
        out[run_id] = {
            "run_id": run_id,
            "summary_path": sp,
            "h5_path": h5_path,
        }
    if not out:
        raise SystemExit(f"No real run*_slot6.summary.json found in {in_dir}")
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
            out[slot][channel] = {
                k: _clip01(_safe_rate(int(payload[channel][k]), int(payload["N"][k])))
                for k in KEYS
            }
    return out


def _fit_exp_tilt_quad(samples: List[Tuple[int, float]]) -> Dict[str, float]:
    good = []
    for d, ratio in samples:
        if d == 0:
            continue
        r = float(ratio)
        if not math.isfinite(r) or r <= 0.0:
            continue
        good.append((int(d), min(max(r, 1.0e-12), 1.0e12)))
    if len(good) < 2:
        return {"tilt": 0.0, "quad": 0.0}

    X = []
    y = []
    for d, r in good:
        X.append([float(d), -float(d * d)])
        y.append(math.log(r))
    Xa = np.asarray(X, dtype=float)
    ya = np.asarray(y, dtype=float)
    try:
        coef, *_ = np.linalg.lstsq(Xa, ya, rcond=None)
        tilt = float(coef[0])
        quad = max(0.0, float(-coef[1]))
    except Exception:
        tilt = 0.0
        quad = 0.0
    if not math.isfinite(tilt):
        tilt = 0.0
    if not math.isfinite(quad):
        quad = 0.0
    return {"tilt": tilt, "quad": quad}


def _profile_samples(
    rates_by_run: Dict[str, Dict[int, Dict[str, Dict[str, float]]]],
    train_runs: Iterable[str],
    channel: str,
    center_slot: int,
    profile_scope: str,
    setting: str | None = None,
) -> List[Tuple[int, float]]:
    samples: List[Tuple[int, float]] = []
    for run_id in train_runs:
        slot_map = rates_by_run[run_id]
        if profile_scope == "by_channel_setting":
            if setting is None:
                continue
            seed = float(slot_map[center_slot][channel][setting])
            if seed <= 0.0:
                continue
            for slot in sorted(slot_map.keys()):
                rate = float(slot_map[slot][channel][setting])
                samples.append((slot - center_slot, rate / seed if seed > 0.0 else 0.0))
        else:
            vals = [float(slot_map[center_slot][channel][k]) for k in KEYS if float(slot_map[center_slot][channel][k]) > 0.0]
            if not vals:
                continue
            for k in KEYS:
                seed = float(slot_map[center_slot][channel][k])
                if seed <= 0.0:
                    continue
                for slot in sorted(slot_map.keys()):
                    rate = float(slot_map[slot][channel][k])
                    samples.append((slot - center_slot, rate / seed if seed > 0.0 else 0.0))
    return samples


def _fit_profiles(
    rates_by_run: Dict[str, Dict[int, Dict[str, Dict[str, float]]]],
    train_runs: List[str],
    center_slot: int,
    profile_scope: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    profiles: Dict[str, Any] = {}
    report: Dict[str, Any] = {}
    for channel in CHANNELS:
        if profile_scope == "by_channel_setting":
            profiles[channel] = {}
            report[channel] = {}
            for k in KEYS:
                samples = _profile_samples(rates_by_run, train_runs, channel, center_slot, profile_scope, setting=k)
                prof = _fit_exp_tilt_quad(samples)
                profiles[channel][k] = prof
                report[channel][k] = {
                    "n_samples": len(samples),
                    "fit": prof,
                }
        else:
            samples = _profile_samples(rates_by_run, train_runs, channel, center_slot, profile_scope)
            prof = _fit_exp_tilt_quad(samples)
            profiles[channel] = prof
            report[channel] = {
                "n_samples": len(samples),
                "fit": prof,
            }
    return profiles, report


def _predict_window(seed: float, slots: Iterable[int], center_slot: int, tilt: float, quad: float) -> float:
    prod = 1.0
    seed = _clip01(seed)
    for slot in slots:
        d = float(int(slot) - int(center_slot))
        scale = math.exp(max(-50.0, min(50.0, float(tilt) * d - float(quad) * d * d)))
        p = _clip01(seed * scale)
        prod *= (1.0 - p)
    return _clip01(1.0 - prod)


def _empirical_window_counts(in_dir: Path, run_id: str, tag: str) -> Dict[str, Any]:
    path = in_dir / f"run{run_id}_{tag}.counts.csv"
    if not path.exists():
        return {}
    import csv
    out = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            k = f"{int(row['a_set'])}{int(row['b_set'])}"
            n = int(float(row.get("trials_valid", row.get("trials", "0"))))
            a = int(float(row.get("alice_detect", "0")))
            b = int(float(row.get("bob_detect", "0")))
            ab = int(float(row.get("both_detect", "0")))
            out[k] = {
                "N": n,
                "pp": _clip01(_safe_rate(ab, n)),
                "p0": _clip01(_safe_rate(max(0, a - ab), n)),
                "0p": _clip01(_safe_rate(max(0, b - ab), n)),
            }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--out_json", default=r".\out\nist_ch\model_params_predictive_slotkernel_v1.json")
    ap.add_argument("--chunk", type=int, default=2_000_000)
    ap.add_argument("--center_slot", type=int, default=6)
    ap.add_argument(
        "--profile_scope",
        default="by_channel",
        choices=["by_channel", "by_channel_setting"],
        help="Fit one global profile per channel, or a separate profile per channel+setting.",
    )
    ap.add_argument("--train_runs", default="", help="Comma-separated explicit training runs. Default: auto from all real runs minus holdout.")
    ap.add_argument("--holdout_runs", default="", help="Comma-separated holdout runs to exclude from profile fitting.")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    runs = _discover_runs(in_dir)
    all_runs = sorted(runs.keys())
    holdout_runs = _parse_run_list(args.holdout_runs)
    train_runs = _parse_run_list(args.train_runs)
    if not train_runs:
        train_runs = [r for r in all_runs if r not in holdout_runs]
    train_runs = [r for r in train_runs if r in runs]
    holdout_runs = [r for r in holdout_runs if r in runs]
    if not train_runs:
        raise SystemExit("No training runs left after applying holdout/train filters.")

    rates_by_run: Dict[str, Dict[int, Dict[str, Dict[str, float]]]] = {}
    seed_report: Dict[str, Any] = {}
    for run_id in all_runs:
        h5_path = Path(runs[run_id]["h5_path"])
        if not h5_path.exists():
            raise SystemExit(f"HDF5 not found for run {run_id}: {h5_path}")
        slot_counts = _collect_single_slot_channels(h5_path, chunk=int(args.chunk))
        rates = _rates_from_counts(slot_counts)
        rates_by_run[run_id] = rates
        seed_report[run_id] = {
            "h5_path": str(h5_path),
            "slot6": {
                channel: {k: float(rates[int(args.center_slot)][channel][k]) for k in KEYS}
                for channel in CHANNELS
            },
        }

    profiles, fit_report = _fit_profiles(
        rates_by_run=rates_by_run,
        train_runs=train_runs,
        center_slot=int(args.center_slot),
        profile_scope=str(args.profile_scope),
    )

    top: Dict[str, Any] = {
        "defaults": {
            "bridge_version": "PREDICTIVE SLOTKERNEL v1 (strict holdout dynamic bridge)",
            "note": (
                "Uses exact slot6 seeds from each target run plus a slot-dynamics profile fitted "
                "only on training runs. Does not use target wide-window CH channels."
            ),
            "center_slot": int(args.center_slot),
            "slot_profile_model": "exp_tilt_quad",
            "profile_scope": str(args.profile_scope),
            "train_runs": train_runs,
            "holdout_runs": holdout_runs,
            "profiles": profiles,
        },
        "runs": {},
    }

    eval_report: Dict[str, Any] = {}
    for run_id in all_runs:
        rates = rates_by_run[run_id]
        top["runs"][run_id] = {
            "seed_source": "exact single-slot counts from original HDF5 at center_slot",
            "p_pp_seed_by_setting": {k: float(rates[int(args.center_slot)]["pp"][k]) for k in KEYS},
            "p_p0_seed_by_setting": {k: float(rates[int(args.center_slot)]["p0"][k]) for k in KEYS},
            "p_0p_seed_by_setting": {k: float(rates[int(args.center_slot)]["0p"][k]) for k in KEYS},
        }

        per_run_eval: Dict[str, Any] = {}
        for tag, slots in (("slot6", [6]), ("slots5_7", [5, 6, 7]), ("slots4_8", [4, 5, 6, 7, 8])):
            emp = _empirical_window_counts(in_dir, run_id, tag)
            if not emp:
                continue
            ch_eval: Dict[str, Any] = {}
            for channel in CHANNELS:
                ch_eval[channel] = {}
                for k in KEYS:
                    if str(args.profile_scope) == "by_channel_setting":
                        cfg = dict(profiles[channel].get(k, {}) or {})
                    else:
                        cfg = dict(profiles.get(channel, {}) or {})
                    pred = _predict_window(
                        seed=float(top["runs"][run_id][f"p_{channel}_seed_by_setting"][k]),
                        slots=slots,
                        center_slot=int(args.center_slot),
                        tilt=float(cfg.get("tilt", 0.0)),
                        quad=float(cfg.get("quad", 0.0)),
                    )
                    ch_eval[channel][k] = {
                        "pred": pred,
                        "emp": float(emp.get(k, {}).get(channel, 0.0)),
                        "delta": pred - float(emp.get(k, {}).get(channel, 0.0)),
                    }
            per_run_eval[tag] = ch_eval
        eval_report[run_id] = per_run_eval

    out_json.write_text(json.dumps(top, indent=2), encoding="utf-8")
    report_path = out_json.parent / "predictive_slotkernel_v1_report.json"
    report = {
        "kind": "predictive_slotkernel_v1_report",
        "train_runs": train_runs,
        "holdout_runs": holdout_runs,
        "fit_report": fit_report,
        "seed_report": seed_report,
        "window_eval": eval_report,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[OK] wrote:", str(out_json))
    print("[OK] wrote:", str(report_path))
    print("train_runs:", train_runs)
    print("holdout_runs:", holdout_runs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
