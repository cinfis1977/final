"""
thread_env_model.py

A minimal "thread-network UV completion" hook that produces a *spatially varying*
environment factor env_thread(r) from baryonic acceleration g_bar(r), designed to:

1) Reduce to the *old* effective model when disabled (env_thread ≡ 1).
2) Avoid being a trivial rescaling of A by default (median normalization).
3) Be cheap to evaluate (no PDE solves) while still encoding "network coupling"
   via a cumulative (non-local) stress proxy.

This is intentionally a *Phase-2A* module: it makes the thread-network enter
the master-equation pipeline through an effective stress field S(r).
A later Phase-2B can replace the stress proxy with an explicit lattice solve.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional

import os

import numpy as np


if os.environ.get("DM_POISON_PROXY_CALLS") == "1":
    raise RuntimeError("DM proxy path poisoned: thread_env_model import blocked")


NormalizeMode = Literal["none", "mean", "median"]
ThreadMode = Literal["down", "up"]


@dataclass(frozen=True)
class ThreadEnvParams:
    # Reference acceleration scale (m/s^2). For SPARC/RAR, g0 ~ 1e-10 is typical.
    g0: float = 1.2e-10

    # How strongly stress maps into env_thread:
    #   "down": env_thread decreases with stress (stiff regions suppress GEO response)
    #   "up"  : env_thread increases with stress (stress amplifies GEO response)
    mode: ThreadMode = "down"

    # Shape parameter: env_thread = (1 + S)^(-q)  [down]
    #                 env_thread = (1 + S)^(+q)  [up]
    q: float = 0.5

    # Non-local mixing between local stress and cumulative stress (0..1).
    # xi=0: purely local; xi=1: fully non-local (network-coupled).
    xi: float = 0.5

    # Prevent division by zero at r=0 or g_bar=0.
    eps: float = 1e-30

    # Normalize env_thread to avoid degeneracy with the global amplitude A.
    # Recommended: "median"
    normalize: NormalizeMode = "median"

    # Weighting power for non-local cumulative stress integral: w ~ dr/(r^p + eps)
    # p=1 is a simple default.
    r_weight_power: float = 1.0

    # --- Optional non-linear "real-spring" stiffening gate (Phase-2A extension) ---
    # Design goal: let the cube-to-cube thread network *decouple* in mild environments,
    # but turn on only under large stress/curvature (e.g. extreme events).
    #
    # Gate uses an "effective stress" polynomial:
    #   S_eff = k2 * S^2 + k4 * S^4
    # then a smooth activation:
    #   gate = (S_eff/S0)^p / (1 + (S_eff/S0)^p)
    # If S0 is None => gate=1 (backwards compatible with the old thread env).
    S0: Optional[float] = None
    gate_p: float = 4.0
    k2: float = 1.0
    k4: float = 0.0


def gate_factor(S: np.ndarray, *, S0: Optional[float], gate_p: float, k2: float, k4: float) -> np.ndarray:
    """Smooth activation in [0,1]. If S0 is None or non-positive => fully on (1)."""
    S = np.asarray(S, dtype=float)
    if S0 is None:
        return np.ones_like(S)
    try:
        S0f = float(S0)
    except Exception:
        return np.ones_like(S)
    if not np.isfinite(S0f) or S0f <= 0:
        return np.ones_like(S)

    p = float(gate_p) if np.isfinite(gate_p) and gate_p > 0 else 1.0
    k2f = float(k2) if np.isfinite(k2) else 1.0
    k4f = float(k4) if np.isfinite(k4) else 0.0

    Seff = k2f * (S * S) + k4f * (S * S) * (S * S)
    x = np.maximum(Seff, 0.0) / max(S0f, 1e-300)
    xp = np.power(x, p)
    g = xp / (1.0 + xp)
    g = np.where(np.isfinite(g), g, 0.0)
    return np.clip(g, 0.0, 1.0)


def _safe_sort_by_r(r_m: np.ndarray, *arrays: np.ndarray):
    idx = np.argsort(r_m)
    out = [r_m[idx]]
    for a in arrays:
        out.append(a[idx])
    return idx, out


def stress_proxy(r_m: np.ndarray, g_bar: np.ndarray, p: ThreadEnvParams) -> np.ndarray:
    """
    Build a dimensionless stress proxy S(r) from baryonic acceleration.

    Local piece: s_local = (g_bar/g0)^2

    Non-local piece: s_cum(r) = ∫_0^r s_local(r') * dr' / (r'^p + eps)
    Then mixed: S = (1-xi)*s_local + xi*s_cum_scaled
    """
    r_m = np.asarray(r_m, dtype=float)
    g_bar = np.asarray(g_bar, dtype=float)
    if r_m.shape != g_bar.shape:
        raise ValueError("r_m and g_bar must have the same shape")

    idx, (r_sorted, g_sorted) = _safe_sort_by_r(r_m, g_bar)
    s_local = (np.maximum(g_sorted, 0.0) / max(p.g0, p.eps)) ** 2

    # cumulative integral with simple trapezoid in r
    dr = np.diff(r_sorted, prepend=r_sorted[0])
    w = dr / (np.power(np.maximum(r_sorted, 0.0), p.r_weight_power) + p.eps)
    s_cum = np.cumsum(s_local * w)

    # scale cumulative term to be comparable to local term
    # (use median to reduce sensitivity to outliers)
    scale = np.median(s_cum) if np.isfinite(np.median(s_cum)) and np.median(s_cum) > 0 else 1.0
    s_cum_scaled = s_cum / max(scale, p.eps)

    S_sorted = (1.0 - p.xi) * s_local + p.xi * s_cum_scaled

    # un-sort to original order
    S = np.empty_like(S_sorted)
    S[idx] = S_sorted
    return S


def env_thread(
    r_m: np.ndarray,
    g_bar: np.ndarray,
    params: Optional[ThreadEnvParams] = None,
) -> np.ndarray:
    """
    Compute a per-point multiplicative factor env_thread(r) from thread-network stress.

    Default design goal: change *shape* (inner vs outer) without trivially rescaling A,
    via median normalization.
    """
    if params is None:
        params = ThreadEnvParams()

    S = stress_proxy(r_m, g_bar, params)

    if params.mode == "down":
        e = np.power(1.0 + S, -params.q)
    elif params.mode == "up":
        e = np.power(1.0 + S, +params.q)
    else:
        raise ValueError(f"Unknown mode: {params.mode}")

    # Optional non-linear activation: decouple in mild environments.
    # Backwards compatible if params.S0 is None.
    g = gate_factor(S, S0=params.S0, gate_p=params.gate_p, k2=params.k2, k4=params.k4)
    e = 1.0 + g * (e - 1.0)

    # normalization to reduce A–env degeneracy
    if params.normalize == "none":
        pass
    elif params.normalize == "mean":
        mu = float(np.mean(e)) if np.isfinite(np.mean(e)) and np.mean(e) != 0 else 1.0
        e = e / mu
    elif params.normalize == "median":
        med = float(np.median(e)) if np.isfinite(np.median(e)) and np.median(e) != 0 else 1.0
        e = e / med
    else:
        raise ValueError(f"Unknown normalize mode: {params.normalize}")

    # safety clamp: avoid negative/NaN
    e = np.where(np.isfinite(e), e, 1.0)
    e = np.maximum(e, 0.0)
    return e
