#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Predictive slot-kernel CH provider — DROP-IN v1

Purpose
-------
This provider is designed as a stricter, more honest alternative to calibrated
closure bridges:

- it uses only per-run `slot6` seed channels for the target run,
- it uses a globally fitted slot-dynamics profile learned from training runs,
- it does NOT read target-run wide-window CH channels.

It plugs directly into:
  nist_ch_model_scorecard_v1_DROPIN.py

Expected params structure
-------------------------
The scorecard passes `defaults + runs[run_id]` as `run_ctx["params"]`.
This provider expects that merged dict to contain:

- center_slot: int
- slot_profile_model: "exp_tilt_quad"
- profile_scope: "by_channel" or "by_channel_setting"
- profiles: {
    "pp": {"tilt": ..., "quad": ...} or {"00": {...}, ...},
    "p0": ...,
    "0p": ...,
  }
- p_pp_seed_by_setting: {"00":...,"01":...,"10":...,"11":...}
- p_p0_seed_by_setting: {"00":...,"01":...,"10":...,"11":...}
- p_0p_seed_by_setting: {"00":...,"01":...,"10":...,"11":...}

This is a predictive dynamic bridge. It is NOT a direct-CH calibrated closure.
"""
from __future__ import annotations

import math
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
        "quad": max(0.0, _safe_float(cfg.get("quad", 0.0), 0.0)),
    }


def _slot_scale(slot: int, center_slot: int, profile: Dict[str, float]) -> float:
    d = float(int(slot) - int(center_slot))
    tilt = float(profile.get("tilt", 0.0))
    quad = max(0.0, float(profile.get("quad", 0.0)))
    log_scale = tilt * d - quad * d * d
    if log_scale > 50.0:
        log_scale = 50.0
    if log_scale < -50.0:
        log_scale = -50.0
    return float(math.exp(log_scale))


def _window_union(seed: float, slots: Any, center_slot: int, profile: Dict[str, float]) -> float:
    seed = _clip01(seed)
    if seed <= 0.0:
        return 0.0
    prod = 1.0
    for slot in list(slots or []):
        scale = _slot_scale(int(slot), int(center_slot), profile)
        p_slot = _clip01(seed * scale)
        prod *= (1.0 - p_slot)
    return _clip01(1.0 - prod)


def _channel_window(params: Dict[str, Any], seed_key: str, channel: str, slots: Any, center_slot: int) -> Dict[str, float]:
    seeds = dict(params.get(seed_key, {}) or {})
    out: Dict[str, float] = {}
    for k in KEYS:
        profile = _profile_for(params, channel, k)
        out[k] = _window_union(_safe_float(seeds.get(k, 0.0), 0.0), slots, center_slot, profile)
    return out


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(run_ctx.get("params", {}) or {})
    slots = list(run_ctx.get("slots", []) or [])
    center_slot = int(params.get("center_slot", 6) or 6)

    P_pp = _channel_window(params, "p_pp_seed_by_setting", "pp", slots, center_slot)
    P_p0 = _channel_window(params, "p_p0_seed_by_setting", "p0", slots, center_slot)
    P_0p = _channel_window(params, "p_0p_seed_by_setting", "0p", slots, center_slot)

    train_runs = params.get("train_runs", [])
    if isinstance(train_runs, list) and train_runs:
        train_label = ",".join(str(x) for x in train_runs)
    else:
        train_label = "auto"

    label = (
        "PREDICTIVE SLOTKERNEL v1 "
        f"(strict holdout bridge; center_slot={center_slot}; train_runs={train_label})"
    )
    return {
        "__provider_label__": label,
        "P_pp": P_pp,
        "P_p0": P_p0,
        "P_0p": P_0p,
    }
