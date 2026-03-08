#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GKSL-modulated predictive CH provider — DROP-IN v2

Purpose
-------
A stricter dynamic provider that keeps the target run on holdout for wide windows:

- target run contributes only exact `slot6` seed channels,
- slot growth is driven by a training-only profile,
- the profile is interpreted through `UnifiedGKSL` visibility ratios,
- no target `slots5_7` / `slots4_8` channel calibration is used.

Important honesty label
----------------------
This is closer to a model-faithful dynamic provider than the calibrated bridges,
but it is still a bridge: it maps channel amplitudes from slot6 seeds and uses
GKSL only for dynamic slot modulation. It should be presented as:

    GKSL-modulated predictive holdout bridge

not as a fully first-principles detector model.
"""
from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


KEYS = ("00", "01", "10", "11")
CHANNELS = ("pp", "p0", "0p")


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
    if (root / "mastereq" / "__init__.py").exists():
        entry = str(root)
    else:
        entry = str(root / "integration_artifacts")
    if entry not in sys.path:
        sys.path.insert(0, entry)


@lru_cache(maxsize=512)
def _visibility_ratio_cached(
    dm2: float,
    theta_deg: float,
    gamma_km_inv: float,
    L0_km: float,
    delta_km: float,
    E_GeV: float,
    steps: int,
) -> float:
    _ensure_repo_on_syspath()
    from mastereq.unified_gksl import UnifiedGKSL
    from mastereq.entanglement_sector import make_entanglement_dephasing_fn

    def _vis(L_km: float) -> float:
        ug = UnifiedGKSL(float(dm2), math.radians(float(theta_deg)))
        ug.add_damping(make_entanglement_dephasing_fn(gamma=float(gamma_km_inv)))
        rho = ug.integrate(float(L_km), float(E_GeV), steps=int(steps))
        V = float(2.0 * abs(complex(rho[0, 1])))
        return max(1.0e-15, min(1.0, V))

    v0 = _vis(float(L0_km))
    v1 = _vis(max(0.0, float(L0_km) + float(delta_km)))
    return max(1.0e-15, min(1.0e15, v1 / v0))


def _resolve_gamma(gksl: Dict[str, Any]) -> float:
    gamma = gksl.get("gamma_km_inv", None)
    if gamma is not None:
        return max(0.0, _safe_float(gamma, 0.0))
    _ensure_repo_on_syspath()
    from mastereq.microphysics import gamma_km_inv_from_n_sigma_v, sigma_entanglement_reference_cm2

    E_GeV = _safe_float(gksl.get("E_GeV", 1.0), 1.0)
    visibility_ref = _safe_float(gksl.get("visibility_ref", 0.9), 0.9)
    sigma = sigma_entanglement_reference_cm2(E_GeV, visibility_ref)
    return max(
        0.0,
        float(
            gamma_km_inv_from_n_sigma_v(
                _safe_float(gksl.get("n_cm3", 1.0e18), 1.0e18),
                float(sigma),
                _safe_float(gksl.get("v_cm_s", 3.0e10), 3.0e10),
            )
        ),
    )


def _profile_for(params: Dict[str, Any], channel: str, setting: str) -> Dict[str, float]:
    profiles = dict(params.get("profiles", {}) or {})
    scope = str(params.get("profile_scope", "by_channel") or "by_channel")
    ch = dict(profiles.get(channel, {}) or {})
    if scope == "by_channel_setting":
        cfg = dict(ch.get(setting, {}) or {})
    else:
        cfg = ch
    return {
        "tilt": _safe_float(cfg.get("tilt", 0.0), 0.0),
        "abs_km": max(0.0, _safe_float(cfg.get("abs_km", 0.0), 0.0)),
        "quad_km": max(0.0, _safe_float(cfg.get("quad_km", 0.0), 0.0)),
    }


def _slot_scale(slot: int, center_slot: int, profile: Dict[str, float], gksl: Dict[str, Any]) -> float:
    d = float(int(slot) - int(center_slot))
    delta_km = float(profile.get("abs_km", 0.0)) * abs(d) + float(profile.get("quad_km", 0.0)) * d * d
    ratio = _visibility_ratio_cached(
        _safe_float(gksl.get("dm2", 0.0025), 0.0025),
        _safe_float(gksl.get("theta_deg", 45.0), 45.0),
        _resolve_gamma(gksl),
        _safe_float(gksl.get("L0_km", 1.0), 1.0),
        delta_km,
        _safe_float(gksl.get("E_GeV", 1.0), 1.0),
        int(_safe_float(gksl.get("steps", 320), 320)),
    )
    log_gate = max(-50.0, min(50.0, float(profile.get("tilt", 0.0)) * d))
    gate = math.exp(log_gate)
    return max(0.0, min(1.0e15, gate * ratio))


def _window_union(seed: float, slots: Any, center_slot: int, profile: Dict[str, float], gksl: Dict[str, Any]) -> float:
    seed = _clip01(seed)
    if seed <= 0.0:
        return 0.0
    prod = 1.0
    for slot in list(slots or []):
        p_slot = _clip01(seed * _slot_scale(int(slot), center_slot, profile, gksl))
        prod *= (1.0 - p_slot)
    return _clip01(1.0 - prod)


def _channel_window(params: Dict[str, Any], seed_key: str, channel: str, slots: Any, center_slot: int, gksl: Dict[str, Any]) -> Dict[str, float]:
    seeds = dict(params.get(seed_key, {}) or {})
    out: Dict[str, float] = {}
    for k in KEYS:
        out[k] = _window_union(_safe_float(seeds.get(k, 0.0), 0.0), slots, center_slot, _profile_for(params, channel, k), gksl)
    return out


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(run_ctx.get("params", {}) or {})
    slots = list(run_ctx.get("slots", []) or [])
    center_slot = int(_safe_float(params.get("center_slot", 6), 6))
    gksl = dict(params.get("gksl", {}) or {})

    P_pp = _channel_window(params, "p_pp_seed_by_setting", "pp", slots, center_slot, gksl)
    P_p0 = _channel_window(params, "p_p0_seed_by_setting", "p0", slots, center_slot, gksl)
    P_0p = _channel_window(params, "p_0p_seed_by_setting", "0p", slots, center_slot, gksl)

    gamma_label = _resolve_gamma(gksl)
    label = (
        "GKSL_PREDICTIVE_V2 "
        f"(holdout bridge; center_slot={center_slot}; gamma_km_inv={gamma_label:.6g})"
    )
    return {
        "__provider_label__": label,
        "P_pp": P_pp,
        "P_p0": P_p0,
        "P_0p": P_0p,
    }
