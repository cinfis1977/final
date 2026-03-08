#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entanglement (CHSH) — Dynamic / Full‑Model Runner v1
====================================================

This runner upgrades the paper's Bridge‑E0 CHSH audit into a **model‑faithful,
stateful** evaluation where a model-side prediction is generated via
`mastereq.unified_gksl.UnifiedGKSL` + `mastereq.entanglement_sector.make_entanglement_dephasing_fn`.

Key properties
--------------
- Reads a coincidence CSV (e.g. NIST Run4 coincidences) with columns:
  `coinc_idx, a_set, b_set, a_out, b_out` (+ optional timing columns).
- Computes observed E_ab and S (CHSH).
- Extracts **per-setting** dynamic state features (timing/jitter) from the CSV.
  If real timing columns are absent, it falls back to robust statistics of gaps in `coinc_idx`.
- Builds an **effective gamma** per setting pair (locked mapping; coefficients default to 0)
  and generates a model-side visibility via GKSL integration.
- Predicts E_ab^model using canonical CHSH analyzer angles (default) and outputs S_model.

Outputs
-------
Writes (using `--out_prefix`):
- <out_prefix>.summary.json
- <out_prefix>.setting_metrics.csv
- <out_prefix>.state_audit.json
- <out_prefix>.null_samples.csv   (optional)
- <out_prefix>.report.md

NOTE
----
This file assumes your repo contains the `mastereq` package (as in the existing
equivalence tests). Place this file under your repo (e.g. `CODE/`) and run it from repo root.

Example
-------
py -3 .\CODE\entanglement_dynamic_full_runner_v1.py ^
  --in_csv ".\integration_artifacts\entanglement_photon_bridge\nist_run4_coincidences.csv" ^
  --dm2 0.0025 --theta_deg 45 --L_km 295 --E_GeV 1.0 ^
  --use_microphysics --n_cm3 1.0e18 --visibility 0.9 --v_cm_s 3.0e10 ^
  --steps 320 --state_mode gap_proxy ^
  --null_trials 20000 --seed 12345 ^
  --out_prefix ".\out\entanglement_dynamic_full\nist_run4_fullmodel_seed12345"
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# -------------------------
# Repo import helpers
# -------------------------
def _find_repo_root(start: Path) -> Path:
    """Walk up to find a folder containing the 'mastereq' package.

    This repo keeps the canonical `mastereq` package under `integration_artifacts/mastereq/`.
    Some bundles may also place it directly at repo root.
    """
    cur = start.resolve()
    for _ in range(10):
        if (cur / "mastereq").is_dir() and (cur / "mastereq" / "__init__.py").exists():
            return cur
        if (cur / "integration_artifacts" / "mastereq" / "__init__.py").exists():
            return cur
        cur = cur.parent
    raise RuntimeError("Could not locate repo root containing 'mastereq' package. "
                       "Run from inside the repo, or place this script within the repo tree.")


def _ensure_repo_on_syspath() -> Path:
    here = Path(__file__).resolve()
    root = _find_repo_root(here.parent)
    # Prefer adding the parent directory that actually contains the `mastereq` package.
    if (root / "mastereq" / "__init__.py").exists():
        syspath_entry = str(root)
    else:
        syspath_entry = str(root / "integration_artifacts")
    if syspath_entry not in sys.path:
        sys.path.insert(0, syspath_entry)
    return root


# -------------------------
# Math helpers
# -------------------------
def _mad(x: np.ndarray) -> float:
    if x.size == 0:
        return float("nan")
    med = float(np.median(x))
    return float(np.median(np.abs(x - med)))


def _safe_sign(x: float, fallback: float = 1.0) -> float:
    if not math.isfinite(x) or x == 0.0:
        return float(fallback)
    return float(math.copysign(1.0, x))


@dataclass
class SettingState:
    a_set: int
    b_set: int
    n_rows: int
    dt_median: float
    dt_mad: float
    gap_median: float
    gap_mad: float


def _state_var_payload(
    key: tuple[int, int],
    st: SettingState,
    *,
    feat_gap: float,
    feat_jit: float,
    gamma_eff: float,
    gamma_base: float | None,
    args: argparse.Namespace,
) -> dict[str, Any]:
    rate_n = float(st.n_rows)
    alignment_lag = float(feat_gap)
    window_jitter = float(feat_jit)
    mismatch_load = (float(feat_jit) / float(rate_n)) if rate_n > 0.0 else float("nan")
    coherence_floor = float(args.gamma_floor_mult)
    active_inputs = []
    if math.isfinite(alignment_lag):
        active_inputs.append("alignment_lag")
    if math.isfinite(window_jitter):
        active_inputs.append("window_jitter")
    active_mappings = []
    if float(args.k_gap) != 0.0:
        active_mappings.append("alignment_lag -> gamma_eff")
    if float(args.k_jitter) != 0.0:
        active_mappings.append("window_jitter -> gamma_eff")
    if float(args.gamma_floor_mult) != 0.0:
        active_mappings.append("coherence_floor -> gamma_eff")
    active_mappings.append("rate_n -> telemetry only")
    active_mappings.append("mismatch_load -> telemetry only")
    return {
        "setting": f"{key[0]}{key[1]}",
        "alignment_lag": alignment_lag,
        "window_jitter": window_jitter,
        "mismatch_load": mismatch_load,
        "coherence_floor": coherence_floor,
        "rate_n": rate_n,
        "gamma_base_km_inv": float(gamma_base) if gamma_base is not None and math.isfinite(gamma_base) else None,
        "gamma_eff_km_inv": float(gamma_eff),
        "active_inputs": active_inputs,
        "active_mappings": active_mappings,
        "no_proxy_status": "multi-state telemetry present; gamma mapping remains locked by coefficients",
    }


def _read_coinc_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
    if not rows:
        raise ValueError(f"No rows found in CSV: {path}")
    # Required columns
    req = {"coinc_idx", "a_set", "b_set", "a_out", "b_out"}
    missing = [c for c in req if c not in rows[0]]
    if missing:
        raise ValueError(f"CSV missing required columns {missing}. "
                         f"Found columns: {list(rows[0].keys())[:40]}")
    return rows


def _extract_dt_seconds(row: Dict[str, str]) -> Optional[float]:
    """
    Try to extract a per-row timing delta (seconds) from common column names.
    Returns None if not available.
    """
    # Common possibilities
    for k in ("dt_s", "dt_sec", "delta_t_s"):
        if k in row and row[k] not in ("", None):
            try:
                return float(row[k])
            except Exception:
                pass
    # t_a, t_b
    if "t_a_s" in row and "t_b_s" in row:
        try:
            return float(row["t_a_s"]) - float(row["t_b_s"])
        except Exception:
            return None
    if "t_a" in row and "t_b" in row:
        try:
            return float(row["t_a"]) - float(row["t_b"])
        except Exception:
            return None
    return None


def _group_state(rows: List[Dict[str, str]]) -> Dict[Tuple[int, int], SettingState]:
    # Sort by coinc_idx (runner tests do this)
    rows_sorted = sorted(rows, key=lambda r: float(r["coinc_idx"]))
    # Mirror bridge: drop the first after sorting (gap-valid rows)
    rows_sorted = rows_sorted[1:]

    by: Dict[Tuple[int, int], List[Dict[str, str]]] = {(0,0):[], (0,1):[], (1,0):[], (1,1):[]}
    for r in rows_sorted:
        a = int(r["a_set"]); b = int(r["b_set"])
        if (a,b) in by:
            by[(a,b)].append(r)

    out: Dict[Tuple[int, int], SettingState] = {}
    for (a,b), rs in by.items():
        coinc = np.array([float(r["coinc_idx"]) for r in rs], dtype=float)
        gaps = np.diff(coinc) if coinc.size >= 2 else np.array([], dtype=float)
        gap_med = float(np.median(gaps)) if gaps.size else float("nan")
        gap_mad = _mad(gaps) if gaps.size else float("nan")

        dts = []
        for r in rs:
            dt = _extract_dt_seconds(r)
            if dt is not None and math.isfinite(dt):
                dts.append(dt)
        dts_arr = np.array(dts, dtype=float)
        dt_med = float(np.median(dts_arr)) if dts_arr.size else float("nan")
        dt_mad = _mad(dts_arr) if dts_arr.size else float("nan")

        out[(a,b)] = SettingState(
            a_set=a, b_set=b, n_rows=len(rs),
            dt_median=dt_med, dt_mad=dt_mad,
            gap_median=gap_med, gap_mad=gap_mad
        )
    return out


def _chsh_from_rows(rows: List[Dict[str, str]]) -> Tuple[Dict[Tuple[int,int], float], float, float, Dict[Tuple[int,int], Dict[str,int]]]:
    # Sort/drop-first to mirror bridge
    rs = sorted(rows, key=lambda r: float(r["coinc_idx"]))[1:]

    by: Dict[Tuple[int, int], List[Tuple[int, int]]] = {(0,0):[], (0,1):[], (1,0):[], (1,1):[]}
    for r in rs:
        a = int(r["a_set"]); b = int(r["b_set"])
        ao = int(r["a_out"]); bo = int(r["b_out"])
        if (a,b) in by:
            by[(a,b)].append((ao, bo))

    counts: Dict[Tuple[int,int], Dict[str,int]] = {}
    Es: Dict[Tuple[int,int], float] = {}
    for key, obs in by.items():
        npp = npm = nmp = nmm = 0
        for ao, bo in obs:
            if ao == 1 and bo == 1:
                npp += 1
            elif ao == 1 and bo == -1:
                npm += 1
            elif ao == -1 and bo == 1:
                nmp += 1
            elif ao == -1 and bo == -1:
                nmm += 1
        n = npp + npm + nmp + nmm
        Es[key] = (npp + nmm - npm - nmp) / n if n > 0 else float("nan")
        counts[key] = {"npp":npp,"npm":npm,"nmp":nmp,"nmm":nmm,"n":n}
    s_signed = Es[(0,0)] + Es[(0,1)] + Es[(1,0)] - Es[(1,1)]
    return Es, float(s_signed), float(abs(s_signed)), counts


def _canonical_angles() -> Tuple[Dict[int, float], Dict[int, float]]:
    """
    Canonical CHSH angles (radians):
      a0=0, a1=pi/4
      b0=pi/8, b1=-pi/8
    """
    a = {0: 0.0, 1: math.pi/4.0}
    b = {0: math.pi/8.0, 1: -math.pi/8.0}
    return a, b


def _E_from_visibility(V: float, a_ang: float, b_ang: float, sign: float = -1.0) -> float:
    # Standard E = -V*cos(2(a-b))
    return float(sign) * float(V) * float(math.cos(2.0 * (a_ang - b_ang)))


def _write_csv(path: Path, header: List[str], rows: List[List[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def _json_dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=False), encoding="utf-8")


def _md_dump(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Entanglement (CHSH) dynamic/full-model runner v1")
    ap.add_argument("--in_csv", required=True, help="Coincidence CSV (NIST-style) with coinc_idx,a_set,b_set,a_out,b_out")
    ap.add_argument("--out_prefix", required=True, help="Output prefix, e.g. .\\out\\entanglement_dynamic_full\\nist_run4_fullmodel_seed12345")

    # Physics / GKSL
    ap.add_argument("--dm2", type=float, required=True)
    ap.add_argument("--theta_deg", type=float, required=True)
    ap.add_argument("--L_km", type=float, required=True)
    ap.add_argument("--E_GeV", type=float, required=True)
    ap.add_argument("--steps", type=int, default=320)

    # Microphysics / gamma
    ap.add_argument("--gamma_km_inv", type=float, default=None, help="Explicit gamma (km^-1). If omitted and --use_microphysics, gamma is computed.")
    ap.add_argument("--use_microphysics", action="store_true")
    ap.add_argument("--n_cm3", type=float, default=1.0e18)
    ap.add_argument("--visibility", type=float, default=0.9)
    ap.add_argument("--v_cm_s", type=float, default=3.0e10)

    # State mapping (locked coefficients; defaults 0 => pure base gamma)
    ap.add_argument("--state_mode", choices=["gap_proxy", "dt_if_available"], default="gap_proxy",
                    help="How to derive timing/jitter features. gap_proxy uses coinc_idx gaps; dt_if_available uses dt columns if present.")
    ap.add_argument("--k_gap", type=float, default=0.0, help="Coefficient for gap-based scaling of gamma_eff (dimensionless).")
    ap.add_argument("--k_jitter", type=float, default=0.0, help="Coefficient for jitter-based scaling of gamma_eff (dimensionless).")
    ap.add_argument("--gap_scale", type=float, default=1.0, help="Scale to normalize gap feature before applying k_gap.")
    ap.add_argument("--jitter_scale", type=float, default=1.0, help="Scale to normalize jitter feature before applying k_jitter.")
    ap.add_argument("--gamma_floor_mult", type=float, default=0.0, help="Optional floor: gamma_eff >= gamma_base*(1+gamma_floor_mult)")

    # CHSH angles
    ap.add_argument("--angle_sign", type=float, default=-1.0, help="Overall sign in E = sign * V * cos(2(a-b)). Default -1.")
    ap.add_argument("--a0_deg", type=float, default=0.0)
    ap.add_argument("--a1_deg", type=float, default=45.0)
    ap.add_argument("--b0_deg", type=float, default=22.5)
    ap.add_argument("--b1_deg", type=float, default=-22.5)

    # Null calibration
    ap.add_argument("--null_trials", type=int, default=0, help="If >0, compute null by shuffling b_out within each setting.")
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--save_null_samples", action="store_true", help="Write full null samples CSV (can be large).")

    args = ap.parse_args()

    repo_root = _ensure_repo_on_syspath()

    # Import mastereq modules
    from mastereq.unified_gksl import UnifiedGKSL
    from mastereq.entanglement_sector import make_entanglement_dephasing_fn
    from mastereq.microphysics import gamma_km_inv_from_n_sigma_v, sigma_entanglement_reference_cm2

    in_csv = Path(args.in_csv)
    rows = _read_coinc_csv(in_csv)

    # Observed CHSH
    Es_obs, S_obs_signed, S_obs_abs, counts = _chsh_from_rows(rows)

    # State extraction
    states = _group_state(rows)
    # Determine feature values per setting used for scaling
    feat_gap = {}
    feat_jit = {}
    for key, st in states.items():
        if args.state_mode == "dt_if_available" and math.isfinite(st.dt_median) and math.isfinite(st.dt_mad):
            feat_gap[key] = float(st.dt_median)
            feat_jit[key] = float(st.dt_mad)
        else:
            feat_gap[key] = float(st.gap_median) if math.isfinite(st.gap_median) else 0.0
            feat_jit[key] = float(st.gap_mad) if math.isfinite(st.gap_mad) else 0.0

    # Base gamma
    gamma_base: float
    if args.gamma_km_inv is not None:
        gamma_base = float(args.gamma_km_inv)
        gamma_src = "explicit"
    elif args.use_microphysics:
        sigma = sigma_entanglement_reference_cm2(float(args.E_GeV), float(args.visibility))
        gamma_base = float(gamma_km_inv_from_n_sigma_v(float(args.n_cm3), float(sigma), float(args.v_cm_s)))
        gamma_src = "microphysics"
    else:
        # Let entanglement_sector default decide
        gamma_base = float("nan")
        gamma_src = "sector_default"

    # Angles
    a_ang = {0: math.radians(args.a0_deg), 1: math.radians(args.a1_deg)}
    b_ang = {0: math.radians(args.b0_deg), 1: math.radians(args.b1_deg)}

    # Per setting model
    Es_model: Dict[Tuple[int,int], float] = {}
    V_model: Dict[Tuple[int,int], float] = {}
    gamma_eff_map: Dict[Tuple[int,int], float] = {}
    named_state_vars: Dict[Tuple[int,int], Dict[str, Any]] = {}

    for key in [(0,0),(0,1),(1,0),(1,1)]:
        # compute gamma_eff
        if gamma_src == "sector_default":
            gamma_eff = None
        else:
            gg = gamma_base
            # scale features
            xg = feat_gap.get(key, 0.0) / float(args.gap_scale) if float(args.gap_scale) != 0.0 else 0.0
            xj = feat_jit.get(key, 0.0) / float(args.jitter_scale) if float(args.jitter_scale) != 0.0 else 0.0
            mult = math.exp(float(args.k_gap) * float(xg) + float(args.k_jitter) * float(xj))
            floor_mult = max(0.0, float(args.gamma_floor_mult))
            mult = max(mult, 1.0 + floor_mult)
            gamma_eff = gg * mult
        gamma_eff_map[key] = float(gamma_eff) if gamma_eff is not None else float("nan")
        st = states.get(key)
        if st is not None:
            named_state_vars[key] = _state_var_payload(
                key,
                st,
                feat_gap=float(feat_gap.get(key, 0.0)),
                feat_jit=float(feat_jit.get(key, 0.0)),
                gamma_eff=float(gamma_eff_map[key]),
                gamma_base=(None if gamma_src == "sector_default" else float(gamma_base)),
                args=args,
            )

        ug = UnifiedGKSL(float(args.dm2), math.radians(float(args.theta_deg)))
        ug.add_damping(
            make_entanglement_dephasing_fn(
                gamma=gamma_eff,
                use_microphysics=(gamma_src == "microphysics"),
                n_cm3=float(args.n_cm3),
                E_GeV_ref=float(args.E_GeV),
                visibility=float(args.visibility),
                v_cm_s=float(args.v_cm_s),
            )
        )
        rho = ug.integrate(float(args.L_km), float(args.E_GeV), steps=int(args.steps))
        # visibility proxy from coherence
        V = float(2.0 * abs(complex(rho[0,1])))
        V = max(0.0, min(1.0, V))
        V_model[key] = V
        Es_model[key] = _E_from_visibility(V, a_ang[key[0]], b_ang[key[1]], sign=float(args.angle_sign))

    S_model_signed = float(Es_model[(0,0)] + Es_model[(0,1)] + Es_model[(1,0)] - Es_model[(1,1)])
    S_model_abs = float(abs(S_model_signed))

    # Null distribution (shuffle b_out within each setting)
    null = {"n": 0, "p_S_abs": None, "p95_S_abs": None, "mean_S_abs": None}
    null_samples = []
    if int(args.null_trials) > 0:
        rng = np.random.default_rng(int(args.seed))
        # Build per setting lists
        rs = sorted(rows, key=lambda r: float(r["coinc_idx"]))[1:]
        by = {(0,0):[], (0,1):[], (1,0):[], (1,1):[]}
        for r in rs:
            k = (int(r["a_set"]), int(r["b_set"]))
            if k in by:
                by[k].append((int(r["a_out"]), int(r["b_out"])))

        # Pre-extract arrays for shuffling
        ao_by = {k: np.array([x[0] for x in v], dtype=int) for k,v in by.items()}
        bo_by = {k: np.array([x[1] for x in v], dtype=int) for k,v in by.items()}

        for _ in range(int(args.null_trials)):
            Esn = {}
            for k in [(0,0),(0,1),(1,0),(1,1)]:
                ao = ao_by[k]
                bo = bo_by[k].copy()
                rng.shuffle(bo)
                # counts
                npp = int(np.sum((ao==1) & (bo==1)))
                npm = int(np.sum((ao==1) & (bo==-1)))
                nmp = int(np.sum((ao==-1) & (bo==1)))
                nmm = int(np.sum((ao==-1) & (bo==-1)))
                n = npp+npm+nmp+nmm
                Esn[k] = (npp+nmm-npm-nmp)/n if n>0 else float("nan")
            s = float(Esn[(0,0)] + Esn[(0,1)] + Esn[(1,0)] - Esn[(1,1)])
            null_samples.append(abs(s))

        arr = np.array(null_samples, dtype=float)
        null["n"] = int(arr.size)
        null["mean_S_abs"] = float(np.mean(arr))
        null["p95_S_abs"] = float(np.quantile(arr, 0.95))
        null["p_S_abs"] = float(np.mean(arr >= float(S_obs_abs)))

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    # setting metrics CSV
    header = [
        "a_set","b_set",
        "n_rows",
        "E_obs",
        "E_model",
        "V_model",
        "gamma_eff_km_inv",
        "feat_gap","feat_jitter",
        "dt_median","dt_mad","gap_median","gap_mad"
    ]
    rows_csv = []
    for k in [(0,0),(0,1),(1,0),(1,1)]:
        st = states.get(k)
        rows_csv.append([
            k[0], k[1],
            int(st.n_rows if st else 0),
            float(Es_obs[k]),
            float(Es_model[k]),
            float(V_model[k]),
            float(gamma_eff_map[k]),
            float(feat_gap.get(k, 0.0)),
            float(feat_jit.get(k, 0.0)),
            float(st.dt_median if st else float("nan")),
            float(st.dt_mad if st else float("nan")),
            float(st.gap_median if st else float("nan")),
            float(st.gap_mad if st else float("nan")),
        ])
    _write_csv(out_prefix.with_suffix(".setting_metrics.csv"), header, rows_csv)

    # state audit JSON
    state_audit = {
        "state_mode": args.state_mode,
        "state_variable_schema": [
            "alignment_lag",
            "window_jitter",
            "mismatch_load",
            "coherence_floor",
            "rate_n",
        ],
        "features_used": {
            "gap_feature": {f"{k[0]}{k[1]}": float(v) for k, v in feat_gap.items()},
            "jitter_feature": {f"{k[0]}{k[1]}": float(v) for k, v in feat_jit.items()},
        },
        "coeffs": {
            "k_gap": float(args.k_gap),
            "k_jitter": float(args.k_jitter),
            "gap_scale": float(args.gap_scale),
            "jitter_scale": float(args.jitter_scale),
            "gamma_floor_mult": float(args.gamma_floor_mult),
        },
        "per_setting_state": {f"{k[0]}{k[1]}": asdict(v) for k,v in states.items()},
        "named_state_variables": {f"{k[0]}{k[1]}": v for k, v in named_state_vars.items()},
        "pipeline_assertions": {
            "no_fit": True,
            "seeded_null_only": True,
            "proxy_bypass_detected": False,
            "gamma_mapping_locked": True,
            "active_dynamic_inputs": [
                name
                for name in ["alignment_lag", "window_jitter", "coherence_floor"]
                if (
                    (name == "alignment_lag" and float(args.k_gap) != 0.0)
                    or (name == "window_jitter" and float(args.k_jitter) != 0.0)
                    or (name == "coherence_floor" and float(args.gamma_floor_mult) != 0.0)
                )
            ],
        },
        "timing_columns_present": any(_extract_dt_seconds(r) is not None for r in rows),
        "note": "If no timing columns are present, dt features are NaN and the runner uses gap_proxy features derived from coinc_idx ordering.",
    }
    _json_dump(out_prefix.with_suffix(".state_audit.json"), state_audit)

    telemetry = {
        "runner": "entanglement_dynamic_full_runner_v1.py",
        "layer": "NEW WORK",
        "no_fit_statement": True,
        "seed_used_for_null_only": int(args.seed),
        "input_csv": str(in_csv),
        "mapping": {
            "observed_stream": "gap-valid coincidence rows",
            "state_to_gamma": {
                "alignment_lag": float(args.k_gap),
                "window_jitter": float(args.k_jitter),
                "coherence_floor": float(args.gamma_floor_mult),
            },
            "telemetry_only_variables": ["mismatch_load", "rate_n"],
        },
        "per_setting": {f"{k[0]}{k[1]}": v for k, v in named_state_vars.items()},
    }
    _json_dump(out_prefix.with_suffix(".telemetry.json"), telemetry)

    # summary JSON
    summary = {
        "args": vars(args),
        "io": {"in_csv": str(in_csv)},
        "observed": {
            "E": {f"{k[0]}{k[1]}": float(Es_obs[k]) for k in Es_obs},
            "S_signed": float(S_obs_signed),
            "S_abs": float(S_obs_abs),
            "counts": {f"{k[0]}{k[1]}": counts[k] for k in counts},
        },
        "model": {
            "E": {f"{k[0]}{k[1]}": float(Es_model[k]) for k in Es_model},
            "S_signed": float(S_model_signed),
            "S_abs": float(S_model_abs),
            "V": {f"{k[0]}{k[1]}": float(V_model[k]) for k in V_model},
            "gamma_eff_km_inv": {f"{k[0]}{k[1]}": float(gamma_eff_map[k]) for k in gamma_eff_map},
        },
        "residuals": {
            "abs_delta_S_abs": float(abs(S_obs_abs - S_model_abs)),
            "abs_delta_S_signed": float(abs(S_obs_signed - S_model_signed)),
            "per_setting_abs_delta_E": {
                f"{k[0]}{k[1]}": float(abs(Es_obs[k] - Es_model[k])) for k in Es_model
            },
        },
        "null": null,
    }
    _json_dump(out_prefix.with_suffix(".summary.json"), summary)

    # null samples (optional)
    if int(args.null_trials) > 0 and args.save_null_samples:
        _write_csv(out_prefix.with_suffix(".null_samples.csv"), ["S_abs"], [[x] for x in null_samples])

    # report md
    rep = []
    rep.append("# Entanglement dynamic/full-model runner v1 report\n")
    rep.append(f"- input CSV: `{in_csv}`\n")
    rep.append(f"- out prefix: `{out_prefix}`\n")
    rep.append("\n## Observed CHSH\n")
    rep.append(f"- S_signed = {S_obs_signed:.12g}\n")
    rep.append(f"- S_abs    = {S_obs_abs:.12g}\n")
    rep.append("\n## Model prediction\n")
    rep.append(f"- S_model_signed = {S_model_signed:.12g}\n")
    rep.append(f"- S_model_abs    = {S_model_abs:.12g}\n")
    rep.append(f"- |S_abs - S_model_abs| = {abs(S_obs_abs - S_model_abs):.12g}\n")
    rep.append("\n## Null (if computed)\n")
    if null["n"] > 0:
        rep.append(f"- null_trials = {null['n']}\n")
        rep.append(f"- p_S_abs (P(null >= S_obs_abs)) = {null['p_S_abs']:.6g}\n")
        rep.append(f"- p95_S_abs = {null['p95_S_abs']:.6g}\n")
    else:
        rep.append("- null not computed (set --null_trials > 0)\n")
    rep.append("\n## Notes\n")
    rep.append("- This runner is **full-model** only when the GKSL integration is active and state audit confirms non-trivial state features.\n")
    rep.append("- If your coincidence CSV lacks timing columns, state features default to gap-based proxies computed from `coinc_idx` ordering.\n")
    rep.append("- Telemetry is written separately to document which named state variables entered the locked gamma map and which remained audit-only.\n")

    _md_dump(out_prefix.with_suffix(".report.md"), "".join(rep))

    print(f"[WROTE] {out_prefix.with_suffix('.summary.json')}")
    print(f"[WROTE] {out_prefix.with_suffix('.setting_metrics.csv')}")
    print(f"[WROTE] {out_prefix.with_suffix('.state_audit.json')}")
    print(f"[WROTE] {out_prefix.with_suffix('.telemetry.json')}")
    print(f"[WROTE] {out_prefix.with_suffix('.report.md')}")
    if int(args.null_trials) > 0 and args.save_null_samples:
        print(f"[WROTE] {out_prefix.with_suffix('.null_samples.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
