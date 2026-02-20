#!/usr/bin/env python3
"""
t2k_penalty_cli.py (ascii-safe)

Reads 1D Δχ² profiles extracted from the T2K Frequentist/Bayesian public ROOT releases
and returns an additive penalty at a requested parameter point.

Why ASCII-only?
- On Windows, when stdout is piped (e.g., called via subprocess with capture_output),
  Python may use a legacy codepage (cp1252) that cannot encode Greek letters or superscripts.
  Using ASCII-only output prevents UnicodeEncodeError.

Expected input JSON schema (from t2k_release_extract):
{
  "profiles": {
     "<profile_key>": {
        "centers": [...],
        "dchi2": [...],   # preferred; already min-subtracted
        "chi2":  [...],   # optional
        ...
     }, ...
  }
}
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Any, Tuple, List

def _load_profiles(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    # support either {"profiles": {...}} or direct dict
    if isinstance(obj, dict) and "profiles" in obj and isinstance(obj["profiles"], dict):
        return obj["profiles"]
    if isinstance(obj, dict):
        return obj
    raise ValueError("profiles json must be a dict (or contain a 'profiles' dict).")

def _interp1d(x: List[float], y: List[float], x0: float) -> float:
    """Linear interpolation with flat extrapolation at edges."""
    if not x or not y or len(x) != len(y):
        raise ValueError("invalid x/y arrays for interpolation")
    if x0 <= x[0]:
        return float(y[0])
    if x0 >= x[-1]:
        return float(y[-1])
    # find right index
    lo, hi = 0, len(x)-1
    while hi - lo > 1:
        mid = (lo + hi)//2
        if x[mid] <= x0:
            lo = mid
        else:
            hi = mid
    x1, x2 = x[lo], x[hi]
    y1, y2 = y[lo], y[hi]
    if x2 == x1:
        return float(y1)
    t = (x0 - x1) / (x2 - x1)
    return float(y1 + t*(y2 - y1))

def _profile_arrays(prof: Dict[str, Any]) -> Tuple[List[float], List[float], float]:
    """
    Return (x_centers, dchi2, dchi2_min_used).
    Prefer 'dchi2'. Else compute from 'chi2' by subtracting min.
    """
    x = prof.get("centers") or prof.get("x") or prof.get("bins")
    if x is None:
        raise ValueError("profile missing 'centers' (or alias 'x')")
    if "dchi2" in prof:
        y = prof["dchi2"]
        y_min = float(min(y)) if y else 0.0
        return list(map(float, x)), list(map(float, y)), y_min
    if "chi2" in prof:
        chi2 = list(map(float, prof["chi2"]))
        chi2_min = float(min(chi2)) if chi2 else 0.0
        y = [c - chi2_min for c in chi2]
        return list(map(float, x)), y, 0.0
    raise ValueError("profile missing both 'dchi2' and 'chi2'")

def penalty_for_param(profiles: Dict[str, Any], key: str, x0: float) -> Tuple[float, float, float]:
    prof = profiles.get(key)
    if prof is None:
        raise KeyError(f"profile key not found: {key}")
    x, y, y_min = _profile_arrays(prof)
    dchi2_x = _interp1d(x, y, float(x0))
    # If y isn't exactly min-shifted to 0, subtract y_min so penalty is relative
    pen = dchi2_x - y_min
    return float(pen), float(dchi2_x), float(y_min)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", required=True, help="Path to extracted profiles JSON (e.g., t2k_frequentist_profiles.json)")
    ap.add_argument("--hierarchy", choices=["NH", "IH"], default="NH")
    ap.add_argument("--rc", choices=["wRC", "woRC"], default="wRC")

    # Parameters (names are ASCII and match the wrapper script)
    ap.add_argument("--s2th23", type=float, default=None, help="sin^2(theta23)")
    ap.add_argument("--dm2", type=float, default=None, help="Delta m^2_32 [eV^2]")
    ap.add_argument("--dcp", type=float, default=None, help="delta_CP [rad]")

    # Optional extras if you later want them
    ap.add_argument("--s2th13", type=float, default=None)
    ap.add_argument("--s2th12", type=float, default=None)

    args = ap.parse_args()
    prof_path = Path(args.profiles)

    profiles = _load_profiles(prof_path)

    # Key templates used by the extractor drop-in
    def key_for(which: str) -> str:
        # matches keys like: h1D_th23chi2_wRC_NH
        return f"h1D_{which}chi2_{args.rc}_{args.hierarchy}"

    total = 0.0
    print(f"profiles: {prof_path}")
    print(f"hierarchy: {args.hierarchy}   rc: {args.rc}")

    def add(label: str, val: float | None, which: str):
        nonlocal total
        if val is None:
            return
        k = key_for(which)
        pen, chi2_x, chi2_min = penalty_for_param(profiles, k, val)
        total += pen
        print(f"{label:8s} = {val: .6g}  ->  dchi2_pen = {pen: .6g}   (dchi2={chi2_x: .6g}, dchi2_min={chi2_min: .6g})   key={k}")

    add("s2th23", args.s2th23, "th23")
    add("dm2",    args.dm2,    "dm2")
    add("dcp",    args.dcp,    "dCP")

    # Keep one parseable line for wrappers:
    print(f"TOTAL_dchi2_penalty = {total:.6g}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
