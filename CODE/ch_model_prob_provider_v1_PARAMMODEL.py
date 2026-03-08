#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PARAMMODEL provider v4.1 (bridge; NOT full GKSL)

Fix vs v4
---------
v4 applied alpha_pair to the pair channel even when window size w=1 (slot6),
which breaks the intended seed condition P_pp(w=1) = p_pair_1slot_by_setting.

v4.1 uses an anchored effective-trials rule:
  eff_w = 1 + alpha_pair * (w - 1)

So:
- w=1  -> eff_w = 1  (exactly preserves slot6 seed)
- w>1  -> growth is boosted if alpha_pair>1, reduced if alpha_pair<1

Pair channel (union mode):
  pp = 1 - (1 - p1)^(eff_w)

Singles channel (uncorrelated) keeps alpha=1:
  pA_u(w) = 1 - (1 - pA_u_1)^w
  pB_u(w) = 1 - (1 - pB_u_1)^w

Optional damping:
  pp *= exp(-gamma_window*(w-1))   (default gamma_window=0; positive values can break sign)

Provider API (required)
-----------------------
compute_probabilities(run_ctx) -> dict with:
- P_pp, P_p0, P_0p over keys "00","01","10","11"

Parameters (run_ctx['params'])
------------------------------
Required:
- p_pair_1slot_by_setting (dict)
- pA0_u_1slot, pA1_u_1slot, pB0_u_1slot, pB1_u_1slot
Optional:
- alpha_pair (default 1.0)
- window_union_mode: union|linear (default union)
- gamma_window (default 0.0)
"""
from __future__ import annotations
from typing import Dict, Any
import math

def _clip01(x: float) -> float:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return float(x)

def _p_union(p1: float, eff: float) -> float:
    p1 = _clip01(p1)
    if eff <= 0:
        return 0.0
    return _clip01(1.0 - (1.0 - p1) ** eff)

def _p_linear(p1: float, eff: float) -> float:
    return _clip01(_clip01(p1) * eff)

def _get_pair_1slot(params: Dict[str, Any]) -> Dict[str, float]:
    d = params.get("p_pair_1slot_by_setting", None)
    if isinstance(d, dict):
        return {k: float(d.get(k, 0.0)) for k in ["00","01","10","11"]}
    p = float(params.get("p_pair_1slot", 0.0))
    return {"00": p, "01": p, "10": p, "11": p}

def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(run_ctx.get("params", {}) or {})
    slots = run_ctx.get("slots", [])
    w = int(len(slots))

    mode = str(params.get("window_union_mode", "union")).strip().lower()
    if mode not in ("union", "linear"):
        mode = "union"

    alpha_pair = float(params.get("alpha_pair", 1.0))
    if alpha_pair <= 0:
        alpha_pair = 1.0

    gamma_w = float(params.get("gamma_window", 0.0))
    damp = math.exp(-gamma_w * max(0, w - 1))

    # anchored effective trials for pair channel
    eff_pair = 1.0 + alpha_pair * max(0, w - 1)

    # singles expansion uses plain w (alpha=1)
    pA0_u_1 = float(params.get("pA0_u_1slot", 0.0))
    pA1_u_1 = float(params.get("pA1_u_1slot", 0.0))
    pB0_u_1 = float(params.get("pB0_u_1slot", 0.0))
    pB1_u_1 = float(params.get("pB1_u_1slot", 0.0))

    if mode == "linear":
        pA0_u_w = _p_linear(pA0_u_1, w)
        pA1_u_w = _p_linear(pA1_u_1, w)
        pB0_u_w = _p_linear(pB0_u_1, w)
        pB1_u_w = _p_linear(pB1_u_1, w)
        pair_fn = _p_linear
    else:
        pA0_u_w = _p_union(pA0_u_1, w)
        pA1_u_w = _p_union(pA1_u_1, w)
        pB0_u_w = _p_union(pB0_u_1, w)
        pB1_u_w = _p_union(pB1_u_1, w)
        pair_fn = _p_union

    pair_1 = _get_pair_1slot(params)

    P_pp: Dict[str, float] = {}
    P_p0: Dict[str, float] = {}
    P_0p: Dict[str, float] = {}

    for a_set in (0, 1):
        for b_set in (0, 1):
            k = f"{a_set}{b_set}"
            pp = pair_fn(float(pair_1[k]), eff_pair) * damp
            pp = _clip01(pp)

            pA_u = pA0_u_w if a_set == 0 else pA1_u_w
            pB_u = pB0_u_w if b_set == 0 else pB1_u_w

            P_pp[k] = pp
            P_p0[k] = _clip01((1.0 - pp) * pA_u * (1.0 - pB_u))
            P_0p[k] = _clip01((1.0 - pp) * pB_u * (1.0 - pA_u))

    return {
        "__provider_label__": f"PARAMMODEL v4.1 (bridge; alpha_pair={alpha_pair:g})",
        "P_pp": P_pp,
        "P_p0": P_p0,
        "P_0p": P_0p,
    }
