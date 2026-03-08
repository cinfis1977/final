#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PARAMMODEL v5.1 provider (calibrated bridge; direct CH channels; bugfix)

Design:
- Do NOT reconstruct latent Alice/Bob unpaired channels.
- Work directly with the three CH channels the scorecard actually consumes:
    P_pp  : ++
    P_p0  : +0
    P_0p  : 0+
- Each channel is seeded from slot6 empirical rates, per setting.
- Wider windows use an anchored alpha+beta effective-trials law:

    eff(w) = 1 + alpha*(w-1) + beta*(w-1)*(w-3)

  so that:
    w=1 -> eff=1   (slot6 seed preserved exactly)
    w=3 -> eff=1 + 2*alpha
    w=5 -> eff=1 + 4*alpha + 8*beta

This file is intentionally a calibrated bridge, not a model-faithful GKSL provider.
"""
from __future__ import annotations

from typing import Any, Dict


KEYS = ("00", "01", "10", "11")


def _clip01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return float(x)


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _fmt(x: float) -> str:
    s = f"{float(x):.6g}"
    return s


def _effective_trials(w: int, alpha: float, beta: float) -> float:
    if w <= 0:
        return 0.0
    if w == 1:
        return 1.0
    eff = 1.0 + float(alpha) * (w - 1) + float(beta) * (w - 1) * (w - 3)
    if eff < 0.0:
        eff = 0.0
    return eff


def _expand_rate(p1: float, w: int, alpha: float, beta: float) -> float:
    p1 = _clip01(p1)
    if w <= 0 or p1 <= 0.0:
        return 0.0
    if p1 >= 1.0:
        return 1.0
    eff = _effective_trials(w, alpha, beta)
    return _clip01(1.0 - (1.0 - p1) ** eff)


def _rates_for_channel(params: Dict[str, Any], base_key: str, alpha_key: str, beta_key: str, w: int) -> Dict[str, float]:
    p1_map = dict(params.get(base_key, {}) or {})
    alpha_map = dict(params.get(alpha_key, {}) or {})
    beta_map = dict(params.get(beta_key, {}) or {})
    out: Dict[str, float] = {}
    for k in KEYS:
        p1 = _safe_float(p1_map.get(k, 0.0), 0.0)
        alpha = _safe_float(alpha_map.get(k, 1.0), 1.0)
        beta = _safe_float(beta_map.get(k, 0.0), 0.0)
        out[k] = _expand_rate(p1, w, alpha, beta)
    return out


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(run_ctx.get("params", {}) or {})
    slots = list(run_ctx.get("slots", []) or [])
    w = len(slots)

    P_pp = _rates_for_channel(
        params,
        "p_pp_1slot_by_setting",
        "alpha_pp_by_setting",
        "beta_pp_by_setting",
        w,
    )
    P_p0 = _rates_for_channel(
        params,
        "p_p0_1slot_by_setting",
        "alpha_p0_by_setting",
        "beta_p0_by_setting",
        w,
    )
    P_0p = _rates_for_channel(
        params,
        "p_0p_1slot_by_setting",
        "alpha_0p_by_setting",
        "beta_0p_by_setting",
        w,
    )

    alpha_pair = _safe_float(params.get("alpha_pair", 1.0), 1.0)
    beta_pair = _safe_float(params.get("beta_pair", 0.0), 0.0)
    label = (
        "PARAMMODEL v5.1 (calibrated bridge; direct CH channels; "
        f"alpha_pair={_fmt(alpha_pair)}; beta_pair={_fmt(beta_pair)})"
    )

    return {
        "__provider_label__": label,
        "P_pp": P_pp,
        "P_p0": P_p0,
        "P_0p": P_0p,
    }
