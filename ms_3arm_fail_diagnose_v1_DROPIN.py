#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ms_3arm_fail_diagnose_v1_DROPIN.py

Summarize prereg verdict JSONs produced by:
  run_ms_particle_specific_dynamic_3arm_v1_0.py

This repo's verdict JSON schema is:
  {
    "metrics": {...},
    "criteria": {"C1_psuccess": bool, "C2_mad": bool, "C3_thirdarm": bool},
    "final_verdict": "PASS"|"FAIL",
    ...
  }

So this script extracts:
  - final_verdict
  - criteria.C1_psuccess / C2_mad / C3_thirdarm
  - key correlation metrics for diagnosis

Usage:
  python ms_3arm_fail_diagnose_v1_DROPIN.py --run_id <run_id>
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import csv
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_reports(run_id: str) -> List[str]:
    pats = [
        f"out/**/{run_id}/**/prereg_lock_and_final_verdict_goodppm3.json",
        f"out/**/{run_id}/prereg_lock_and_final_verdict_goodppm3.json",
    ]
    seen: set[str] = set()
    hits: List[str] = []
    for pat in pats:
        for p in glob.glob(pat, recursive=True):
            if p not in seen:
                seen.add(p)
                hits.append(p)
    hits.sort(key=lambda p: os.path.getmtime(p))
    return hits


def find_telemetry(run_id: str) -> List[str]:
    pats = [
        f"out/**/{run_id}/**/ms_dynamic_telemetry.json",
        f"out/**/{run_id}/ms_dynamic_telemetry.json",
    ]
    seen: set[str] = set()
    hits: List[str] = []
    for pat in pats:
        for p in glob.glob(pat, recursive=True):
            if p not in seen:
                seen.add(p)
                hits.append(p)
    hits.sort(key=lambda p: p.replace("\\", "/"))
    return hits


def scan_state_stats(scan_state_csv_path: str) -> Dict[str, Any]:
    stats: Dict[str, Any] = {
        "n_rows": 0,
        "drift_state_ppm_min": None,
        "drift_state_ppm_max": None,
        "n_settings": 0,
        "n_scans": 0,
    }
    if not os.path.exists(scan_state_csv_path):
        return stats

    settings: set[str] = set()
    scans: set[str] = set()
    drift_min: float | None = None
    drift_max: float | None = None

    with open(scan_state_csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["n_rows"] += 1
            if "setting" in row and row["setting"] != "":
                settings.add(row["setting"])
            if "scan" in row and row["scan"] != "":
                scans.add(row["scan"])
            v = row.get("drift_state_ppm", "")
            try:
                if v is not None and v != "":
                    fv = float(v)
                    drift_min = fv if drift_min is None else min(drift_min, fv)
                    drift_max = fv if drift_max is None else max(drift_max, fv)
            except ValueError:
                # Leave as None if non-numeric.
                pass

    stats["n_settings"] = len(settings)
    stats["n_scans"] = len(scans)
    stats["drift_state_ppm_min"] = drift_min
    stats["drift_state_ppm_max"] = drift_max
    return stats


def guess_ablation(path: str) -> str:
    lp = path.lower()
    for tag in ("internal_only", "thread_only", "full"):
        if f"/{tag}/" in lp.replace("\\", "/"):
            return tag
    if "internal" in lp:
        return "internal_only"
    if "thread" in lp:
        return "thread_only"
    if "full" in lp:
        return "full"
    return "unknown"


def g(d: Dict[str, Any], *keys: str) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_id", required=True)
    args = ap.parse_args()

    reports = find_reports(args.run_id)
    if not reports:
        print(f"No verdict JSON found for run_id={args.run_id}")
        return 2

    print("=== MS 3-ARM DIAG (verdict summary) ===")

    for p in reports:
        j = load_json(p)
        ablation = guess_ablation(p)
        # Keep output deterministic & compact.
        print(f"\n[{ablation}] {p}")
        print(f"  final_verdict      : {g(j, 'final_verdict')}")
        print(f"  C1_psuccess        : {g(j, 'criteria', 'C1_psuccess')}")
        print(f"  C2_mad             : {g(j, 'criteria', 'C2_mad')}")
        print(f"  C3_thirdarm        : {g(j, 'criteria', 'C3_thirdarm')}")

        print(f"  rank_corr_abs      : {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'rank_corr_abs')}")
        print(f"  median_abs_delta_b2: {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'median_abs_delta_b2')}")
        print(f"  median_abs_delta_b3: {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'median_abs_delta_b3')}")
        print(f"  nz_targets_b2      : {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'nz_targets_b2')}")
        print(f"  nz_targets_b3      : {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'nz_targets_b3')}")
        print(f"  mad_rank_corr      : {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'mad_rank_corr')}")
        print(f"  mad_top_b2         : {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'mad_top_b2')}")
        print(f"  mad_top_b3         : {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'mad_top_b3')}")
        print(f"  mad_top_match      : {g(j, 'metrics', 'A1_B2_vs_A1_B3', 'mad_top_target_match')}")
        print(f"  third_rank_b2_a23  : {g(j, 'metrics', 'third_arm_A2_B3', 'rank_corr_b2_a23')}")
        print(f"  third_rank_b3_a23  : {g(j, 'metrics', 'third_arm_A2_B3', 'rank_corr_b3_a23')}")
        print(f"  third_top_b2       : {g(j, 'metrics', 'third_arm_A2_B3', 'top_b2')}")
        print(f"  third_top_b3       : {g(j, 'metrics', 'third_arm_A2_B3', 'top_b3')}")
        print(f"  third_top_a23      : {g(j, 'metrics', 'third_arm_A2_B3', 'top_a23')}")
        print(f"  third_top_all_match: {g(j, 'metrics', 'third_arm_A2_B3', 'top_all_match')}")

        # Sanity: p_success levels to catch NaNs/empties.
        print(f"  mean_p_success_B2  : {g(j, 'metrics', 'psuccess_levels', 'A1_B2', 'mean_p_success')}")
        print(f"  mean_p_success_B3  : {g(j, 'metrics', 'psuccess_levels', 'A1_B3_holdout', 'mean_p_success')}")
        print(f"  mean_p_success_A23 : {g(j, 'metrics', 'psuccess_levels', 'A2_B3', 'mean_p_success')}")

    telemetry = find_telemetry(args.run_id)
    if telemetry:
        print("\n=== MS 3-ARM DIAG (telemetry summary) ===")
        for tp in telemetry:
            tj = load_json(tp)
            ablation = g(tj, "ablation") or guess_ablation(tp)
            # Try to infer arm from path segment immediately under ablation.
            norm = tp.replace("\\", "/")
            arm = "unknown_arm"
            parts = norm.split("/")
            # .../<run_id>/<ablation>/<arm>/ms_dynamic_telemetry.json
            for i, part in enumerate(parts[:-1]):
                if part == args.run_id and i + 2 < len(parts):
                    arm = parts[i + 2]
                    break

            scan_state_path = str(Path(tp).with_name("scan_state.csv"))
            sstats = scan_state_stats(scan_state_path)
            print(f"\n[{ablation}] {arm}")
            print(f"  internal_dynamics_used : {g(tj, 'dynamics', 'internal_dynamics_used')}")
            print(f"  thread_env_used       : {g(tj, 'dynamics', 'thread_env_used')}")
            print(f"  stateful_steps_total  : {g(tj, 'dynamics', 'stateful_steps_total')}")
            print(f"  n_targets             : {g(tj, 'data', 'n_targets')}")
            print(f"  n_settings            : {g(tj, 'data', 'n_settings')}")
            print(f"  scan_series_required  : {g(tj, 'integrity', 'scan_series_required')}")
            print(f"  scan_state_rows       : {sstats['n_rows']}")
            print(f"  scan_state_scans      : {sstats['n_scans']}")
            print(f"  scan_state_settings   : {sstats['n_settings']}")
            print(f"  drift_state_ppm_range : {sstats['drift_state_ppm_min']} .. {sstats['drift_state_ppm_max']}")
    else:
        print("\n(No ms_dynamic_telemetry.json found under this run_id.)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
