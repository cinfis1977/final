"""Clean demo runner that uses the UnifiedGKSL API and weak-sector helper.

Writes a single-row CSV with P_sm (vacuum analytic) and P_unified (full GKSL result).
This is a safe, standalone script placed in `integration_artifacts/runners/`.
"""
from __future__ import annotations
import math
import argparse
import numpy as np
import pandas as pd

from mastereq.unified_gksl import UnifiedGKSL
from mastereq.weak_sector import make_weak_flavor_H_fn, make_weak_damping_fn


def analytic_sm_prob(dm2: float, theta: float, L_km: float, E_GeV: float) -> float:
    Delta = 1.267 * dm2 * L_km / max(E_GeV, 1e-12) / 4.0
    amp = math.sin(2 * theta) ** 2
    return float(amp * (math.sin(Delta) ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--E", type=float, default=1.0)
    ap.add_argument("--L", type=float, default=295.0)
    ap.add_argument("--ne", type=float, default=1e20, help="electron density (cm^-3)")
    ap.add_argument("--gamma", type=float, default=0.0, help="weak-sector dephasing")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = float(args.E)
    L = float(args.L)

    ug = UnifiedGKSL(dm2, theta)
    # add weak flavor potential and optional damping
    ug.add_flavor_sector(make_weak_flavor_H_fn(ne_cm3=args.ne, scale=1.0))
    if args.gamma and args.gamma > 0.0:
        ug.add_damping(make_weak_damping_fn(gamma=float(args.gamma)))

    rho = ug.integrate(L, E, steps=400)
    P_unified = float(np.real(rho[0, 0]))
    P_sm = analytic_sm_prob(dm2, theta, L, E)

    out = pd.DataFrame([{
        "E_GeV": E,
        "L_km": L,
        "P_sm": P_sm,
        "P_unified": P_unified,
        "ne_cm3": args.ne,
        "gamma": args.gamma,
    }])
    out.to_csv(args.out, index=False)
    print(f"Wrote: {args.out}")


if __name__ == "__main__":
    main()
