#!/usr/bin/env python
# dm_holdout_cv_thread.py
#
# Drop-in replacement for dm_holdout_cv.py with Phase-2A thread-network env_model support.
# Galaxy-holdout k-fold CV: split by galaxy id/name, not by points.
#
# Outputs a CSV compatible with your existing analyze scripts (keeps core columns).

from __future__ import annotations
import argparse, os
import numpy as np
import pandas as pd

from dm_thread_env_dropin_STIFFGATE import (
    build_env_vector, extract_g_bar, extract_g_obs, extract_sigma_log10g,
    calibrate_thread_gate_from_galaxy,
)


def chi2_log10g(g_pred: np.ndarray, g_obs: np.ndarray, sigma_log10g: Optional[np.ndarray]) -> float:
    g_pred = np.maximum(g_pred, 1e-30)
    g_obs  = np.maximum(g_obs,  1e-30)
    r = np.log10(g_pred) - np.log10(g_obs)
    if sigma_log10g is None:
        return float(np.sum(r*r))
    w = np.where(np.isfinite(sigma_log10g) & (sigma_log10g > 0), 1.0/(sigma_log10g**2), 0.0)
    return float(np.sum(w * (r*r)))

def geo_add_const(g_bar: np.ndarray, *, A: float, alpha: float, g0: float, env_vec: np.ndarray) -> np.ndarray:
    Aeff = A * env_vec
    g_geo = Aeff * g0 * np.power(g0 / (g_bar + g0), alpha)
    return g_bar + g_geo

def make_grid(A_min, A_max, nA, alpha_min, alpha_max, nAlpha):
    A_grid = np.logspace(np.log10(A_min), np.log10(A_max), int(nA))
    alpha_grid = np.linspace(alpha_min, alpha_max, int(nAlpha))
    return A_grid, alpha_grid

def get_galaxy_col(df: pd.DataFrame) -> str:
    for c in ["galaxy", "galaxy_id", "gal", "name", "gal_name", "SPARC_galaxy"]:
        if c in df.columns:
            return c
    # fallback: any column that looks like galaxy id
    for c in df.columns:
        if "gal" in c.lower():
            return c
    raise RuntimeError(f"Could not find a galaxy identifier column. Columns={list(df.columns)}")

def make_galaxy_folds(galaxies: np.ndarray, kfold: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(int(seed))
    gal = np.array(sorted(set(galaxies.tolist())))
    rng.shuffle(gal)
    folds = np.array_split(gal, int(kfold))
    return folds

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--points_csv", required=True)
    ap.add_argument("--model", default="geo_add_const", choices=["geo_add_const"])
    ap.add_argument("--g0", type=float, default=1.2e-10)

    # legacy flags
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--use_env_scale", action="store_true")
    g.add_argument("--no_env_scale", action="store_true")

    ap.add_argument("--env_model", choices=["legacy","none","global","thread","global_thread"], default="legacy")
    ap.add_argument("--thread_mode", choices=["down","up"], default="down")
    ap.add_argument("--thread_q", type=float, default=0.6)
    ap.add_argument("--thread_xi", type=float, default=0.5)
    ap.add_argument("--thread_norm", choices=["median","mean","none"], default="median")
    ap.add_argument("--thread_r_weight_power", type=float, default=1.0)

    # Optional non-linear "real spring" activation gate (decouple in mild env; turn on in strong stress)
    ap.add_argument("--thread_S0", type=float, default=None)
    ap.add_argument("--thread_gate_p", type=float, default=4.0)
    ap.add_argument("--thread_k2", type=float, default=1.0)
    ap.add_argument("--thread_k4", type=float, default=0.0)
    ap.add_argument("--thread_calibrate_from_galaxy", action="store_true",
                    help="Auto-calibrate (thread_S0, thread_k4) on TRAIN fold so gate is ~0 in galaxy regime")
    ap.add_argument("--gal_hi_p", type=float, default=99.9,
                    help="Percentile of stress proxy used as galaxy high-stress reference (default: 99.9)")
    ap.add_argument("--gal_gate_eps", type=float, default=1e-6,
                    help="Target gate value at S_hi for 'galaxy-closed' regime (default: 1e-6)")
    ap.add_argument("--thread_Sc_factor", type=float, default=10.0,
                    help="Sc = factor * S_hi controls quartic onset (default: 10)")

    ap.add_argument("--A_min", type=float, required=True)
    ap.add_argument("--A_max", type=float, required=True)
    ap.add_argument("--nA", type=int, default=81)
    ap.add_argument("--alpha_min", type=float, required=True)
    ap.add_argument("--alpha_max", type=float, required=True)
    ap.add_argument("--nAlpha", type=int, default=21)

    ap.add_argument("--kfold", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out_csv", required=True)

    args = ap.parse_args()

    df = pd.read_csv(args.points_csv)
    gal_col = get_galaxy_col(df)
    galaxies = df[gal_col].astype(str).to_numpy()

    folds = make_galaxy_folds(galaxies, args.kfold, args.seed)

    A_grid, alpha_grid = make_grid(args.A_min, args.A_max, args.nA, args.alpha_min, args.alpha_max, args.nAlpha)

    use_env = True if args.use_env_scale else False if args.no_env_scale else None

    rows = []
    for i, test_gals in enumerate(folds):
        mask_test = df[gal_col].astype(str).isin(set(test_gals.tolist()))
        df_test = df[mask_test].copy()
        df_train = df[~mask_test].copy()

        # Optional: auto-calibrate the nonlinear thread gate on TRAIN (then reuse on TEST)
        thread_S0_use = args.thread_S0
        thread_k4_use = args.thread_k4
        if args.env_model in ("thread", "global_thread") and args.thread_calibrate_from_galaxy:
            calib = calibrate_thread_gate_from_galaxy(
                df_train,
                g0=args.g0,
                thread_mode=args.thread_mode,
                thread_q=args.thread_q,
                thread_xi=args.thread_xi,
                thread_r_weight_power=args.thread_r_weight_power,
                gate_p=args.thread_gate_p,
                k2=args.thread_k2,
                gal_hi_p=args.gal_hi_p,
                gal_gate_eps=args.gal_gate_eps,
                Sc_factor=args.thread_Sc_factor,
            )
            thread_S0_use = float(calib["S0"])
            thread_k4_use = float(calib["k4"])
            print(
                f"[FOLD {i}] [THREAD-CALIB] S_hi={calib['S_hi']:.6g} Sc={calib['Sc']:.6g} "
                f"S0={thread_S0_use:.6g} k4={thread_k4_use:.6g} gate(S_hi)={calib['gate_at_Shi']:.2e}"
            )


        # CV-safe: learn thread norm on TRAIN, apply to TEST
        env_train, norm_scale = build_env_vector(
            df_train,
            env_model=args.env_model,
            use_env_scale_flag=use_env,
            g0=args.g0,
            thread_mode=args.thread_mode,
            thread_q=args.thread_q,
            thread_xi=args.thread_xi,
            thread_norm=args.thread_norm,
            thread_r_weight_power=args.thread_r_weight_power,
            thread_S0=thread_S0_use,
            thread_gate_p=args.thread_gate_p,
            thread_k2=args.thread_k2,
            thread_k4=thread_k4_use,
            norm_scale_ref=None,
        )
        env_test, _ = build_env_vector(
            df_test,
            env_model=args.env_model,
            use_env_scale_flag=use_env,
            g0=args.g0,
            thread_mode=args.thread_mode,
            thread_q=args.thread_q,
            thread_xi=args.thread_xi,
            thread_norm=args.thread_norm,
            thread_r_weight_power=args.thread_r_weight_power,
            thread_S0=thread_S0_use,
            thread_gate_p=args.thread_gate_p,
            thread_k2=args.thread_k2,
            thread_k4=thread_k4_use,
            norm_scale_ref=norm_scale,
        )

        gbar_train = extract_g_bar(df_train)
        gobs_train = extract_g_obs(df_train)
        sig_train = extract_sigma_log10g(df_train)

        gbar_test = extract_g_bar(df_test)
        gobs_test = extract_g_obs(df_test)
        sig_test = extract_sigma_log10g(df_test)

        chi2_train_base = chi2_log10g(gbar_train, gobs_train, sig_train)

        bestA, bestAlpha, bestChi2 = None, None, np.inf
        for alpha in alpha_grid:
            for A in A_grid:
                gpred = geo_add_const(gbar_train, A=float(A), alpha=float(alpha), g0=args.g0, env_vec=env_train)
                chi2 = chi2_log10g(gpred, gobs_train, sig_train)
                if chi2 < bestChi2:
                    bestChi2 = chi2
                    bestA = float(A)
                    bestAlpha = float(alpha)

        chi2_train_best = float(bestChi2)
        delta_train = float(chi2_train_base - chi2_train_best)

        chi2_test_base = chi2_log10g(gbar_test, gobs_test, sig_test)
        gpred_test = geo_add_const(gbar_test, A=bestA, alpha=bestAlpha, g0=args.g0, env_vec=env_test)
        chi2_test_best = chi2_log10g(gpred_test, gobs_test, sig_test)
        delta_test = float(chi2_test_base - chi2_test_best)

        print(f"[FOLD {i}] train Δχ²={delta_train:.3f}  test Δχ²={delta_test:.3f}  (A={bestA}, alpha={bestAlpha})")

        rows.append({
            "fold": i,
            "n_train_points": int(len(df_train)),
            "n_test_points": int(len(df_test)),
            "n_test_galaxies": int(len(set(test_gals.tolist()))),
            "A_best": bestA,
            "alpha_best": bestAlpha,
            "chi2_train_base": float(chi2_train_base),
            "chi2_train_best": float(chi2_train_best),
            "delta_chi2_train": float(delta_train),
            "chi2_test_base": float(chi2_test_base),
            "chi2_test_best": float(chi2_test_best),
            "delta_chi2_test": float(delta_test),
            "use_env_scale": 1 if (args.env_model=="legacy" and args.use_env_scale) else 0 if (args.env_model=="legacy" and args.no_env_scale) else None,
            "env_model": args.env_model,
            "thread_mode": args.thread_mode,
            "thread_q": args.thread_q,
            "thread_xi": args.thread_xi,
            "thread_norm": args.thread_norm,
            "thread_r_weight_power": args.thread_r_weight_power,
            "thread_S0": args.thread_S0,
            "thread_gate_p": args.thread_gate_p,
            "thread_k2": args.thread_k2,
            "thread_k4": args.thread_k4,
        })

    out_df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True) if os.path.dirname(args.out_csv) else None
    out_df.to_csv(args.out_csv, index=False)
    print(f"[OUT] {args.out_csv}")

if __name__ == "__main__":
    main()