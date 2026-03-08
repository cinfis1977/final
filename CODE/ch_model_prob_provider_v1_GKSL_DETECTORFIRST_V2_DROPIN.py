#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GKSL detector-first CH provider — DROP-IN v2

Uses per-run base rates predicted from non-CH metadata and global GKSL-modulated
profile parameters. No target empirical CH seeds are used.
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
    entry = str(root) if (root / "mastereq" / "__init__.py").exists() else str(root / "integration_artifacts")
    if entry not in sys.path:
        sys.path.insert(0, entry)


@lru_cache(maxsize=4096)
def _visibility_ratio_cached(dm2: float, theta_deg: float, gamma_km_inv: float, L0_km: float, delta_km: float, E_GeV: float, steps: int) -> float:
    _ensure_repo_on_syspath()
    from mastereq.unified_gksl import UnifiedGKSL
    from mastereq.entanglement_sector import make_entanglement_dephasing_fn

    def _vis(L_km: float) -> float:
        ug = UnifiedGKSL(float(dm2), math.radians(float(theta_deg)))
        ug.add_damping(make_entanglement_dephasing_fn(gamma=float(gamma_km_inv)))
        rho = ug.integrate(float(L_km), float(E_GeV), steps=int(steps))
        return max(1.0e-15, min(1.0, float(2.0 * abs(complex(rho[0, 1])))))

    v0 = _vis(float(L0_km))
    v1 = _vis(max(0.0, float(L0_km) + float(delta_km)))
    return max(1.0e-15, min(1.0e15, v1 / v0))


def _delta_km(d: float, form: str, cfg: Dict[str, float]) -> float:
    abs_km = max(0.0, _safe_float(cfg.get("abs_km", 0.0), 0.0))
    quad_km = max(0.0, _safe_float(cfg.get("quad_km", 0.0), 0.0))
    if form == "tilt_abs":
        return abs_km * abs(d)
    if form == "tilt_quad":
        return quad_km * d * d
    if form == "abs_quad":
        return abs_km * abs(d) + quad_km * d * d
    return abs_km * abs(d) + quad_km * d * d


def _gate(d: float, form: str, cfg: Dict[str, float]) -> float:
    tilt = _safe_float(cfg.get("tilt", 0.0), 0.0)
    if form == "abs_quad":
        x = 0.0
    else:
        x = tilt * d
    return float(math.exp(max(-50.0, min(50.0, x))))


def _slot_prob(slot: int, center_slot: int, form: str, base_rate: float, cfg: Dict[str, float], gksl: Dict[str, Any]) -> float:
    d = float(int(slot) - int(center_slot))
    ratio = _visibility_ratio_cached(
        _safe_float(gksl.get("dm2", 0.0025), 0.0025),
        _safe_float(gksl.get("theta_deg", 45.0), 45.0),
        _safe_float(gksl.get("gamma_km_inv", 1.0), 1.0),
        _safe_float(gksl.get("L0_km", 1.0), 1.0),
        _delta_km(d, form, cfg),
        _safe_float(gksl.get("E_GeV", 1.0), 1.0),
        int(_safe_float(gksl.get("steps", 320), 320)),
    )
    return _clip01(_clip01(base_rate) * _gate(d, form, cfg) * ratio)


def _window_union(slots: Any, center_slot: int, form: str, base_rate: float, cfg: Dict[str, float], gksl: Dict[str, Any]) -> float:
    prod = 1.0
    for slot in list(slots or []):
        prod *= (1.0 - _slot_prob(int(slot), center_slot, form, base_rate, cfg, gksl))
    return _clip01(1.0 - prod)


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(run_ctx.get("params", {}) or {})
    center_slot = int(_safe_float(params.get("center_slot", 6), 6))
    form = str(params.get("profile_form", "tilt_abs_quad") or "tilt_abs_quad")
    gksl = dict(params.get("gksl", {}) or {})
    base_block = dict(params.get("pred_base_by_channel", {}) or {})
    profile_block = dict(params.get("global_profile_params", {}) or {})
    slots = list(run_ctx.get("slots", []) or [])

    out: Dict[str, Dict[str, float]] = {}
    for channel in CHANNELS:
        out[channel] = {}
        ch_base = dict(base_block.get(channel, {}) or {})
        ch_prof = dict(profile_block.get(channel, {}) or {})
        for k in KEYS:
            out[channel][k] = _window_union(slots, center_slot, form, _safe_float(ch_base.get(k, 0.0), 0.0), dict(ch_prof.get(k, {}) or {}), gksl)

    label = f"GKSL_DETECTORFIRST_V2 (form={form}; gamma_km_inv={_safe_float(gksl.get('gamma_km_inv',1.0),1.0):.6g}; L0_km={_safe_float(gksl.get('L0_km',1.0),1.0):.6g})"
    return {"__provider_label__": label, "P_pp": out["pp"], "P_p0": out["p0"], "P_0p": out["0p"]}
