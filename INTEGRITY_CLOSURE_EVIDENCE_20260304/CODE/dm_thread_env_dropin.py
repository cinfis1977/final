# dm_thread_env_dropin.py
# Phase-2A Thread-network "UV completion" hook for DM scripts.
# Produces a per-point env vector that can be multiplied into A (or into the GEO term).
#
# Key properties:
# - Regression-safe: env_model=none => env_vec=1 (old behavior).
# - CV-safe: for thread normalization, learn scale on TRAIN and reuse for TEST (no leakage).

from __future__ import annotations
from typing import Literal, Optional, Tuple
import os
import numpy as np

if os.environ.get("DM_POISON_PROXY_CALLS") == "1":
    raise RuntimeError("DM proxy path poisoned: dm_thread_env_dropin import blocked")


from thread_env_model import ThreadEnvParams, env_thread

NormalizeMode = Literal["none", "mean", "median"]
ThreadMode = Literal["down", "up"]
EnvModel = Literal["legacy", "none", "global", "thread", "global_thread"]

KPC_TO_M = 3.085677581491367e19


def _get_first_present(d: dict, names: tuple[str, ...]):
    for n in names:
        if n in d:
            return n
    return None


def extract_r_m(points_df) -> np.ndarray:
    cols = points_df.columns
    if "r_m" in cols:
        return points_df["r_m"].astype(float).to_numpy()
    # common SPARC-ish names
    rcol = _get_first_present(points_df.iloc[0].to_dict(), ("r_kpc", "R_kpc", "R", "radius_kpc"))
    if rcol is None:
        raise RuntimeError(f"Could not find radius column. Tried r_m or kpc variants. Columns={list(cols)}")
    r = points_df[rcol].astype(float).to_numpy()
    # heuristic: if median < 1e6 treat as kpc
    if np.nanmedian(r) < 1e6:
        r = r * KPC_TO_M
    return r


def extract_g_bar(points_df) -> np.ndarray:
    cols = points_df.columns
    if "g_bar" in cols:
        return points_df["g_bar"].astype(float).to_numpy()
    # try compute from Vbar^2 / r
    vbar_col = _get_first_present(points_df.iloc[0].to_dict(), ("v_bar_kms", "Vbar", "vbar", "Vbar_kms"))
    if vbar_col is None:
        raise RuntimeError(f"Could not find g_bar or a Vbar column to derive it. Columns={list(cols)}")
    r_m = extract_r_m(points_df)
    v_mps = points_df[vbar_col].astype(float).to_numpy() * 1e3
    gbar = (v_mps**2) / np.maximum(r_m, 1e-30)
    return gbar


def extract_g_obs(points_df) -> np.ndarray:
    cols = points_df.columns
    if "g_obs" in cols:
        return points_df["g_obs"].astype(float).to_numpy()
    vobs_col = _get_first_present(points_df.iloc[0].to_dict(), ("v_obs_kms", "Vobs", "vobs", "Vobs_kms"))
    if vobs_col is None:
        raise RuntimeError(f"Could not find g_obs or a Vobs column to derive it. Columns={list(cols)}")
    r_m = extract_r_m(points_df)
    v_mps = points_df[vobs_col].astype(float).to_numpy() * 1e3
    gobs = (v_mps**2) / np.maximum(r_m, 1e-30)
    return gobs


def extract_sigma_log10g(points_df) -> Optional[np.ndarray]:
    """
    If velocity errors exist, compute sigma in log10(g_obs) assuming r error negligible:
      g = V^2/r => log10 g = 2 log10 V - log10 r + const
      sigma_log10g ≈ (2/(ln 10)) * (sigma_V / V)
    Returns None if not available.
    """
    cols = points_df.columns
    if "sigma_log10g" in cols:
        s = points_df["sigma_log10g"].astype(float).to_numpy()
        return np.where(np.isfinite(s) & (s > 0), s, np.nan)

    ev_col = _get_first_present(points_df.iloc[0].to_dict(), ("ev_obs_kms", "eVobs", "evobs", "sigma_v_obs_kms"))
    vobs_col = _get_first_present(points_df.iloc[0].to_dict(), ("v_obs_kms", "Vobs", "vobs", "Vobs_kms"))
    if ev_col is None or vobs_col is None:
        return None

    ev = points_df[ev_col].astype(float).to_numpy() * 1e3
    v = points_df[vobs_col].astype(float).to_numpy() * 1e3
    frac = ev / np.maximum(v, 1e-30)
    sigma = (2.0 / np.log(10.0)) * frac
    sigma = np.where(np.isfinite(sigma) & (sigma > 0), sigma, np.nan)
    return sigma


def extract_env_scale(points_df) -> np.ndarray:
    if os.environ.get("DM_POISON_ENV_SCALE_CALLS") == "1":
        raise RuntimeError("DM env_scale path poisoned: extract_env_scale blocked")
    if "env_scale" in points_df.columns:
        return points_df["env_scale"].astype(float).to_numpy()
    return np.ones(len(points_df), dtype=float)


def compute_env_thread_raw(
    r_m: np.ndarray,
    g_bar: np.ndarray,
    *,
    g0: float,
    mode: ThreadMode,
    q: float,
    xi: float,
    r_weight_power: float,
    thread_S0: Optional[float] = None,
    thread_gate_p: float = 4.0,
    thread_k2: float = 1.0,
    thread_k4: float = 0.0,
) -> np.ndarray:
    if os.environ.get("DM_POISON_THREAD_ENV_CALLS") == "1":
        raise RuntimeError("DM thread-env path poisoned: compute_env_thread_raw blocked")
    # NOTE: normalize is handled outside (train/test safe). Here we return the raw,
    # un-normalized env factor.
    params = ThreadEnvParams(
        g0=float(g0),
        mode=mode,
        q=float(q),
        xi=float(xi),
        normalize="none",
        r_weight_power=float(r_weight_power),
        # optional non-linear gate
        S0=None if thread_S0 is None else float(thread_S0),
        gate_p=float(thread_gate_p),
        k2=float(thread_k2),
        k4=float(thread_k4),
    )
    e = env_thread(r_m, g_bar, params)
    e = np.where(np.isfinite(e), e, 1.0)
    e = np.maximum(e, 0.0)
    return e


def _norm_scale(e_raw: np.ndarray, norm: NormalizeMode) -> float:
    if norm == "none":
        return 1.0
    if norm == "mean":
        mu = float(np.mean(e_raw))
        return mu if np.isfinite(mu) and mu != 0 else 1.0
    if norm == "median":
        med = float(np.median(e_raw))
        return med if np.isfinite(med) and med != 0 else 1.0
    raise ValueError(f"Unknown norm: {norm}")


def build_env_vector(
    points_df,
    *,
    env_model: EnvModel,
    use_env_scale_flag: Optional[bool],  # for legacy compatibility
    g0: float,
    thread_mode: ThreadMode,
    thread_q: float,
    thread_xi: float,
    thread_norm: NormalizeMode,
    thread_r_weight_power: float,
    # Optional non-linear "real spring" gate
    thread_S0: Optional[float] = None,
    thread_gate_p: float = 4.0,
    thread_k2: float = 1.0,
    thread_k4: float = 0.0,
    # CV-safe: provide scale learned on TRAIN; if None, compute from provided df
    norm_scale_ref: Optional[float] = None,
) -> Tuple[np.ndarray, float]:
    """
    Returns (env_vec, norm_scale_used).
    """
    n = len(points_df)
    env = np.ones(n, dtype=float)

    if env_model == "legacy":
        env_model = "global" if bool(use_env_scale_flag) else "none"

    if env_model in ("none",):
        return env, 1.0

    if env_model in ("global", "global_thread"):
        env *= extract_env_scale(points_df)

    if env_model in ("global",):
        return env, 1.0

    if env_model in ("thread", "global_thread"):
        r_m = extract_r_m(points_df)
        g_bar = extract_g_bar(points_df)
        e_raw = compute_env_thread_raw(
            r_m, g_bar,
            g0=g0,
            mode=thread_mode,
            q=thread_q,
            xi=thread_xi,
            r_weight_power=thread_r_weight_power,
            thread_S0=thread_S0,
            thread_gate_p=thread_gate_p,
            thread_k2=thread_k2,
            thread_k4=thread_k4,
        )
        scale = norm_scale_ref if norm_scale_ref is not None else _norm_scale(e_raw, thread_norm)
        if scale == 0 or not np.isfinite(scale):
            e = np.ones_like(e_raw)
        else:
            e = e_raw / scale
        e = np.where(np.isfinite(e), e, 1.0)
        e = np.maximum(e, 0.0)
        env *= e
        return env, float(scale)

    raise ValueError(f"Unknown env_model: {env_model}")
