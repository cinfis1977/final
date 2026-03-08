#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH PARAMMODEL v5 provider (two-parameter calibrated bridge)

IMPORTANT
---------
This is a calibrated bridge provider, not a model-faithful GKSL provider.
It consumes the JSON produced by:
    nist_ch_init_parammodel_from_data_v1_DROPIN.py
and returns the probability dict expected by the scorecard:
    compute_probabilities(run_ctx) -> {
        "P_pp": {..},
        "P_p0": {..},
        "P_0p": {..},
    }

Anchored growth law:
    eff(w) = 1 + alpha*(w-1) + beta*(w-1)*(w-3)
    p_w    = 1 - (1-p_1)**eff(w)

So w=1 is preserved exactly.
"""
from __future__ import annotations

import math
from typing import Dict, Any

KEYS = ["00", "01", "10", "11"]
EPS = 1e-15


def _clip01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0 - 1e-15
    return float(x)


def _window_width(slots: Any) -> int:
    xs = sorted(int(s) for s in slots)
    if len(xs) == 1:
        return 1
    return len(xs)


def _eff(width: int, alpha: float, beta: float) -> float:
    x = width - 1
    e = 1.0 + alpha * x + beta * x * (x - 2.0)
    return max(0.0, float(e))


def _grow_union(p1: float, width: int, alpha: float, beta: float) -> float:
    p1 = _clip01(p1)
    if width <= 1:
        return p1
    e = _eff(width, alpha, beta)
    if p1 <= 0.0:
        return 0.0
    if p1 >= 1.0 - 1e-15:
        return 1.0 - 1e-15
    return _clip01(1.0 - math.exp(e * math.log(max(EPS, 1.0 - p1))))


def _get_run_cfg(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    params = run_ctx.get("params") or {}
    run_id = str(run_ctx.get("run_id", ""))

    # Most scorecards pass the selected run block directly as run_ctx["params"].
    # But support the full params JSON too.
    if "runs" in params:
        return dict(params.get("defaults", {}), **params.get("runs", {}).get(run_id, {}))
    return params


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    run_id = str(run_ctx["run_id"])
    width = _window_width(run_ctx["slots"])
    cfg = _get_run_cfg(run_ctx)

    p_pair_1 = dict(cfg.get("p_pair_1slot_by_setting", {}))
    pAu_1 = dict(cfg.get("pA1_u_1slot", {}))
    pBu_1 = dict(cfg.get("pB1_u_1slot", {}))

    alpha_pair_by = dict(cfg.get("alpha_pair_by_setting", {}))
    beta_pair_by = dict(cfg.get("beta_pair_by_setting", {}))
    alpha_Au_by = dict(cfg.get("alpha_Au_by_setting", {}))
    beta_Au_by = dict(cfg.get("beta_Au_by_setting", {}))
    alpha_Bu_by = dict(cfg.get("alpha_Bu_by_setting", {}))
    beta_Bu_by = dict(cfg.get("beta_Bu_by_setting", {}))

    alpha_pair_default = float(cfg.get("alpha_pair", 1.0))
    beta_pair_default = float(cfg.get("beta_pair", 0.0))

    P_pp: Dict[str, float] = {}
    P_p0: Dict[str, float] = {}
    P_0p: Dict[str, float] = {}

    for k in KEYS:
        pp = _grow_union(
            float(p_pair_1.get(k, 0.0)),
            width,
            float(alpha_pair_by.get(k, alpha_pair_default)),
            float(beta_pair_by.get(k, beta_pair_default)),
        )
        pa_u = _grow_union(
            float(pAu_1.get(k, 0.0)),
            width,
            float(alpha_Au_by.get(k, alpha_pair_default)),
            float(beta_Au_by.get(k, 0.0)),
        )
        pb_u = _grow_union(
            float(pBu_1.get(k, 0.0)),
            width,
            float(alpha_Bu_by.get(k, alpha_pair_default)),
            float(beta_Bu_by.get(k, 0.0)),
        )
        P_pp[k] = pp
        P_p0[k] = pa_u
        P_0p[k] = pb_u

    return {
        "__provider_label__": (
            f"PARAMMODEL v5 (calibrated bridge; alpha_pair={alpha_pair_default:.5g}; "
            f"beta_pair={beta_pair_default:.5g})"
        ),
        "P_pp": P_pp,
        "P_p0": P_p0,
        "P_0p": P_0p,
    }
