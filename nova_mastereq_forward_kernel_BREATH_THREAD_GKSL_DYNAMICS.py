#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py

A model-forward WEAK runner that computes probabilities via explicit GKSL integration
(per-bin density-matrix evolution), instead of the legacy invert-and-reapply phase trick.

Scope note (important):
- This uses the repo's current 2-flavor GKSL integrator (`integration_artifacts/mastereq`).
- It keeps the same kernel parameterization and output CSV schema as
  `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py`, so it can be
  validated against existing golden artifacts.

Modes:
- Default: unitary vacuum evolution + geometric mass-sector correction equivalent to dphi.
- Optional: include a (toy) matter potential term and/or damping.

"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _ensure_mastereq_on_path() -> None:
    root = Path(__file__).resolve().parent
    integration_root = root / "integration_artifacts"
    if str(integration_root) not in sys.path:
        sys.path.insert(0, str(integration_root))


_ensure_mastereq_on_path()

from mastereq.unified_gksl import UnifiedGKSL  # noqa: E402
from mastereq.weak_sector import make_weak_damping_fn, ve_from_rho, ve_to_H_km_inv  # noqa: E402
from mastereq.weak_rate_model import compute_sig_sm_from_pack_rate_model  # noqa: E402
from mastereq.weak_rate_kernel import parse_rate_kernel, compute_event_rates_rec  # noqa: E402
from mastereq.unified_gksl_3flavor import UnifiedGKSL3  # noqa: E402
from mastereq.gk_sl_solver_3flavor import lindblad_dephasing_offdiag as lindblad_dephasing_offdiag_3  # noqa: E402
from mastereq.defaults import DEFAULT_GAMMA_KM_INV  # noqa: E402
from mastereq.microphysics import (  # noqa: E402
    gamma_km_inv_from_n_sigma_v,
    sigma_weak_nue_e_cm2,
    sigma_weak_numu_e_cm2,
)

# Reuse the exact kernel contract + utilities from the legacy runner.
from nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude import (  # noqa: E402
    KernelParams,
    chi2_gauss_loose,
    chi2_poisson_deviance,
    kernel_phase_dphi_components,
    omega0_geom_fixed,
    safe_ratio,
    shift_bins,
)


def _theta_for_amp_app(theta23_deg: float, theta13_deg: float) -> tuple[float, float]:
    """Return (A0, theta) such that sin^2(2theta)=A0."""
    theta23 = math.radians(float(theta23_deg))
    theta13 = math.radians(float(theta13_deg))
    A0 = (math.sin(theta23) ** 2) * (math.sin(2 * theta13) ** 2)
    A0 = float(np.clip(A0, 0.0, 1.0))
    theta = 0.5 * math.asin(math.sqrt(max(A0, 0.0)))
    return A0, float(theta)


def _dm2_gksl_from_runner(dm2_runner_eV2: float) -> float:
    """Legacy runner uses Delta=1.267*dm2*L/E.

    The GKSL solver convention is Delta=1.267*dm2*L/(4E).
    Match phases by using dm2_GKSL = 4*dm2_runner.
    """
    return 4.0 * float(dm2_runner_eV2)


def _delta_dm2_gksl_from_dphi(dphi: float, *, L_km: float, E_GeV: float) -> float:
    """Convert a desired additive phase shift dphi into a delta(dm2) in GKSL convention."""
    return float(dphi) * (4.0 * float(E_GeV)) / (1.267 * max(float(L_km), 1e-12))


def _prob_from_rho(rho: np.ndarray, *, channel_type: str) -> float:
    """Match the existing equivalence tests:

    - appearance: use rho[0,0]
    - disappearance: use rho[1,1]

    This is a convention choice for the 2-state toy model.
    """
    if channel_type == "appearance":
        return float(np.real(rho[0, 0]))
    return float(np.real(rho[1, 1]))


def _flavors_for_channel(ch: dict, channel_type: str) -> tuple[str, str]:
    nu_in = ch.get("nu_in")
    nu_out = ch.get("nu_out")
    if nu_in is not None and nu_out is not None:
        return str(nu_in), str(nu_out)
    if channel_type == "appearance":
        return "mu", "e"
    return "mu", "mu"


def _idx3(f: str) -> int:
    m = {"e": 0, "mu": 1, "tau": 2}
    if f not in m:
        raise ValueError(f"Invalid flavor '{f}' (expected e/mu/tau)")
    return m[f]


def _weak_gamma_value(*, gamma: float | None, use_microphysics: bool, n_cm3: float | None, E_GeV_ref: float, channel: str) -> float:
    if gamma is not None:
        return float(gamma)
    if use_microphysics:
        n_val = 1.0e23 if n_cm3 is None else float(n_cm3)
        ch = str(channel).lower()
        if ch == "numu_e":
            sigma = sigma_weak_numu_e_cm2(E_GeV_ref)
        else:
            sigma = sigma_weak_nue_e_cm2(E_GeV_ref)
        return float(gamma_km_inv_from_n_sigma_v(n_val, sigma, 3.0e10))
    return float(DEFAULT_GAMMA_KM_INV)


def _rho_telemetry_3(rho: np.ndarray) -> dict:
    rho_h = 0.5 * (rho + rho.conj().T)
    evals = np.linalg.eigvalsh(rho_h)
    return {
        "trace": float(np.real(np.trace(rho_h))),
        "min_eig": float(np.min(evals)),
        "purity": float(np.real(np.trace(rho_h @ rho_h))),
        "herm_err": float(np.max(np.abs(rho - rho.conj().T))),
        "Pe": float(np.real(rho_h[0, 0])),
        "Pmu": float(np.real(rho_h[1, 1])),
        "Ptau": float(np.real(rho_h[2, 2])),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="NOvA/T2K forward runner with explicit GKSL integration (2- or 3-flavor).")

    ap.add_argument("--pack", required=True)

    # bin shifts (kept for continuity with older runs)
    ap.add_argument("--bin_shift_app", type=int, default=0)
    ap.add_argument("--bin_shift_dis", type=int, default=0)

    # kernel params (same surface API as legacy runner)
    ap.add_argument("--kernel", default="rt", choices=["none", "rt"])
    ap.add_argument("--k_rt", type=float, default=180.0)
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
    ap.add_argument("--phi", type=float, default=math.pi / 2)

    ap.add_argument("--omega", type=float, default=0.0)
    ap.add_argument("--omega0_geom", default="fixed", choices=["fixed", "free"])
    ap.add_argument("--L0_km", type=float, default=810.0)

    ap.add_argument("--zeta", type=float, default=0.0)
    ap.add_argument("--breath_B", type=float, default=0.0)
    ap.add_argument("--breath_w0", type=float, default=0.0)
    ap.add_argument("--breath_gamma", type=float, default=0.2)

    ap.add_argument("--thread_C", type=float, default=0.0)
    ap.add_argument("--thread_w0", type=float, default=-1.0)
    ap.add_argument("--thread_gamma", type=float, default=0.0)
    ap.add_argument("--thread_weight_app", type=float, default=0.0)
    ap.add_argument("--thread_weight_dis", type=float, default=1.0)

    ap.add_argument("--kappa_gate", type=float, default=0.0)
    ap.add_argument("--T0", type=float, default=1.0)
    ap.add_argument("--mu", type=float, default=0.0)
    ap.add_argument("--eta", type=float, default=0.0)

    # matter + damping knobs (new)
    ap.add_argument("--rho", type=float, default=0.0)
    ap.add_argument("--Ye", type=float, default=0.5)
    ap.add_argument("--use_matter", action="store_true", help="Enable a flavor-basis matter potential term.")

    ap.add_argument("--gamma", type=float, default=None, help="Enable off-diagonal damping with this gamma [1/km].")
    ap.add_argument("--use_microphysics", action="store_true", help="If --gamma not given, derive gamma from n*sigma*v (toy templates).")
    ap.add_argument("--n_cm3", type=float, default=None)
    ap.add_argument("--weak_channel", choices=["nue_e", "numu_e"], default="nue_e")
    ap.add_argument("--E_GeV_ref", type=float, default=1.0)

    ap.add_argument("--steps", type=int, default=950, help="RK4 steps for GKSL integration per bin")

    ap.add_argument("--flavors", type=int, default=2, choices=[2, 3], help="Internal dynamics dimensionality")

    ap.add_argument("--dm2_runner_eV2", type=float, default=2.50e-3, help="Legacy phase convention dm2 used in older runner formula")
    ap.add_argument("--theta23_deg", type=float, default=45.0)
    ap.add_argument("--theta13_deg", type=float, default=8.6)

    # 3-flavor parameters
    ap.add_argument("--dm21_eV2", type=float, default=7.53e-5)
    ap.add_argument("--dm31_eV2", type=float, default=2.45e-3)
    ap.add_argument("--theta12_deg", type=float, default=33.44)
    ap.add_argument("--delta_cp_deg", type=float, default=195.0)

    # chi2 (debug only)
    ap.add_argument(
        "--chi2_mode",
        default="gauss_loose",
        choices=["gauss_loose", "poisson_dev"],
        help="Chi2 mode (debug only). Default matches legacy behavior.",
    )
    ap.add_argument(
        "--poisson_shape",
        default="none",
        choices=["none", "per_channel", "per_channel_common"],
        help=(
            "For chi2_mode=poisson_dev: shape-only normalization options. "
            "per_channel profiles separate scales for SM and GEO; per_channel_common uses SM-derived scale for both."
        ),
    )
    ap.add_argument("--systfrac", type=float, default=0.0)
    ap.add_argument(
        "--sigma_floor",
        type=float,
        default=0.0,
        help="Absolute sigma floor added in quadrature to loose-chi2 variance (debug only)",
    )

    ap.add_argument(
        "--use_rate_model",
        action="store_true",
        help="Compute signal baseline from bins.N_noosc or channel.rate_model instead of bins.N_sig_sm.",
    )

    ap.add_argument(
        "--use_rate_kernel",
        action="store_true",
        help="Compute pred_sm/pred_geo from an internal rate kernel (flux×sigma×eff×smear×exposure) using state-derived probabilities.",
    )

    ap.add_argument("--out", required=True)

    args = ap.parse_args()

    pack_path = Path(args.pack)
    with pack_path.open("r", encoding="utf-8") as f:
        pack = json.load(f)

    baseline_km = float(pack.get("meta", {}).get("baseline_km", 810.0))

    weak_alpha_Etilt = float(args.alpha) if args.weak_alpha_Etilt is None else float(args.weak_alpha_Etilt)

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
        kappa_gate=float(args.kappa_gate),
        T0=float(args.T0),
        mu=float(args.mu),
        eta=float(args.eta),
        k_rt=float(args.k_rt),
        k_rt_ref=180.0,
        kernel=str(args.kernel),
    )

    kp.thread_omega0_1_per_km = kp.breath_omega0_1_per_km if float(args.thread_w0) < 0 else float(args.thread_w0)

    if args.omega0_geom == "fixed" and (args.omega == 0.0):
        kp.omega_1_per_km = omega0_geom_fixed(kp.L0_km)

    A0_app, theta_app = _theta_for_amp_app(args.theta23_deg, args.theta13_deg)
    theta_dis = math.radians(float(args.theta23_deg))
    dm2_gksl = _dm2_gksl_from_runner(args.dm2_runner_eV2)

    print(f"omega0_geom [1/km] = {kp.omega_1_per_km}")
    print(f"GKSL base dm2 [eV^2] = {dm2_gksl:.6g}")

    rows: list[dict] = []
    totals: list[tuple[str, float, float, float]] = []

    for ch in pack["channels"]:
        name = ch["name"]
        ctype = ch["type"]
        L_km = float(ch.get("baseline_km", baseline_km))

        bins = ch["bins"]
        E_lo = np.asarray(bins["E_lo"], float)
        E_hi = np.asarray(bins["E_hi"], float)
        E_ctr = np.asarray(bins["E_ctr"], float)

        obs = np.asarray(bins["N_obs"], float)
        bkg_sm = np.asarray(bins["N_bkg_sm"], float)

        # When using the internal rate kernel, we will compute sig_sm from the kernel
        # after we compute P_sm/P_geo on the true-energy bins.
        sig_sm = None
        pred_sm = None
        if not args.use_rate_kernel:
            if args.use_rate_model:
                sig_sm = compute_sig_sm_from_pack_rate_model(channel=ch, E_lo=E_lo, E_hi=E_hi)
            else:
                sig_sm = np.asarray(bins["N_sig_sm"], float)
            pred_sm = sig_sm + bkg_sm

        # Bin shifts: preserve legacy behavior (shift signal/probability, not bkg).
        # Not applied in --use_rate_kernel mode (since rates are recomputed end-to-end).
        if not args.use_rate_kernel:
            if ctype == "appearance" and args.bin_shift_app != 0:
                sig_sm = shift_bins(sig_sm, args.bin_shift_app)
                pred_sm = sig_sm + bkg_sm

            if ctype == "disappearance" and args.bin_shift_dis != 0:
                sig_sm = shift_bins(sig_sm, args.bin_shift_dis)
                pred_sm = sig_sm + bkg_sm

        # Compute kernel phase components per bin (same as legacy).
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

        # GKSL probabilities per bin.
        P_sm = np.zeros_like(E_ctr, dtype=float)
        P_geo = np.zeros_like(E_ctr, dtype=float)

        # Optional per-bin telemetry (3-flavor only). Stored as arrays to write into CSV.
        tele_sm = {k: np.full_like(E_ctr, np.nan, dtype=float) for k in ["trace", "min_eig", "purity", "herm_err", "Pe", "Pmu", "Ptau"]}
        tele_geo = {k: np.full_like(E_ctr, np.nan, dtype=float) for k in ["trace", "min_eig", "purity", "herm_err", "Pe", "Pmu", "Ptau"]}

        for i, E in enumerate(E_ctr):
            if args.flavors == 2:
                theta = theta_app if ctype == "appearance" else theta_dis
                ug_sm = UnifiedGKSL(dm2_gksl, theta)
            else:
                nu_in, nu_out = _flavors_for_channel(ch, ctype)
                ug_sm = UnifiedGKSL3(
                    dm21=float(args.dm21_eV2),
                    dm31=float(args.dm31_eV2),
                    theta12=math.radians(float(args.theta12_deg)),
                    theta13=math.radians(float(args.theta13_deg)),
                    theta23=math.radians(float(args.theta23_deg)),
                    delta_cp=math.radians(float(args.delta_cp_deg)),
                    flavor_in=nu_in,
                )

            if args.use_matter and float(args.rho) != 0.0:
                Ve_eV = ve_from_rho(float(args.rho), float(args.Ye))
                V_km_inv = ve_to_H_km_inv(Ve_eV)

                if args.flavors == 2:
                    def Hmatter(_L: float, _E: float, V=V_km_inv):
                        return np.array([[V, 0.0], [0.0, 0.0]], dtype=complex)
                else:
                    def Hmatter(_L: float, _E: float, V=V_km_inv):
                        return np.array([[V, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=complex)

                ug_sm.add_flavor_sector(Hmatter)

            if args.gamma is not None or args.use_microphysics:
                if args.flavors == 2:
                    D = make_weak_damping_fn(
                        gamma=args.gamma,
                        use_microphysics=bool(args.use_microphysics),
                        n_cm3=args.n_cm3,
                        E_GeV_ref=float(args.E_GeV_ref),
                        channel=str(args.weak_channel),
                    )
                    ug_sm.add_damping(D)
                else:
                    gamma_val = _weak_gamma_value(
                        gamma=args.gamma,
                        use_microphysics=bool(args.use_microphysics),
                        n_cm3=args.n_cm3,
                        E_GeV_ref=float(args.E_GeV_ref),
                        channel=str(args.weak_channel),
                    )

                    def D(_L: float, _E: float, rho: np.ndarray, g=gamma_val):
                        return lindblad_dephasing_offdiag_3(rho, g)

                    ug_sm.add_damping(D)

            rho_sm = ug_sm.integrate(L_km, float(E), steps=int(args.steps))
            if args.flavors == 2:
                P_sm[i] = _prob_from_rho(rho_sm, channel_type=ctype)
            else:
                nu_in, nu_out = _flavors_for_channel(ch, ctype)
                P_sm[i] = float(np.real(rho_sm[_idx3(nu_out), _idx3(nu_out)]))
                t = _rho_telemetry_3(rho_sm)
                for k in tele_sm:
                    tele_sm[k][i] = t[k]

            # GEO: add mass-sector delta(dm2) corresponding to the desired dphi.
            delta_dm2 = _delta_dm2_gksl_from_dphi(float(dphi[i]), L_km=L_km, E_GeV=float(E))

            if args.flavors == 2:
                ug_geo = UnifiedGKSL(dm2_gksl, theta)
            else:
                nu_in, _ = _flavors_for_channel(ch, ctype)
                ug_geo = UnifiedGKSL3(
                    dm21=float(args.dm21_eV2),
                    dm31=float(args.dm31_eV2),
                    theta12=math.radians(float(args.theta12_deg)),
                    theta13=math.radians(float(args.theta13_deg)),
                    theta23=math.radians(float(args.theta23_deg)),
                    delta_cp=math.radians(float(args.delta_cp_deg)),
                    flavor_in=nu_in,
                )
            if args.use_matter and float(args.rho) != 0.0:
                ug_geo.add_flavor_sector(Hmatter)
            if args.gamma is not None or args.use_microphysics:
                ug_geo.add_damping(D)

            def extra_mass(_L: float, _E: float, ddm2=delta_dm2) -> np.ndarray:
                if args.flavors == 2:
                    return np.array([[0.0, 0.0], [0.0, float(ddm2)]], dtype=float)
                return np.diag([0.0, 0.0, float(ddm2)]).astype(float)

            ug_geo.add_mass_sector(extra_mass)
            rho_geo = ug_geo.integrate(L_km, float(E), steps=int(args.steps))
            if args.flavors == 2:
                P_geo[i] = _prob_from_rho(rho_geo, channel_type=ctype)
            else:
                _, nu_out = _flavors_for_channel(ch, ctype)
                P_geo[i] = float(np.real(rho_geo[_idx3(nu_out), _idx3(nu_out)]))
                t = _rho_telemetry_3(rho_geo)
                for k in tele_geo:
                    tele_geo[k][i] = t[k]

        P_sm = np.clip(P_sm, 0.0, 1.0)
        P_geo = np.clip(P_geo, 0.0, 1.0)

        if args.use_rate_kernel:
            rk = parse_rate_kernel(ch, reco_bin_count=len(E_ctr))
            if rk is None:
                raise ValueError("--use_rate_kernel requires channel.rate_kernel")

            # Evaluate probabilities on true-energy bins using the same internal dynamics.
            true_E_ctr = 0.5 * (rk.true_E_lo + rk.true_E_hi)
            P_sm_true = np.zeros_like(true_E_ctr, dtype=float)
            P_geo_true = np.zeros_like(true_E_ctr, dtype=float)

            # Recompute dphi on true-energy centers.
            comps_true = [kernel_phase_dphi_components(L_km, float(e), kp) for e in true_E_ctr]
            dphi_base_t = np.array([c[0] for c in comps_true], float)
            dphi_breath_t = np.array([c[1] for c in comps_true], float)
            dphi_thread_t = np.array([c[2] for c in comps_true], float)
            dphi_t = dphi_base_t + dphi_breath_t + w_thread * dphi_thread_t

            for j, Etrue in enumerate(true_E_ctr):
                # Build SM evolution object
                if args.flavors == 2:
                    theta = theta_app if ctype == "appearance" else theta_dis
                    ug_sm_t = UnifiedGKSL(dm2_gksl, theta)
                else:
                    nu_in, nu_out = _flavors_for_channel(ch, ctype)
                    ug_sm_t = UnifiedGKSL3(
                        dm21=float(args.dm21_eV2),
                        dm31=float(args.dm31_eV2),
                        theta12=math.radians(float(args.theta12_deg)),
                        theta13=math.radians(float(args.theta13_deg)),
                        theta23=math.radians(float(args.theta23_deg)),
                        delta_cp=math.radians(float(args.delta_cp_deg)),
                        flavor_in=nu_in,
                    )

                if args.use_matter and float(args.rho) != 0.0:
                    ug_sm_t.add_flavor_sector(Hmatter)
                if args.gamma is not None or args.use_microphysics:
                    ug_sm_t.add_damping(D)

                rho_sm_t = ug_sm_t.integrate(L_km, float(Etrue), steps=int(args.steps))
                if args.flavors == 2:
                    P_sm_true[j] = _prob_from_rho(rho_sm_t, channel_type=ctype)
                else:
                    _, nu_out = _flavors_for_channel(ch, ctype)
                    P_sm_true[j] = float(np.real(rho_sm_t[_idx3(nu_out), _idx3(nu_out)]))

                # Build GEO evolution with extra mass-sector delta
                delta_dm2 = _delta_dm2_gksl_from_dphi(float(dphi_t[j]), L_km=L_km, E_GeV=float(Etrue))
                if args.flavors == 2:
                    ug_geo_t = UnifiedGKSL(dm2_gksl, theta)
                else:
                    ug_geo_t = UnifiedGKSL3(
                        dm21=float(args.dm21_eV2),
                        dm31=float(args.dm31_eV2),
                        theta12=math.radians(float(args.theta12_deg)),
                        theta13=math.radians(float(args.theta13_deg)),
                        theta23=math.radians(float(args.theta23_deg)),
                        delta_cp=math.radians(float(args.delta_cp_deg)),
                        flavor_in=nu_in,
                    )
                if args.use_matter and float(args.rho) != 0.0:
                    ug_geo_t.add_flavor_sector(Hmatter)
                if args.gamma is not None or args.use_microphysics:
                    ug_geo_t.add_damping(D)

                def extra_mass(_L: float, _E: float, ddm2=delta_dm2) -> np.ndarray:
                    if args.flavors == 2:
                        return np.array([[0.0, 0.0], [0.0, float(ddm2)]], dtype=float)
                    return np.diag([0.0, 0.0, float(ddm2)]).astype(float)

                ug_geo_t.add_mass_sector(extra_mass)
                rho_geo_t = ug_geo_t.integrate(L_km, float(Etrue), steps=int(args.steps))
                if args.flavors == 2:
                    P_geo_true[j] = _prob_from_rho(rho_geo_t, channel_type=ctype)
                else:
                    P_geo_true[j] = float(np.real(rho_geo_t[_idx3(nu_out), _idx3(nu_out)]))

            P_sm_true = np.clip(P_sm_true, 0.0, 1.0)
            P_geo_true = np.clip(P_geo_true, 0.0, 1.0)

            # Compute reconstructed signal rates from internal kernel.
            sig_sm = compute_event_rates_rec(config=rk, P_true=P_sm_true)
            sig_geo = compute_event_rates_rec(config=rk, P_true=P_geo_true)

            pred_sm = sig_sm + bkg_sm
            pred_geo = sig_geo + bkg_sm
        else:
            # Pred geo: scale signal by ratio P_geo/P_sm, keep bkg fixed (legacy contract).
            ratio = safe_ratio(P_geo, P_sm, floor=1e-6)
            sig_geo = sig_sm * ratio
            pred_geo = sig_geo + bkg_sm

        if args.chi2_mode == "poisson_dev":
            if args.poisson_shape == "per_channel":
                s_sm = float(np.sum(np.maximum(obs, 0.0))) / float(np.sum(np.maximum(pred_sm, 1e-12)))
                s_geo = float(np.sum(np.maximum(obs, 0.0))) / float(np.sum(np.maximum(pred_geo, 1e-12)))
                chi2_sm = chi2_poisson_deviance(obs, pred_sm * s_sm)
                chi2_geo = chi2_poisson_deviance(obs, pred_geo * s_geo)
            elif args.poisson_shape == "per_channel_common":
                s = float(np.sum(np.maximum(obs, 0.0))) / float(np.sum(np.maximum(pred_sm, 1e-12)))
                chi2_sm = chi2_poisson_deviance(obs, pred_sm * s)
                chi2_geo = chi2_poisson_deviance(obs, pred_geo * s)
            else:
                chi2_sm = chi2_poisson_deviance(obs, pred_sm)
                chi2_geo = chi2_poisson_deviance(obs, pred_geo)
        else:
            chi2_sm = chi2_gauss_loose(obs, pred_sm, systfrac=args.systfrac, sigma_floor=args.sigma_floor)
            chi2_geo = chi2_gauss_loose(obs, pred_geo, systfrac=args.systfrac, sigma_floor=args.sigma_floor)
        dchi2 = chi2_sm - chi2_geo
        totals.append((name, chi2_sm, chi2_geo, dchi2))

        print(f"- {name:18s} type={ctype:12s} bins={len(obs):2d}  chi2_SM={chi2_sm:8.3f}  chi2_GEO={chi2_geo:8.3f}  dchi2={dchi2:8.3f}")

        for i in range(len(obs)):
            rows.append(
                {
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

                    # 3-flavor dynamics telemetry (NaN in 2-flavor mode)
                    "trace_rho_sm": float(tele_sm["trace"][i]),
                    "min_eig_rho_sm": float(tele_sm["min_eig"][i]),
                    "purity_rho_sm": float(tele_sm["purity"][i]),
                    "herm_err_rho_sm": float(tele_sm["herm_err"][i]),
                    "Pe_sm": float(tele_sm["Pe"][i]),
                    "Pmu_sm": float(tele_sm["Pmu"][i]),
                    "Ptau_sm": float(tele_sm["Ptau"][i]),

                    "trace_rho_geo": float(tele_geo["trace"][i]),
                    "min_eig_rho_geo": float(tele_geo["min_eig"][i]),
                    "purity_rho_geo": float(tele_geo["purity"][i]),
                    "herm_err_rho_geo": float(tele_geo["herm_err"][i]),
                    "Pe_geo": float(tele_geo["Pe"][i]),
                    "Pmu_geo": float(tele_geo["Pmu"][i]),
                    "Ptau_geo": float(tele_geo["Ptau"][i]),
                }
            )

    tot_sm = sum(x[1] for x in totals)
    tot_geo = sum(x[2] for x in totals)
    tot_d = tot_sm - tot_geo

    print("\n------------------------")
    print(f"TOTAL chi2_SM  = {tot_sm:.3f}")
    print(f"TOTAL chi2_GEO = {tot_geo:.3f}")
    print(f"Delta chi2 = chi2_SM - chi2_GEO = {tot_d:.3f}")
    print("------------------------\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
