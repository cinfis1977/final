#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NO-FIT Detector-Hazard provider v1 (CH/Eberhard) — DROP-IN

Purpose
-------
A deterministic, seed-free probability provider for nist_ch_model_scorecard_v1_DROPIN.py.

- NO per-run seeding from CH targets.
- NO calibration from slot6 counts or CH terms.
- Uses ONLY run metadata from HDF5 config (pk, radius, bitoffset) + fixed constants.
- Produces setting-wise probabilities:
    P_pp (++)
    P_p0 (+0)
    P_0p (0+)
  for the requested slot window.

Model (simple mechanistic baseline)
-----------------------------------
We treat each selected TDC slot as an independent Bernoulli opportunity.
Let w = number of selected slots (e.g. slot6 => 1, slots4-8 => 5).

Compute base fractions from HDF5 config:
  fA = radiusA / pkA
  fB = radiusB / pkB

Per-selected-slot hazards (bin-level):
  pA_bin = k_single * fA / n_tdc_bins
  pB_bin = k_single * fB / n_tdc_bins
  pPair_bin_base = k_pair * (fA * fB) / n_tdc_bins

Pair setting modulation (no-fit):
  q(a,b) = 0.5*(1 + V*cos(2*(a-b)))
using fixed angle choices:
  a0=0°, a1=45°, b0=22.5°, b1=-22.5°.

Window aggregation:
  p_window(p_bin, w) = 1 - (1 - p_bin)^w     (union over w slots)

Then for each setting k:
  pp = p_window(pPair_bin_base*q, w)
  pAu = p_window(pA_bin, w)    (depends only on a_set)
  pBu = p_window(pB_bin, w)    (depends only on b_set)

Event-type probabilities:
  P_pp = pp
  P_p0 = (1-pp) * pAu * (1-pBu)
  P_0p = (1-pp) * pBu * (1-pAu)

Notes
-----
- This is a baseline "detector-first" no-fit generator. It will likely be imperfect.
- You may override fixed constants via params_json "defaults" (still no-fit if fixed a priori).
"""
from __future__ import annotations
from typing import Dict, Any
import math

try:
    import h5py  # type: ignore
except Exception:
    h5py = None  # type: ignore


def _clip01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def _p_window(p_bin: float, w: int) -> float:
    p_bin = _clip01(p_bin)
    if w <= 0:
        return 0.0
    return _clip01(1.0 - (1.0 - p_bin) ** int(w))


def _angles_deg(a_set: int, b_set: int, params: Dict[str, Any]) -> tuple[float, float]:
    a0 = float(params.get("a0_deg", 0.0))
    a1 = float(params.get("a1_deg", 45.0))
    b0 = float(params.get("b0_deg", 22.5))
    b1 = float(params.get("b1_deg", -22.5))
    a = a0 if int(a_set) == 0 else a1
    b = b0 if int(b_set) == 0 else b1
    return a, b


def _q_weight(a_deg: float, b_deg: float, V: float) -> float:
    d = math.radians(a_deg - b_deg)
    return _clip01(0.5 * (1.0 + _clip01(V) * math.cos(2.0 * d)))


def _read_config_scalars(h5_path: str) -> Dict[str, float]:
    # Safe defaults (used if config group is missing)
    out = {
        "pk_a": 90.0,
        "pk_b": 125.0,
        "radius_a": 4.0,
        "radius_b": 5.0,
        "bitoffset_a": 0.0,
        "bitoffset_b": 0.0,
    }
    if h5py is None:
        return out
    try:
        with h5py.File(h5_path, "r") as f:
            def get_scalar(path: str) -> float | None:
                try:
                    if path in f:
                        return float(f[path][()])
                except Exception:
                    return None
                return None

            pk_a = get_scalar("config/alice/pk")
            pk_b = get_scalar("config/bob/pk")
            r_a = get_scalar("config/alice/radius")
            r_b = get_scalar("config/bob/radius")
            bo_a = get_scalar("config/alice/bitoffset")
            bo_b = get_scalar("config/bob/bitoffset")

            if pk_a is not None: out["pk_a"] = pk_a
            if pk_b is not None: out["pk_b"] = pk_b
            if r_a is not None: out["radius_a"] = r_a
            if r_b is not None: out["radius_b"] = r_b
            if bo_a is not None: out["bitoffset_a"] = bo_a
            if bo_b is not None: out["bitoffset_b"] = bo_b
    except Exception:
        pass
    return out


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(run_ctx.get("params", {}) or {})

    slots = run_ctx.get("slots", [])
    w = int(len(slots))

    V = float(params.get("visibility", 0.9))
    k_single = float(params.get("k_single", 0.002))
    k_pair = float(params.get("k_pair", 0.02))
    n_bins = int(params.get("n_tdc_bins", 16))
    if n_bins <= 0:
        n_bins = 16

    h5_path = str(run_ctx.get("h5_path", "") or "")
    cfg = _read_config_scalars(h5_path) if h5_path else _read_config_scalars("")

    pk_a = float(cfg["pk_a"]); pk_b = float(cfg["pk_b"])
    r_a = float(cfg["radius_a"]); r_b = float(cfg["radius_b"])

    fA = _clip01(r_a / pk_a) if pk_a > 0 else 0.0
    fB = _clip01(r_b / pk_b) if pk_b > 0 else 0.0

    pA_bin = _clip01(k_single * fA / float(n_bins))
    pB_bin = _clip01(k_single * fB / float(n_bins))
    pPair_bin_base = _clip01(k_pair * (fA * fB) / float(n_bins))

    pAu_w = _p_window(pA_bin, w)
    pBu_w = _p_window(pB_bin, w)

    P_pp: Dict[str, float] = {}
    P_p0: Dict[str, float] = {}
    P_0p: Dict[str, float] = {}

    for a_set in (0, 1):
        for b_set in (0, 1):
            k = f"{a_set}{b_set}"
            a_deg, b_deg = _angles_deg(a_set, b_set, params)
            q = _q_weight(a_deg, b_deg, V)

            pp = _p_window(pPair_bin_base * q, w)
            pAu = pAu_w
            pBu = pBu_w

            P_pp[k] = pp
            P_p0[k] = _clip01((1.0 - pp) * pAu * (1.0 - pBu))
            P_0p[k] = _clip01((1.0 - pp) * pBu * (1.0 - pAu))

    return {
        "__provider_label__": "NOFIT_DETECTORHAZARD v1 (config-only; fixed k_single/k_pair; no seeding)",
        "P_pp": P_pp,
        "P_p0": P_p0,
        "P_0p": P_0p,
        "__debug__": {
            "w": w,
            "pk_a": pk_a, "pk_b": pk_b,
            "radius_a": r_a, "radius_b": r_b,
            "fA": fA, "fB": fB,
            "pA_bin": pA_bin, "pB_bin": pB_bin, "pPair_bin_base": pPair_bin_base,
            "visibility": V, "k_single": k_single, "k_pair": k_pair, "n_tdc_bins": n_bins,
        },
    }
