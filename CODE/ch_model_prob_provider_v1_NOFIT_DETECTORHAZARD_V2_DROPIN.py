#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NO-FIT Detector-Hazard provider v2 (CH/Eberhard) — DROP-IN

v2 fixes v1's main pathology:
- v1 treated uncorrelated singles as independent of pair emission, making +0/0+ too large → J_model negative.
- v2 couples +0/0+ to pair emission with loss.

Per slot:
- pair emitted with prob p_emit_1slot
- Alice detects with efficiency etaA (from HDF5 config radius/pk times fixed k_eta)
- Bob detects with efficiency etaB
- coincidence is modulated by s_ab = 0.5*(1 + V*cos(2*(a-b))) with fixed angles.

Window of w selected slots:
  p_emit_w = 1 - (1 - p_emit_1slot)^w

Per setting:
  P_pp = p_emit_w * etaA * etaB * s_ab
  P_p0 = p_emit_w * etaA * (1-etaB) * sA(a_set)
  P_0p = p_emit_w * etaB * (1-etaA) * sB(b_set)

NO-FIT RULE:
- Does NOT read CH targets or slot6 counts.
- Reads only HDF5 config scalars (pk/radius).
- Uses fixed knobs from params_json defaults.
"""
from __future__ import annotations
from typing import Dict, Any
import math

try:
    import h5py  # type: ignore
except Exception:
    h5py = None  # type: ignore


def _clip01(x: float) -> float:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return float(x)


def _p_union(p: float, w: int) -> float:
    p = _clip01(p)
    if w <= 0:
        return 0.0
    return _clip01(1.0 - (1.0 - p) ** int(w))


def _angles_deg(a_set: int, b_set: int, params: Dict[str, Any]) -> tuple[float, float]:
    a0 = float(params.get("a0_deg", 0.0))
    a1 = float(params.get("a1_deg", 45.0))
    b0 = float(params.get("b0_deg", 22.5))
    b1 = float(params.get("b1_deg", -22.5))
    a = a0 if int(a_set) == 0 else a1
    b = b0 if int(b_set) == 0 else b1
    return a, b


def _s_ab(a_deg: float, b_deg: float, V: float) -> float:
    d = math.radians(a_deg - b_deg)
    return _clip01(0.5 * (1.0 + _clip01(V) * math.cos(2.0 * d)))


def _read_config_scalars(h5_path: str) -> Dict[str, float]:
    out = {"pk_a": 90.0, "pk_b": 125.0, "radius_a": 4.0, "radius_b": 5.0}
    if h5py is None:
        return out
    try:
        with h5py.File(h5_path, "r") as f:
            def get_scalar(path: str):
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
            if pk_a is not None: out["pk_a"] = pk_a
            if pk_b is not None: out["pk_b"] = pk_b
            if r_a is not None: out["radius_a"] = r_a
            if r_b is not None: out["radius_b"] = r_b
    except Exception:
        pass
    return out


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(run_ctx.get("params", {}) or {})
    slots = run_ctx.get("slots", [])
    w = int(len(slots))

    V = float(params.get("visibility", 0.9))
    p_emit_1slot = float(params.get("p_emit_1slot", 0.02))
    k_eta = float(params.get("k_eta", 10.0))
    sA0 = float(params.get("sA0", 0.5)); sA1 = float(params.get("sA1", 0.5))
    sB0 = float(params.get("sB0", 0.5)); sB1 = float(params.get("sB1", 0.5))

    h5_path = str(run_ctx.get("h5_path", "") or "")
    cfg = _read_config_scalars(h5_path) if h5_path else _read_config_scalars("")

    pk_a = float(cfg["pk_a"]); pk_b = float(cfg["pk_b"])
    r_a = float(cfg["radius_a"]); r_b = float(cfg["radius_b"])

    fA = _clip01(r_a / pk_a) if pk_a > 0 else 0.0
    fB = _clip01(r_b / pk_b) if pk_b > 0 else 0.0

    etaA = _clip01(k_eta * fA)
    etaB = _clip01(k_eta * fB)

    p_emit_w = _p_union(p_emit_1slot, w)

    P_pp: Dict[str, float] = {}
    P_p0: Dict[str, float] = {}
    P_0p: Dict[str, float] = {}

    for a_set in (0, 1):
        for b_set in (0, 1):
            k = f"{a_set}{b_set}"
            a_deg, b_deg = _angles_deg(a_set, b_set, params)
            sab = _s_ab(a_deg, b_deg, V)

            sA = sA0 if a_set == 0 else sA1
            sB = sB0 if b_set == 0 else sB1

            pp = _clip01(p_emit_w * etaA * etaB * sab)
            p_p0 = _clip01(p_emit_w * etaA * (1.0 - etaB) * sA)
            p_0p = _clip01(p_emit_w * etaB * (1.0 - etaA) * sB)

            P_pp[k] = pp
            P_p0[k] = p_p0
            P_0p[k] = p_0p

    return {
        "__provider_label__": "NOFIT_DETECTORHAZARD v2 (pair-emission+loss; config-only; fixed knobs)",
        "P_pp": P_pp,
        "P_p0": P_p0,
        "P_0p": P_0p,
        "__debug__": {
            "w": w,
            "pk_a": pk_a, "pk_b": pk_b,
            "radius_a": r_a, "radius_b": r_b,
            "fA": fA, "fB": fB,
            "etaA": etaA, "etaB": etaB,
            "p_emit_1slot": p_emit_1slot, "p_emit_w": p_emit_w,
            "visibility": V, "k_eta": k_eta
        },
    }
