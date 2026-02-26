#!/usr/bin/env python3
# prereg_birefringence_accumulation_v1_DROPIN.py
# No-fit prereg accumulation check across redshift:
#   beta(z) = C_beta * I(z)
# with I(z) a LOCKED FRW integral: I(z)=âˆ«_0^z dz'/((1+z')*E(z'))
#
# Calibration locks C_beta from a high-z dataset (e.g., CMB at z=1100).
# Holdout tests a lower-z dataset (e.g., z~2-3 sources).
#
# This is a consistency/falsification check of a locked scaling.

import argparse
import csv
import math
import os


def E(z: float, Om: float, Ol: float, Or: float) -> float:
    return math.sqrt(Or * (1.0 + z) ** 4 + Om * (1.0 + z) ** 3 + Ol)


def I_frw(z: float, Om: float, Ol: float, Or: float, n_steps: int = 20000) -> float:
    """Dimensionless integral: I(z)=âˆ« dz/((1+z)E(z)). Simpson rule."""
    if z <= 0.0:
        return 0.0
    n = max(200, int(n_steps))
    # Simpson needs even n
    if n % 2 == 1:
        n += 1
    a = 0.0
    b = float(z)
    h = (b - a) / n
    s = 0.0
    for i in range(n + 1):
        zz = a + i * h
        denom = (1.0 + zz) * E(zz, Om, Ol, Or)
        term = 1.0 / denom
        if i == 0 or i == n:
            w = 1.0
        elif i % 2 == 1:
            w = 4.0
        else:
            w = 2.0
        s += w * term
    return s * h / 3.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z_cal", type=float, default=1100.0)
    ap.add_argument("--beta_cal_deg", type=float, required=True)
    ap.add_argument("--sigma_cal_deg", type=float, required=True)
    ap.add_argument("--label_cal", type=str, default="CMB")

    ap.add_argument("--z_hold", type=float, required=True)
    ap.add_argument("--beta_hold_deg", type=float, required=True)
    ap.add_argument("--sigma_hold_deg", type=float, required=True)
    ap.add_argument("--label_hold", type=str, default="LOWZ")

    ap.add_argument("--Om", type=float, default=0.315)
    ap.add_argument("--Ol", type=float, default=0.685)
    ap.add_argument("--Or", type=float, default=0.0)

    ap.add_argument("--k_sigma", type=float, default=2.0)
    ap.add_argument("--abs_test", action="store_true",
                    help="Use |beta| instead of signed beta (useful if sign conventions differ).")

    ap.add_argument("--out_csv", type=str, default="out/birefringence_accumulation_prereg_v1.csv")
    args = ap.parse_args()

    I_cal = I_frw(args.z_cal, args.Om, args.Ol, args.Or)
    I_hold = I_frw(args.z_hold, args.Om, args.Ol, args.Or)
    if I_cal <= 0.0:
        raise SystemExit("I(z_cal) <= 0; check inputs.")

    beta_cal = float(args.beta_cal_deg)
    sig_cal = float(args.sigma_cal_deg)
    C_beta = beta_cal / I_cal  # locked

    beta_pred = C_beta * I_hold
    beta_hold = float(args.beta_hold_deg)
    sig_hold = float(args.sigma_hold_deg)

    if args.abs_test:
        diff = abs(beta_hold) - abs(beta_pred)
        metric_str = "abs(|beta|)"
    else:
        diff = beta_hold - beta_pred
        metric_str = "signed(beta)"

    sig = math.sqrt(sig_cal ** 2 + sig_hold ** 2)
    zscore = diff / sig if sig > 0.0 else float("inf")
    verdict = "PASS" if abs(zscore) <= float(args.k_sigma) else "FAIL"

    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    row = {
        "cal_label": args.label_cal,
        "hold_label": args.label_hold,
        "z_cal": args.z_cal,
        "z_hold": args.z_hold,
        "Om": args.Om,
        "Ol": args.Ol,
        "Or": args.Or,
        "I_cal": I_cal,
        "I_hold": I_hold,
        "beta_cal_deg": beta_cal,
        "sigma_cal_deg": sig_cal,
        "C_beta_locked_per_I": C_beta,
        "beta_pred_hold_deg": beta_pred,
        "beta_hold_deg": beta_hold,
        "sigma_hold_deg": sig_hold,
        "abs_test": int(bool(args.abs_test)),
        "metric": metric_str,
        "diff_deg": diff,
        "sigma_comb_deg": sig,
        "z_score": zscore,
        "k_sigma": args.k_sigma,
        "verdict": verdict,
    }
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        w.writeheader()
        w.writerow(row)

    print("=== BIREFRINGENCE ACCUMULATION PREREG (NO FIT) ===")
    print(f"LOCK: I(z)=âˆ« dz/((1+z)E(z))  with Om={args.Om} Ol={args.Ol} Or={args.Or}")
    print(f"I_cal(z={args.z_cal})   = {I_cal:.10g}")
    print(f"I_hold(z={args.z_hold}) = {I_hold:.10g}")
    print("")
    print(f"cal  : {args.label_cal} beta={beta_cal} +/- {sig_cal} deg  => C_beta=beta/I_cal={C_beta:.10g}")
    print(f"pred : beta_pred(z_hold) = C_beta * I_hold = {beta_pred:.10g} deg")
    print(f"hold : {args.label_hold} beta={beta_hold} +/- {sig_hold} deg")
    print(f"metric: {metric_str}")
    print(f"diff  : {diff:.10g} deg")
    print(f"sigma : {sig:.10g} deg")
    print(f"z     : {zscore:.10g}")
    print(f"RULE  : PASS if |z| <= {args.k_sigma}")
    print(f"VERDICT={verdict}")
    print(f"OUT_CSV={args.out_csv}")


if __name__ == "__main__":
    main()

