from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np


Channel = Literal["pp", "pbarp"]


@dataclass(frozen=True)
class PDGParamsSigmaTot:
    """Parameter block matching `strong_sigma_tot_energy_scan_v2.py` defaults."""

    P_mb: float = 33.73
    H_mb: float = 0.2838
    R1_mb: float = 13.67
    eta1: float = 0.412
    R2_mb: float = 7.77
    eta2: float = 0.5626
    mN_GeV: float = 0.938
    M_GeV: float = 2.076

    @property
    def sM_GeV2(self) -> float:
        return (2.0 * self.mN_GeV + self.M_GeV) ** 2


@dataclass(frozen=True)
class PDGParamsRho:
    """Parameter block matching `strong_rho_energy_scan_v3.py` defaults."""

    sM_GeV2: float = 1.0
    P_mb: float = 33.73
    H_mb: float = 0.283
    R1_mb: float = 13.67
    eta1: float = 0.412
    R2_mb: float = 7.77
    eta2: float = 0.562


@dataclass
class PDGBasisState:
    """Stateful 'film' evolution in t = ln(s/sM).

    We evolve basis functions along t with exact stepping (no drift):
      - t itself
      - e1(t) = exp(-eta1 * t)
      - e2(t) = exp(-eta2 * t)

    Other basis pieces (t^2) are derived from t.

    This turns the legacy closed-form PDG baseline into an explicit internal-state
    evolution, so downstream observables can be computed from state.
    """

    t: float
    e1: float
    e2: float

    @staticmethod
    def from_t0(t0: float, eta1: float, eta2: float) -> "PDGBasisState":
        return PDGBasisState(t=float(t0), e1=float(math.exp(-eta1 * t0)), e2=float(math.exp(-eta2 * t0)))

    def advance_to(self, t_new: float, eta1: float, eta2: float) -> None:
        t_new = float(t_new)
        dt = t_new - self.t
        if dt == 0.0:
            return
        self.e1 *= float(math.exp(-eta1 * dt))
        self.e2 *= float(math.exp(-eta2 * dt))
        self.t = t_new


def t_from_sqrts(sqrts_GeV: np.ndarray, *, sM_GeV2: float) -> np.ndarray:
    sq = np.asarray(sqrts_GeV, dtype=float)
    s = np.maximum(sq * sq, 1e-300)
    return np.log(np.maximum(s / float(sM_GeV2), 1e-300))


def sigma_from_state(state: PDGBasisState, channel: Channel, *, P_mb: float, H_mb: float, R1_mb: float, eta1: float, R2_mb: float, eta2: float) -> float:
    t = float(state.t)
    base = float(P_mb) + float(H_mb) * (t * t) + float(R1_mb) * float(state.e1)
    odd = float(R2_mb) * float(state.e2)
    return float(base - odd) if channel == "pp" else float(base + odd)


def dsigma_dt_from_state(state: PDGBasisState, channel: Channel, *, H_mb: float, R1_mb: float, eta1: float, R2_mb: float, eta2: float) -> float:
    """Derivative w.r.t. t = ln(s/sM). Note d/d ln(s) is identical (t differs by constant)."""
    t = float(state.t)
    term_log = 2.0 * float(H_mb) * t
    term_r1 = -float(eta1) * float(R1_mb) * float(state.e1)
    term_r2 = -float(eta2) * float(R2_mb) * float(state.e2)
    return float(term_log + term_r1 - term_r2) if channel == "pp" else float(term_log + term_r1 + term_r2)


def scan_sigma_tot_stateful(
    sqrts_GeV: np.ndarray,
    channel: Channel,
    pars: PDGParamsSigmaTot,
    *,
    A_rad: float,
    delta_geo_ref_rad: float,
    c1_abs: float,
    template: Literal["cos", "sin"],
    env_mode: Literal["none", "debroglie", "log", "radius", "eikonal"],
    sqrts_ref_GeV: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (sigma_sm_mb, env_scale, sigma_geo_mb) using stateful evolution in t."""

    sq = np.asarray(sqrts_GeV, dtype=float)
    if sq.ndim != 1:
        raise ValueError("sqrts_GeV must be 1D")

    # Sort -> evolve a single state forward -> map back (film behavior).
    order = np.argsort(sq)
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))

    t_arr = t_from_sqrts(sq[order], sM_GeV2=pars.sM_GeV2)
    state = PDGBasisState.from_t0(float(t_arr[0]), pars.eta1, pars.eta2)

    sigma_sm_sorted = np.empty_like(t_arr)
    ds_dt_sorted = np.empty_like(t_arr)
    for i, ti in enumerate(t_arr):
        state.advance_to(float(ti), pars.eta1, pars.eta2)
        sigma_sm_sorted[i] = sigma_from_state(
            state,
            channel,
            P_mb=pars.P_mb,
            H_mb=pars.H_mb,
            R1_mb=pars.R1_mb,
            eta1=pars.eta1,
            R2_mb=pars.R2_mb,
            eta2=pars.eta2,
        )
        ds_dt_sorted[i] = dsigma_dt_from_state(
            state,
            channel,
            H_mb=pars.H_mb,
            R1_mb=pars.R1_mb,
            eta1=pars.eta1,
            R2_mb=pars.R2_mb,
            eta2=pars.eta2,
        )

    sigma_sm = sigma_sm_sorted[inv]

    if env_mode == "none":
        scale = np.ones_like(sq)
    elif env_mode == "debroglie":
        scale = sq / float(sqrts_ref_GeV)
    elif env_mode == "log":
        scale = 2.0 * np.log(np.maximum(sq, 1e-300) / float(sqrts_ref_GeV))
    elif env_mode == "radius":
        # radius scaling uses sigma_sm(s)/sigma_sm(s_ref)
        t_ref = float(t_from_sqrts(np.array([sqrts_ref_GeV], dtype=float), sM_GeV2=pars.sM_GeV2)[0])
        state_ref = PDGBasisState.from_t0(float(t_arr[0]), pars.eta1, pars.eta2)
        state_ref.advance_to(t_ref, pars.eta1, pars.eta2)
        sigma_sm_ref = sigma_from_state(
            state_ref,
            channel,
            P_mb=pars.P_mb,
            H_mb=pars.H_mb,
            R1_mb=pars.R1_mb,
            eta1=pars.eta1,
            R2_mb=pars.R2_mb,
            eta2=pars.eta2,
        )
        sigma_sm_ref = max(float(sigma_sm_ref), 1e-300)
        scale = np.sqrt(np.maximum(sigma_sm, 1e-300) / sigma_sm_ref)
    else:
        # eikonal scaling: log(s/sM)/log(s_ref/sM) == t/t_ref
        t_ref = float(t_from_sqrts(np.array([sqrts_ref_GeV], dtype=float), sM_GeV2=pars.sM_GeV2)[0])
        if abs(t_ref) < 1e-12:
            scale = np.ones_like(sq)
        else:
            scale = t_from_sqrts(sq, sM_GeV2=pars.sM_GeV2) / t_ref

    if A_rad == 0.0:
        return sigma_sm, np.zeros_like(sq), sigma_sm.copy()

    phase = float(delta_geo_ref_rad) * np.asarray(scale, dtype=float)
    mod = np.cos(phase) if template == "cos" else np.sin(phase)
    sigma_geo = sigma_sm * (1.0 + float(A_rad) * float(c1_abs) * mod)
    return sigma_sm, scale, sigma_geo


def scan_rho_stateful(
    sqrts_GeV: np.ndarray,
    channel: Channel,
    pars: PDGParamsRho,
    *,
    A: float,
    delta_geo_ref: float,
    c1_abs: float,
    template: Literal["cos", "sin"],
    env_mode: Literal["none", "debroglie", "log", "radius", "eikonal", "radius_amp", "eikonal_amp"],
    sqrts_ref_GeV: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (sigma_sm, rho_sm, phi_geo, sigma_geo, rho_geo) with stateful PDG baseline."""

    sq = np.asarray(sqrts_GeV, dtype=float)
    if sq.ndim != 1:
        raise ValueError("sqrts_GeV must be 1D")

    order = np.argsort(sq)
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))

    t_arr = t_from_sqrts(sq[order], sM_GeV2=pars.sM_GeV2)
    state = PDGBasisState.from_t0(float(t_arr[0]), pars.eta1, pars.eta2)

    sigma_sm_sorted = np.empty_like(t_arr)
    ds_dt_sorted = np.empty_like(t_arr)
    for i, ti in enumerate(t_arr):
        state.advance_to(float(ti), pars.eta1, pars.eta2)
        sigma_sm_sorted[i] = sigma_from_state(
            state,
            channel,
            P_mb=pars.P_mb,
            H_mb=pars.H_mb,
            R1_mb=pars.R1_mb,
            eta1=pars.eta1,
            R2_mb=pars.R2_mb,
            eta2=pars.eta2,
        )
        ds_dt_sorted[i] = dsigma_dt_from_state(
            state,
            channel,
            H_mb=pars.H_mb,
            R1_mb=pars.R1_mb,
            eta1=pars.eta1,
            R2_mb=pars.R2_mb,
            eta2=pars.eta2,
        )

    sigma_sm = sigma_sm_sorted[inv]
    ds_dt = ds_dt_sorted[inv]

    sig_safe = np.maximum(sigma_sm, 1e-300)
    rho_sm = (math.pi / 2.0) * (ds_dt / sig_safe)

    # phase_geo from legacy runner, but computed from state-derived sigma_sm where needed.
    arg_scale = None
    amp_scale = np.ones_like(sq, dtype=float)

    if env_mode == "radius":
        # argument scaling using interaction-radius proxy from sigma_SM
        t_ref = float(t_from_sqrts(np.array([sqrts_ref_GeV], dtype=float), sM_GeV2=pars.sM_GeV2)[0])
        state_ref = PDGBasisState.from_t0(float(t_arr[0]), pars.eta1, pars.eta2)
        state_ref.advance_to(t_ref, pars.eta1, pars.eta2)
        sigma_ref = sigma_from_state(
            state_ref,
            channel,
            P_mb=pars.P_mb,
            H_mb=pars.H_mb,
            R1_mb=pars.R1_mb,
            eta1=pars.eta1,
            R2_mb=pars.R2_mb,
            eta2=pars.eta2,
        )
        sigma_ref = max(float(sigma_ref), 1e-300)
        arg_scale = np.sqrt(np.maximum(sigma_sm, 1e-300) / sigma_ref)
    elif env_mode == "eikonal":
        t_ref = float(t_from_sqrts(np.array([sqrts_ref_GeV], dtype=float), sM_GeV2=pars.sM_GeV2)[0])
        arg_scale = np.ones_like(sq) if abs(t_ref) < 1e-12 else (t_from_sqrts(sq, sM_GeV2=pars.sM_GeV2) / t_ref)
    elif env_mode == "radius_amp":
        t_ref = float(t_from_sqrts(np.array([sqrts_ref_GeV], dtype=float), sM_GeV2=pars.sM_GeV2)[0])
        state_ref = PDGBasisState.from_t0(float(t_arr[0]), pars.eta1, pars.eta2)
        state_ref.advance_to(t_ref, pars.eta1, pars.eta2)
        sigma_ref = sigma_from_state(
            state_ref,
            channel,
            P_mb=pars.P_mb,
            H_mb=pars.H_mb,
            R1_mb=pars.R1_mb,
            eta1=pars.eta1,
            R2_mb=pars.R2_mb,
            eta2=pars.eta2,
        )
        sigma_ref = max(float(sigma_ref), 1e-300)
        amp_scale = np.sqrt(np.maximum(sigma_sm, 1e-300) / sigma_ref)
        arg_scale = None
    elif env_mode == "eikonal_amp":
        t_ref = float(t_from_sqrts(np.array([sqrts_ref_GeV], dtype=float), sM_GeV2=pars.sM_GeV2)[0])
        amp_scale = np.ones_like(sq) if abs(t_ref) < 1e-12 else (t_from_sqrts(sq, sM_GeV2=pars.sM_GeV2) / t_ref)
        arg_scale = None
    else:
        # basic argument scaling family, note debroglie is inverse for rho-runner
        if env_mode == "none":
            arg_scale = np.ones_like(sq)
        elif env_mode == "debroglie":
            ref = max(float(sqrts_ref_GeV), 1e-300)
            arg_scale = ref / np.maximum(sq, 1e-300)
        else:
            ref = max(float(sqrts_ref_GeV), 1e-300)
            arg_scale = 2.0 * np.log(np.maximum(sq, 1e-300) / ref)

    phase_arg = float(delta_geo_ref) if arg_scale is None else (float(delta_geo_ref) * np.asarray(arg_scale, dtype=float))
    mod = np.cos(phase_arg) if template == "cos" else np.sin(phase_arg)
    phi = float(A) * float(c1_abs) * amp_scale * mod

    # Apply forward amplitude phase rotation
    c = np.cos(phi)
    s = np.sin(phi)
    re = rho_sm * c - 1.0 * s
    im = rho_sm * s + 1.0 * c

    im_safe = np.where(np.abs(im) < 1e-300, np.sign(im) * 1e-300 + 1e-300, im)
    rho_geo = re / im_safe
    sigma_geo = sigma_sm * im

    return sigma_sm, rho_sm, phi, sigma_geo, rho_geo
