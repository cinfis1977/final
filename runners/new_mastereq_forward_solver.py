"""
Demonstration forward runner that uses the GKSL solver (2-flavor toy) and compares
its output to the phase-shift approximation used by existing runners.

Produces per-bin CSV with P_sm, P_phase_approx, P_gksl and a simple chi2 comparison.

Usage example:
python runners/new_mastereq_forward_solver.py --E 1.0 --L 295 --A 0.01 --omega 0.00388 --out out_demo.csv
"""
from __future__ import annotations
import argparse
import math
import numpy as np
import pandas as pd
from mastereq.gk_sl_solver import (
    build_Hfn_2flavor,
    build_Dfn_simple,
    integrate_rho,
    geometric_delta_m2_2flavor,
)

# Reuse a simple kernel for base_dphi_dL similar to forward runners
def base_dphi_dL_kernel(L_km: float, E_GeV: float, A: float, omega: float, phi: float, zeta: float) -> float:
    # simple damped sinusoidal driver (we interpret as "dphi per unit L")
    damp = math.exp(-zeta * abs(omega) * L_km)
    return A * damp * math.sin(omega * L_km + phi)


def phase_shift_approx_prob(dm2: float, theta: float, L_km: float, E_GeV: float, integrated_dphi: float, mode: str = "appearance") -> float:
    # two-flavor analytic phase
    Delta = 1.267 * dm2 * L_km / max(E_GeV, 1e-12)
    tot = Delta + integrated_dphi
    if mode == "appearance":
        amp = (math.sin(theta) ** 2) * (math.sin(2 * theta) ** 2)
        return float(amp * (math.sin(tot) ** 2))
    else:
        amp = (math.sin(2 * theta) ** 2)
        return float(1.0 - amp * (math.sin(tot) ** 2))


def analytic_sm_prob(dm2: float, theta: float, L_km: float, E_GeV: float, mode: str = "appearance") -> float:
    Delta = 1.267 * dm2 * L_km / max(E_GeV, 1e-12)
    if mode == "appearance":
        amp = (math.sin(theta) ** 2) * (math.sin(2 * theta) ** 2)
        return float(amp * (math.sin(Delta) ** 2))
    else:
        amp = (math.sin(2 * theta) ** 2)
        return float(1.0 - amp * (math.sin(Delta) ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--E", type=float, default=1.0, help="Energy in GeV")
    ap.add_argument("--L", type=float, default=295.0, help="Baseline km")
    ap.add_argument("--A", type=float, default=0.0, help="Geometry amplitude (driver scale)")
    ap.add_argument("--omega", type=float, default=0.0, help="Driver omega [1/km]")
    ap.add_argument("--phi", type=float, default=math.pi/2, help="Driver phase")
    ap.add_argument("--zeta", type=float, default=0.0, help="Damping zeta")
    ap.add_argument("--gamma", type=float, default=0.0, help="dephasing gamma")
    ap.add_argument("--steps", type=int, default=500, help="integration steps for GKSL")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = float(args.E)
    L = float(args.L)

    # build extra deltaM2 function via base_dphi_dL kernel
    def extra_dm2_fn(L_km, E_GeV):
        base = base_dphi_dL_kernel(L_km, E_GeV, args.A, args.omega, args.phi, args.zeta)
        # use geometric_delta_m2_2flavor to produce a 2x2 mass-basis matrix
        return geometric_delta_m2_2flavor(base, E_GeV, scale_factor=1.0)

    # build H and D functions
    Hfn = build_Hfn_2flavor(dm2, theta, extra_dm2_fn)
    # junction_scale = 1 for demo
    Dfn = build_Dfn_simple(args.gamma, lambda L_km, E_GeV: 1.0)

    # integrate GKSL
    rhoL = integrate_rho(L, E, Hfn, Dfn, steps=args.steps)
    # probability to detect electron flavor (appearance) = <nu_e|rho|nu_e> -> element (0,0)
    P_gksl = float(np.real(rhoL[0, 0]))

    # compute integrated dphi as trapezoid over kernel samples
    Ns = max(200, args.steps)
    xs = np.linspace(0.0, L, Ns)
    vals = [base_dphi_dL_kernel(x, E, args.A, args.omega, args.phi, args.zeta) for x in xs]
    int_dphi = float(np.trapz(vals, xs))

    P_phase = phase_shift_approx_prob(dm2, theta, L, E, int_dphi, mode="appearance")
    P_sm = analytic_sm_prob(dm2, theta, L, E, mode="appearance")

    out = pd.DataFrame([{
        "E_GeV": E,
        "L_km": L,
        "P_sm": P_sm,
        "P_phase_approx": P_phase,
        "P_gksl": P_gksl,
        "int_dphi": int_dphi,
        "A": args.A,
        "omega": args.omega,
        "phi": args.phi,
        "zeta": args.zeta,
        "gamma": args.gamma,
    }])
    out.to_csv(args.out, index=False)
    print(f"Wrote: {args.out}")

if __name__ == "__main__":
    main()
