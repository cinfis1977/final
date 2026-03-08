#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nova_mastereq_forward_kernel.py

Drop-in forward runner for NOvA channels pack, using the *unified kernel notation*
(consistent with the paper Sec 2.4/2.5 "micro-geometry kernel" language).

Goals:
- Be robust: single-file, no project-internal imports required.
- Produce a debug CSV with per-bin obs, SM pred, GEO pred, and (P_sm, P_geo).
- Provide a sane minimal "geometry kernel" phase dphi(L,E;Theta) with k_rt baseline.

IMPORTANT:
This is a minimal *falsification runner*. It does NOT try to be a full
three-flavor matter-accurate global-fit engine; it is designed to be:
    (pack-driven SM baseline) + (kernel-driven controlled modulation)

If you want bit-for-bit continuity with an older in-repo forward script,
use this as the reference implementation and unify other sector runners to it.
"""

from __future__ import annotations
import argparse
import json
import os
import math
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd


# -----------------------------
# Kernel (Sec 2.4/2.5 style)
# -----------------------------
@dataclass
class KernelParams:
    # Baselines
    L0_km: float = 810.0
    E0_GeV: float = 1.0

    # Core amplitude/energy scaling
    A: float = 0.0
    alpha: float = 0.0
    n: float = 0.0

    # Spatial modulation
    omega_1_per_km: float = 0.0
    phi: float = 0.0
    zeta: float = 0.0  # exponential damping vs L
    breath_B: float = 0.0  # internal elastic (breathing) feedback strength; 0 disables
    breath_omega0_1_per_km: float = 0.0  # breathing natural frequency [1/km]; 0 disables
    breath_gamma: float = 0.2  # breathing damping (dimensionless)
    # --- BREATH -> THREAD transfer (optional) ---
    thread_C: float = 0.0              # coupling strength (0 disables)
    thread_omega0_1_per_km: float = 0.0 # thread natural frequency [1/km] (resolved in main)
    thread_gamma: float = 0.0          # thread damping (dimensionless, like breath_gamma)
    thread_weight_app: float = 0.0     # weight of thread term in appearance channels
    thread_weight_dis: float = 1.0     # weight of thread term in disappearance channels
    # --- Thread transfer gating (v2) ---
    # Motivation: BREATH->THREAD coupling is treated as a *resonant inter-plane transfer* that
    # is strongest near the design baseline L0 (phase-matched), and suppressed when L deviates.
    # This is what prevents NOvA-tuned THREAD from automatically damaging near-by baselines
    # like MINOS unless the coupling is broad enough.
    thread_gate_mode: str = "resonant"   # "none" or "resonant" (phase-matched Gaussian)
    thread_gate_band: float = 1.0        # sigma_phi = band * max(thread_gamma, 1e-3)


    # "Auxiliary field / extra DOF layer" gating + junction filter (minimal)
    kappa_gate: float = 0.0  # >=0
    T0: float = 1.0
    mu: float = 0.0
    eta: float = 0.0  # acts like kappa_junc

    # Geometry stiffness knobs (paper baseline now: k_rt=180)
    k_rt: float = 180.0
    k_rt_ref: float = 180.0  # reference for scaling

    # Switches
    kernel: str = "rt"  # "none" or "rt"


def env_scale(L_km: float, kp: KernelParams) -> float:
    """Minimal env_scale(L): keep as 1 unless user wants distance scaling.
    Here: 1.0 for stability. (Can be upgraded sector-by-sector later.)
    """
    return 1.0


def gate_factor(L_km: float, kp: KernelParams) -> float:
    """Auxiliary-field gate: smooth turn-on / saturation.
    Using the paper-like 'junction filter' style: G = L/(L + kappa_gate*L0)
    """
    if kp.kappa_gate <= 0:
        return 1.0
    # scale kappa_gate by L0 so kp.kappa_gate is dimensionless-ish knob
    denom = L_km + (kp.kappa_gate * kp.L0_km)
    if denom <= 0:
        return 1.0
    return float(L_km / denom)


def junction_filter(L_km: float, kp: KernelParams) -> float:
    """J(tau; kappa) = tau/(tau + kappa).
    Here: tau(L) = T0*(L/L0)^mu, kappa = eta.
    """
    if kp.eta <= 0:
        return 1.0
    x = max(L_km / max(kp.L0_km, 1e-12), 1e-12)
    tau = kp.T0 * (x ** kp.mu) if kp.mu != 0 else kp.T0
    denom = tau + kp.eta
    if denom <= 0:
        return 1.0
    return float(tau / denom)


def omega0_geom_fixed(L0_km: float) -> float:
    """Historically your runs used omega0_geom=fixed with:
        omega0 = pi / L0   (so that omega0 * (2*L0) = 2*pi)
    This matches omega0 ≈ 0.0038785 1/km for L0=810 km.
    """
    if L0_km <= 0:
        return 0.0
    return math.pi / L0_km


def _breath_transfer(omega_drive_1_per_km: float, omega0_1_per_km: float, gamma: float) -> tuple[float, float]:
    """Standard damped driven-oscillator transfer (dimensionless). Returns (amp, phase_lag).

    amp = 1/sqrt((1-r^2)^2 + (2*gamma*r)^2),  phase_lag = -atan2(2*gamma*r, 1-r^2),  r=omega/omega0
    """
    if omega0_1_per_km <= 0.0 or omega_drive_1_per_km == 0.0:
        return 0.0, 0.0
    r = omega_drive_1_per_km / omega0_1_per_km
    denom = (1.0 - r * r) ** 2 + (2.0 * gamma * r) ** 2
    amp = 1.0 / math.sqrt(denom) if denom > 0.0 else 0.0
    phase_lag = -math.atan2(2.0 * gamma * r, 1.0 - r * r)
    return amp, phase_lag


def _wrap_to_pi(x: float) -> float:
    """Wrap an angle to [-pi, pi)."""
    return (x + math.pi) % (2.0 * math.pi) - math.pi


def _thread_gate_factor(L_km: float, kp: "KernelParams") -> float:
    """Gate for BREATH->THREAD transfer.

    v2 idea: THREAD transfer is resonant / phase-matched around the design baseline L0.
    We use a Gaussian in phase mismatch:

        g = exp( -0.5 * (Δφ / σφ)^2 ),
        Δφ = wrap( ω L - ω L0 ),
        σφ = thread_gate_band * max(thread_gamma, 1e-3).

    This introduces *no new scanned parameter* by default (band=1), and makes
    MINOS-like baselines naturally suppress the thread transfer if they are off L0.
    """
    mode = str(getattr(kp, "thread_gate_mode", "resonant")).lower()
    if mode in ("none", "off", "0", "false"):
        return 1.0
    # If thread is disabled anyway, don't gate
    if getattr(kp, "thread_C", 0.0) == 0.0:
        return 1.0
    omega = float(getattr(kp, "omega_1_per_km", 0.0))
    if omega == 0.0:
        return 1.0

    dphi = _wrap_to_pi(omega * float(L_km) - omega * float(kp.L0_km))
    gamma = float(getattr(kp, "thread_gamma", 0.0))
    band = float(getattr(kp, "thread_gate_band", 1.0))
    sigma_phi = max(1e-6, band * max(abs(gamma), 1e-3))
    return math.exp(-0.5 * (dphi / sigma_phi) ** 2)


def kernel_phase_dphi_components(L_km: float, E_GeV: float, kp: KernelParams) -> tuple[float, float, float, float, float, float, float]:
    """Return (dphi_base, dphi_breath, dphi_thread, breath_amp, breath_phase_lag, thread_amp, thread_phase_lag).

    dphi_base   : original rt/cv phase perturbation
    dphi_breath : internal breathing mode response (w0,gamma)
    dphi_thread : BREATH->THREAD transferred response (optional; weighted per channel in main)
    """
    # shared energy & baseline scaling
    xE = (E_GeV / kp.E0_GeV) if kp.E0_GeV > 0 else 1.0
    sE = (xE ** kp.n) * (1.0 + kp.alpha * (xE - 1.0))
    sL = (L_km / kp.L0_km) if kp.L0_km > 0 else 1.0
    A_eff = kp.A

    if kp.kernel == "rt":
        damp = math.exp(-kp.zeta * abs(kp.omega_1_per_km) * sL)
        mod = math.sin(kp.omega_1_per_km * L_km + kp.phi)
        dphi_base = A_eff * sE * sL * damp * mod

    elif kp.kernel == "cv":
        # "curvature pulse" centered near L0: Gaussian-like envelope in baseline space
        sigma = (kp.zeta * kp.L0_km) if kp.L0_km > 0 else 1.0
        if sigma <= 0:
            sigma = 1.0
        env = math.exp(-0.5 * ((L_km - kp.L0_km) / sigma) ** 2)
        mod = math.sin(kp.omega_1_per_km * L_km + kp.phi)
        dphi_base = A_eff * sE * env * mod

    else:
        dphi_base = 0.0

    # additional internal elastic ("breathing") feedback
    dphi_breath = 0.0
    dphi_thread = 0.0
    thread_amp = 0.0
    thread_phase = 0.0
    breath_amp = 0.0
    breath_phase = 0.0
    if kp.breath_B != 0.0 and kp.breath_omega0_1_per_km > 0.0:
        breath_amp, breath_phase = _breath_transfer(kp.omega_1_per_km, kp.breath_omega0_1_per_km, kp.breath_gamma)
        if breath_amp != 0.0:
            # same envelope & scaling as base mode, but with oscillator phase-lag
            if kp.kernel == "rt":
                damp = math.exp(-kp.zeta * abs(kp.omega_1_per_km) * sL)
                mod_b = math.sin(kp.omega_1_per_km * L_km + kp.phi + breath_phase)
                dphi_breath = kp.breath_B * A_eff * sE * sL * damp * mod_b * breath_amp
                if kp.thread_C != 0.0:
                    thread_amp, thread_phase = _breath_transfer(kp.omega_1_per_km, kp.thread_omega0_1_per_km, kp.thread_gamma)
                    mod_t = math.sin(kp.omega_1_per_km * L_km + kp.phi + breath_phase + thread_phase)
                    dphi_thread = kp.thread_C * kp.breath_B * A_eff * sE * sL * damp * mod_t * breath_amp * thread_amp
                    dphi_thread *= _thread_gate_factor(L_km, kp)
            elif kp.kernel == "cv":
                sigma = (kp.zeta * kp.L0_km) if kp.L0_km > 0 else 1.0
                if sigma <= 0:
                    sigma = 1.0
                env = math.exp(-0.5 * ((L_km - kp.L0_km) / sigma) ** 2)
                mod_b = math.sin(kp.omega_1_per_km * L_km + kp.phi + breath_phase)
                dphi_breath = kp.breath_B * A_eff * sE * env * mod_b * breath_amp
                if kp.thread_C != 0.0:
                    thread_amp, thread_phase = _breath_transfer(kp.omega_1_per_km, kp.thread_omega0_1_per_km, kp.thread_gamma)
                    mod_t = math.sin(kp.omega_1_per_km * L_km + kp.phi + breath_phase + thread_phase)
                    dphi_thread = kp.thread_C * kp.breath_B * A_eff * sE * env * mod_t * breath_amp * thread_amp

    return dphi_base, dphi_breath, dphi_thread, breath_amp, breath_phase, thread_amp, thread_phase


def kernel_phase_dphi(L_km: float, E_GeV: float, kp: KernelParams) -> float:
    dphi_base, dphi_breath, dphi_thread, *_ = kernel_phase_dphi_components(L_km, E_GeV, kp)
    return dphi_base + dphi_breath + dphi_thread

def prob_appearance_sm(E: float, L: float) -> float:
    """
    Minimal νμ->νe appearance probability.
    P ≈ sin^2(theta23) * sin^2(2*theta13) * sin^2(1.27*dm2*L/E)
    """
    # Typical values (tunable later)
    theta23 = math.radians(45.0)
    theta13 = math.radians(8.6)
    dm2 = 2.50e-3  # eV^2

    amp = (math.sin(theta23) ** 2) * (math.sin(2 * theta13) ** 2)
    Delta = 1.267 * dm2 * L / max(E, 1e-12)
    return float(amp * (math.sin(Delta) ** 2))


def prob_disappearance_sm(E: float, L: float) -> float:
    """
    Minimal νμ survival probability.
    P ≈ 1 - sin^2(2*theta23) * sin^2(1.27*dm2*L/E)
    """
    theta23 = math.radians(45.0)
    dm2 = 2.50e-3  # eV^2
    amp = (math.sin(2 * theta23) ** 2)
    Delta = 1.267 * dm2 * L / max(E, 1e-12)
    return float(1.0 - amp * (math.sin(Delta) ** 2))


def apply_phase_shift_to_prob(P_sm: np.ndarray, dphi: np.ndarray, mode: str) -> np.ndarray:
    """
    Convert baseline probability P_sm -> P_geo by applying Δ -> Δ + dphi
    using an invert-and-reapply trick, to avoid needing full oscillation internals.

    mode:
      - "appearance": assume P = A0 * sin^2(Δ); infer sin^2Δ from P_sm/A0
      - "disappearance": assume P = cos^2(Δ)  (maximal mixing); infer Δ from arccos(sqrt(P))
    """
    P_sm = np.clip(P_sm.astype(float), 0.0, 1.0)
    dphi = dphi.astype(float)

    if mode == "appearance":
        # Use the same amplitude constant as in prob_appearance_sm()
        theta23 = math.radians(45.0)
        theta13 = math.radians(8.6)
        A0 = (math.sin(theta23) ** 2) * (math.sin(2 * theta13) ** 2)
        A0 = max(A0, 1e-12)
        sin2 = np.clip(P_sm / A0, 0.0, 1.0)
        Delta = np.arcsin(np.sqrt(sin2))  # in [0, pi/2]
        P_geo = A0 * (np.sin(Delta + dphi) ** 2)
        return np.clip(P_geo, 0.0, 1.0)

    # disappearance (survival)
    # P = cos^2Δ => Δ = arccos(sqrt(P))
    Delta = np.arccos(np.sqrt(P_sm))
    P_geo = (np.cos(Delta + dphi) ** 2)
    return np.clip(P_geo, 0.0, 1.0)


# -----------------------------
# Utilities
# -----------------------------
def sum_bkg(components: Dict[str, List[float]]) -> np.ndarray:
    total = None
    for _, arr in components.items():
        a = np.asarray(arr, dtype=float)
        total = a if total is None else (total + a)
    return total if total is not None else np.zeros(0, dtype=float)


def safe_ratio(num: np.ndarray, den: np.ndarray, floor: float = 1e-12) -> np.ndarray:
    den2 = np.where(np.abs(den) < floor, np.sign(den) * floor, den)
    den2 = np.where(np.abs(den2) < floor, floor, den2)
    return num / den2


def chi2_gauss_loose(obs: np.ndarray, pred: np.ndarray, systfrac: float = 0.0) -> float:
    """
    Lightweight, stable chi2. This is NOT the publication-grade statistic;
    it's for debug sanity only.

    var = max(pred, 1.0) + (systfrac*pred)^2
    """
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    var = np.maximum(pred, 1.0) + (systfrac * pred) ** 2
    return float(np.sum((obs - pred) ** 2 / var))


def shift_bins(arr: np.ndarray, shift: int) -> np.ndarray:
    """
    Shift an array by integer bins, filling with zeros.
    Positive shift: move content to higher index (right).
    Negative shift: move content to lower index (left).
    """
    arr = np.asarray(arr, float)
    if shift == 0:
        return arr.copy()
    out = np.zeros_like(arr)
    if shift > 0:
        out[shift:] = arr[:-shift]
    else:
        out[:shift] = arr[-shift:]
    return out


# -----------------------------
# Main
# -----------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="NOvA forward runner using unified kernel notation (k_rt baseline).")

    ap.add_argument("--pack", required=True, help="Path to nova_channels.json pack")

    # bin shifts (kept for continuity with older runs)
    ap.add_argument("--bin_shift_app", type=int, default=0)
    ap.add_argument("--bin_shift_dis", type=int, default=0)

    # kernel switch
    ap.add_argument("--kernel", default="rt", choices=["none", "rt"], help="Kernel mode (none or rt)")

    # kernel params
    ap.add_argument("--k_rt", type=float, default=180.0, help="RT stiffness baseline (user baseline now 180)")
    ap.add_argument("--A", type=float, default=0.0)
    ap.add_argument(
        "--alpha",
        type=float,
        default=0.0,
        help="DEPRECATED (WEAK only): use --weak_alpha_Etilt. Kept for backward compatibility.",
    )
    ap.add_argument(
        "--weak_alpha_Etilt",
        type=float,
        default=None,
        help="WEAK kernel energy-tilt modifier; overrides --alpha if provided.",
    )
    ap.add_argument("--n", type=float, default=0.0)
    ap.add_argument("--E0", type=float, default=1.0)
    ap.add_argument("--phi", type=float, default=math.pi/2)

    ap.add_argument("--omega", type=float, default=0.0, help="omega [1/km] for spatial modulation")
    ap.add_argument("--omega0_geom", default="fixed", choices=["fixed", "free"], help="If fixed, omega=pi/L0 unless --omega provided.")
    ap.add_argument("--L0_km", type=float, default=810.0)

    ap.add_argument("--zeta", type=float, default=0.0)
    ap.add_argument("--breath_B", type=float, default=0.0, help="internal breathing feedback amplitude (relative to A); 0 disables")
    ap.add_argument("--breath_w0", type=float, default=0.0, help="breathing natural frequency [1/km]; 0 disables")
    ap.add_argument("--breath_gamma", type=float, default=0.2, help="breathing damping (dimensionless); used if breath_w0>0")
    # --- BREATH -> THREAD transfer (optional) ---
    ap.add_argument("--thread_C", type=float, default=0.0, help="couple BREATH response into a secondary thread-like response (0 disables)")
    ap.add_argument("--thread_w0", type=float, default=-1.0, help="thread natural frequency [1/km]; <0 => use breath_w0")
    ap.add_argument("--thread_gamma", type=float, default=0.0, help="thread damping gamma (dimensionless)")
    ap.add_argument("--thread_weight_app", type=float, default=0.0, help="weight of thread term in appearance channels")
    ap.add_argument("--thread_weight_dis", type=float, default=1.0, help="weight of thread term in disappearance channels")

    ap.add_argument("--thread_gate_mode", type=str, default="resonant", choices=["none", "resonant"],
                    help="gating for BREATH->THREAD transfer: resonant suppresses thread away from L0")
    ap.add_argument("--thread_gate_band", type=float, default=1.0,
                    help="sigma_phi = thread_gate_band * max(thread_gamma, 1e-3); smaller => narrower resonance")

    ap.add_argument("--kappa_gate", type=float, default=0.0)
    ap.add_argument("--T0", type=float, default=1.0)
    ap.add_argument("--mu", type=float, default=0.0)
    ap.add_argument("--eta", type=float, default=0.0)

    # matter density is only printed for continuity; this minimal runner doesn't use it yet
    ap.add_argument("--rho", type=float, default=0.0)
    ap.add_argument("--Ye", type=float, default=0.5)

    # chi2 debug knob
    ap.add_argument("--systfrac", type=float, default=0.0, help="Loose chi2 systematic fraction (debug only)")

    ap.add_argument("--out", required=True, help="Output CSV path")

    args = ap.parse_args()

    weak_alpha_Etilt = float(args.alpha) if args.weak_alpha_Etilt is None else float(args.weak_alpha_Etilt)

    with open(args.pack, "r", encoding="utf-8") as f:
        pack = json.load(f)

    baseline_km = float(pack.get("meta", {}).get("baseline_km", 810.0))

    # Build kernel params
    kp = KernelParams(
        L0_km=float(args.L0_km),
        E0_GeV=float(args.E0),
        A=float(args.A),
        alpha=float(weak_alpha_Etilt),
        n=float(args.n),
        omega_1_per_km=float(args.omega),
        phi=float(args.phi),
        zeta=float(args.zeta),
        breath_B=float(args.breath_B),
        breath_omega0_1_per_km=float(args.breath_w0),
        breath_gamma=float(args.breath_gamma),
        thread_C=float(args.thread_C),
        thread_gamma=float(args.thread_gamma),
        thread_weight_app=float(args.thread_weight_app),
        thread_weight_dis=float(args.thread_weight_dis),
        thread_gate_mode=str(args.thread_gate_mode),
        thread_gate_band=float(args.thread_gate_band),
        kappa_gate=float(args.kappa_gate),
        T0=float(args.T0),
        mu=float(args.mu),
        eta=float(args.eta),
        k_rt=float(args.k_rt),
        k_rt_ref=180.0,
        kernel=str(args.kernel),
    )

    # Resolve thread natural frequency: default to breath_w0 unless user overrides
    kp.thread_omega0_1_per_km = kp.breath_omega0_1_per_km if float(args.thread_w0) < 0 else float(args.thread_w0)

    # omega0_geom=fixed convenience
    if args.omega0_geom == "fixed" and (args.omega == 0.0):
        kp.omega_1_per_km = omega0_geom_fixed(kp.L0_km)

    print(f"omega0_geom [1/km] = {kp.omega_1_per_km}")

    rows = []
    totals = []

    print("\n========================")
    print("REAL-DATA FORWARD SUMMARY")
    print("========================")
    print(f"pack      : {args.pack}")
    print(f"baseline  : L={baseline_km:.1f} km")
    print(f"matter    : rho={args.rho} g/cm^3, Ye={args.Ye}")
    print(f"kernel    : mode={kp.kernel} k_rt={kp.k_rt} A={kp.A} weak_alpha_Etilt={kp.alpha} n={kp.n} omega={kp.omega_1_per_km} phi={kp.phi} zeta={kp.zeta} kappa_gate={kp.kappa_gate} T0={kp.T0} mu={kp.mu} eta={kp.eta} breath_B={kp.breath_B} breath_w0={kp.breath_omega0_1_per_km} breath_gamma={kp.breath_gamma} thread_C={kp.thread_C} thread_w0={kp.thread_omega0_1_per_km} thread_gamma={kp.thread_gamma} thread_w_app={kp.thread_weight_app} thread_w_dis={kp.thread_weight_dis} thread_gate={kp.thread_gate_mode} gate_band={kp.thread_gate_band}")
    print("")

    for ch in pack["channels"]:
        name = ch["name"]
        ctype = ch["type"]  # "appearance" or "disappearance"
        is_antinu = bool(ch.get("is_antinu", False))
        L_km = float(ch.get("baseline_km", baseline_km))

        bins = ch["bins"]
        E_lo = np.asarray(bins["E_lo"], float)
        E_hi = np.asarray(bins["E_hi"], float)
        E_ctr = np.asarray(bins["E_ctr"], float)

        obs = np.asarray(bins["N_obs"], float)
        sig_sm = np.asarray(bins["N_sig_sm"], float)
        bkg_sm = np.asarray(bins["N_bkg_sm"], float)
        pred_sm = sig_sm + bkg_sm

        # Baseline probabilities:
        # - disappearance: if N_sig_noosc exists, infer P_sm_ref = sig_sm/noosc
        # - appearance: use minimal formula (kept stable)
        if ctype == "disappearance" and ("N_sig_noosc" in bins):
            noosc = np.asarray(bins["N_sig_noosc"], float)
            P_sm = np.clip(safe_ratio(sig_sm, noosc, floor=1e-12), 0.0, 1.0)
        else:
            # appearance (or fallback)
            P_sm = np.array([prob_appearance_sm(e, L_km) if ctype == "appearance" else prob_disappearance_sm(e, L_km) for e in E_ctr], float)

        # Apply integer bin shifts for continuity (shifting SIGNAL only; bkg unchanged)
        if ctype == "appearance" and args.bin_shift_app != 0:
            sig_sm = shift_bins(sig_sm, args.bin_shift_app)
            pred_sm = sig_sm + bkg_sm
            P_sm = shift_bins(P_sm, args.bin_shift_app)

        if ctype == "disappearance" and args.bin_shift_dis != 0:
            sig_sm = shift_bins(sig_sm, args.bin_shift_dis)
            pred_sm = sig_sm + bkg_sm
            P_sm = shift_bins(P_sm, args.bin_shift_dis)

        # Kernel phase per bin
        comps = [kernel_phase_dphi_components(L_km, float(e), kp) for e in E_ctr]
        dphi_base = np.array([c[0] for c in comps], float)
        dphi_breath = np.array([c[1] for c in comps], float)
        dphi_thread = np.array([c[2] for c in comps], float)
        breath_amp = np.array([c[3] for c in comps], float)
        breath_phase = np.array([c[4] for c in comps], float)
        thread_amp = np.array([c[5] for c in comps], float)
        thread_phase = np.array([c[6] for c in comps], float)
        w_thread = kp.thread_weight_app if ctype == "appearance" else kp.thread_weight_dis
        dphi = dphi_base + dphi_breath + w_thread * dphi_thread


        # P_geo by phase-shift method
        P_geo = apply_phase_shift_to_prob(P_sm, dphi, "appearance" if ctype == "appearance" else "disappearance")

        # Pred geo: scale signal by ratio P_geo/P_sm, keep bkg fixed
        ratio = safe_ratio(P_geo, P_sm, floor=1e-6)
        sig_geo = sig_sm * ratio
        pred_geo = sig_geo + bkg_sm

        # chi2 (debug only)
        chi2_sm = chi2_gauss_loose(obs, pred_sm, systfrac=args.systfrac)
        chi2_geo = chi2_gauss_loose(obs, pred_geo, systfrac=args.systfrac)
        dchi2 = chi2_sm - chi2_geo
        totals.append((name, chi2_sm, chi2_geo, dchi2))

        print(f"- {name:18s} type={ctype:12s} antinu={str(is_antinu).lower():5s} bins={len(obs):2d}  chi2_SM={chi2_sm:8.3f}  chi2_GEO={chi2_geo:8.3f}  dchi2={dchi2:8.3f}")

        # Write per-bin debug rows
        for i in range(len(obs)):
            rows.append({
                "channel": name,
                "i": int(i),
                "E_lo": float(E_lo[i]),
                "E_hi": float(E_hi[i]),
                "E_ctr": float(E_ctr[i]),
                "obs": float(obs[i]),
                "pred_sm": float(pred_sm[i]),
                "pred_geo": float(pred_geo[i]),
                "bkg": float(bkg_sm[i]),
                "P_sm": float(P_sm[i]),
                "P_geo": float(P_geo[i]),
                "dphi": float(dphi[i]),
                "dphi_base": float(dphi_base[i]),
                "dphi_breath": float(dphi_breath[i]),
                "dphi_thread": float(dphi_thread[i]),
                "thread_weight": float(w_thread),
                "thread_amp": float(thread_amp[i]),
                "thread_phase": float(thread_phase[i]),
                "breath_amp": float(breath_amp[i]),
                "breath_phase": float(breath_phase[i]),
                "k_rt": float(kp.k_rt),
                "kappa_gate": float(kp.kappa_gate),
                "eta": float(kp.eta),
                "omega": float(kp.omega_1_per_km),
            })

    tot_sm = sum(x[1] for x in totals)
    tot_geo = sum(x[2] for x in totals)
    tot_d = tot_sm - tot_geo

    print("\n------------------------")
    print(f"TOTAL chi2_SM  = {tot_sm:.3f}")
    print(f"TOTAL chi2_GEO = {tot_geo:.3f}")
    print(f"Delta chi2 = chi2_SM - chi2_GEO = {tot_d:.3f}")
    print("------------------------\n")

    out_path = args.out
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
