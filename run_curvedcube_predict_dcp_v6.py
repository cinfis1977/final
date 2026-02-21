#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CurvedCube: predict delta_CP from geometry (no scan), then evaluate MINOS + NOvA spectral chi2
at that predicted delta_CP, and read T2K profile Δχ² at that same delta_CP.

Key features:
- NO/IO ordering controls which T2K profile is selected (NH vs IH) unless --dcp_key is provided.
- --t2k_rc selects wRC vs woRC (T2K profile variant) unless --dcp_key is provided.
- Reports three metrics together to avoid sign/interpretation confusion:
    SUM      = dchi2_MINOS + dchi2_NOVA
    PLUS_PEN = SUM + T2K_dchi2(delta_geo)   (chi2-like; lower better)
    SCORE    = SUM - T2K_dchi2(delta_geo)   (net-score; higher better)
"""
import argparse, json, math, os, subprocess, sys
from typing import Dict, Any, Tuple

def _wrap_pi(x: float) -> float:
    """Wrap to [-pi, pi]."""
    x = (x + math.pi) % (2*math.pi) - math.pi
    return x

def _interp_profile_dchi2(delta: float, centers, dchi2) -> float:
    """Linear interpolation of profile Δχ² vs centers. centers assumed monotonic."""
    if len(centers) != len(dchi2) or len(centers) < 2:
        raise ValueError("profile arrays malformed")
    # ensure wrap consistent with centers range (-pi,pi) typical; do a wrap to nearest
    delta = _wrap_pi(delta)
    # clamp
    if delta <= centers[0]:
        return float(dchi2[0])
    if delta >= centers[-1]:
        return float(dchi2[-1])
    # binary search
    lo, hi = 0, len(centers)-1
    while hi - lo > 1:
        mid = (lo + hi)//2
        if centers[mid] <= delta:
            lo = mid
        else:
            hi = mid
    x0, x1 = float(centers[lo]), float(centers[hi])
    y0, y1 = float(dchi2[lo]), float(dchi2[hi])
    t = (delta - x0) / (x1 - x0)
    return y0 + t*(y1 - y0)

def _load_profiles(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    # tolerate either {"profiles": {...}} or flat dict
    if isinstance(j, dict) and "profiles" in j and isinstance(j["profiles"], dict):
        return j["profiles"]
    if isinstance(j, dict):
        return j
    raise ValueError("profiles json must be a dict")

def _pick_t2k_key(ordering: str, t2k_rc: str) -> str:
    ordering = ordering.upper()
    hier = "NH" if ordering == "NO" else "IH"
    t2k_rc = t2k_rc
    return f"h1D_dCPchi2_{t2k_rc}_{hier}"

def _run_runner(runner: str, pack: str, delta_cp: float, args: argparse.Namespace) -> Tuple[float, float, float]:
    """
    Calls the runner twice: once with geo off (SM), once with geo on (GEO), at a fixed delta_cp.
    Returns (chi2_sm, chi2_geo, dchi2=chi2_sm-chi2_geo?) -> We follow existing convention:
        dchi2 = chi2_SM - chi2_GEO?  No: your outputs elsewhere used dchi2 = chi2_SM - chi2_GEO?? Actually logs show dchi2 = chi2_SM(BF) - chi2_GEO(geo) negative when GEO worse.
    We'll compute dchi2 = chi2_SM - chi2_GEO so positive means GEO improves.
    """
    base = [
        sys.executable, runner,
        "--pack", pack,
        "--kernel", "rt",
        "--k_rt", str(args.k_rt),
        "--A", str(args.A),
        "--alpha", "0.7",
        "--n", str(args.n),
        "--E0", str(args.E0),
        "--omega0_geom", "fixed",
        "--phi", str(args.phi),
        "--zeta", str(args.zeta),
        "--kappa_gate", str(args.kappa_gate),
        "--geo_action", args.geo_action,
        "--fullphys_op", args.fullphys_op,
        "--fullphys_scale", args.fullphys_scale,
        "--delta_cp", str(delta_cp),
        "--pull_sig", str(args.pull_sig),
        "--pull_bkg", str(args.pull_bkg),
    ]

    # SM: force gate=0 and A=0 effectively turns off; but keep consistent: easiest is kappa_gate=0
    sm = base.copy()
    # turn off geometric contribution
    sm[sm.index("--kappa_gate")+1] = "0"
    # keep A as-is? for safety set to 0
    sm[sm.index("--A")+1] = "0"

    geo = base.copy()

    def _call(cmd):
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            # Some runners in this repo do not support optional "--quiet". Retry once without it.
            err = (p.stderr or "") + "\n" + (p.stdout or "")

            if ("--quiet" in cmd) and ("unrecognized arguments: --quiet" in err):
                cmd2 = [c for c in cmd if c != "--quiet"]
                p2 = subprocess.run(cmd2, capture_output=True, text=True)
                if p2.returncode != 0:
                    raise RuntimeError(p2.stderr.strip() or p2.stdout.strip() or f"runner failed: {cmd2}")
                p = p2
            else:
                raise RuntimeError(p.stderr.strip() or p.stdout.strip() or f"runner failed: {cmd}")
        # runner prints a summary line containing "chi2_total=" in our project runners; fallback:ck: search "chi2=".
        out = p.stdout.splitlines()
        chi2 = None
        for line in reversed(out):
            if "chi2_total" in line:
                try:
                    chi2 = float(line.split("chi2_total=")[-1].strip().split()[0])
                    break
                except Exception:
                    pass
            if "chi2=" in line and chi2 is None:
                # last-resort
                try:
                    chi2 = float(line.split("chi2=")[-1].strip().split()[0])
                    break
                except Exception:
                    pass
        if chi2 is None:
            raise RuntimeError("Could not parse chi2 from runner output")
        return chi2

    chi2_sm = _call(sm)
    chi2_geo = _call(geo)
    dchi2 = chi2_sm - chi2_geo
    return chi2_sm, chi2_geo, dchi2

def _predict_delta_cp_geo(args: argparse.Namespace) -> float:
    """
    Uses weak_prob_engine_LAYERED_CURVED_v1.py helper (already in project) to compute a geometry-derived phase.
    We import dynamically so this script stays lightweight.
    """
    from weak_prob_engine_LAYERED_CURVED_v1 import _curvedcube_u_profile
    import numpy as np

    # generate u(s) samples along the baseline (normalized s in [0,1])
    N = int(args.k_rt)
    L0 = float(args.L0_km)
    baseline = float(args.baseline_km)

    # Call u-profile with signature-aware kwargs (engine versions differ in parameter names).
    import inspect
    phi = float(args.phi)
    zeta = float(args.zeta)
    Nin = int(args.Nin)
    Nface = int(args.Nface)
    sig = inspect.signature(_curvedcube_u_profile)
    params = sig.parameters
    kwargs = {}
    # Baseline / reference-length parameters
    if 'L_km' in params: kwargs['L_km'] = baseline
    if 'baseline_km' in params: kwargs['baseline_km'] = baseline
    if 'L0_km' in params: kwargs['L0_km'] = L0
    if 'phi' in params: kwargs['phi'] = phi
    if 'zeta' in params: kwargs['zeta'] = zeta
    # Geometry thread-count parameters
    if 'Nin' in params: kwargs['Nin'] = Nin
    if 'Nface' in params: kwargs['Nface'] = Nface
    if 'N_in' in params: kwargs['N_in'] = Nin
    if 'N_face' in params: kwargs['N_face'] = Nface
    try:
        u = _curvedcube_u_profile(N, **kwargs)
    except TypeError:
        # Fallback: common positional conventions (kept deterministic).
        try:
            u = _curvedcube_u_profile(N, baseline, L0, phi, zeta)
        except TypeError:
            u = _curvedcube_u_profile(N, L0, baseline, phi, zeta)
    u = np.asarray(u, dtype=float)

    # Use mode to derive complex "holonomy-like" phasor
    if args.geo_dcp_mode == "u_phase":
        a = u
    elif args.geo_dcp_mode == "du_phase":
        # discrete derivative along s
        a = np.gradient(u)
    else:
        raise ValueError("unknown geo_dcp_mode")

    # oriented first-harmonic projection as a Wilson-loop proxy
    theta = 2.0 * math.pi * (np.arange(N, dtype=float) / float(N))
    phasor = np.sum(a * np.exp(1j * theta))
    delta = float(np.angle(phasor))
    return _wrap_pi(delta)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", default="weak_real_spectral_forward_pois_pull_LAYERED_CURVED_v1.py")
    ap.add_argument("--profiles", default="t2k_frequentist_profiles_FIXED.json")
    ap.add_argument("--dcp_key", default="", help="Override T2K profile key; if set, --ordering/--t2k_rc won't change it.")
    ap.add_argument("--t2k_rc", choices=["wRC", "woRC"], default="wRC", help="T2K profile variant (used only if --dcp_key not set).")

    ap.add_argument("--minos_pack", default="minos_channels.json")
    ap.add_argument("--nova_pack", default="nova_channels_FROM_RELEASE_CSV.json")

    ap.add_argument("--ordering", choices=["NO", "IO"], default="NO")

    ap.add_argument("--phi", type=float, default=1.57079632679)
    ap.add_argument("--zeta", type=float, default=0.05)
    ap.add_argument("--k_rt", type=int, default=180)
    ap.add_argument("--A", type=float, default=1e-3)
    ap.add_argument("--n", type=float, default=0.0)
    ap.add_argument("--E0", type=float, default=1.0)
    ap.add_argument("--kappa_gate", type=int, default=1)

    ap.add_argument("--geo_action", default="curved_cube")
    ap.add_argument("--fullphys_op", default="emu")
    ap.add_argument("--fullphys_scale", default="dm31")

    ap.add_argument("--Nin", type=int, default=8)
    ap.add_argument("--Nface", type=int, default=16)

    ap.add_argument("--geo_dcp_mode", choices=["u_phase", "du_phase"], default="du_phase")

    ap.add_argument("--pull_sig", type=float, default=0.0)
    ap.add_argument("--pull_bkg", type=float, default=0.0)

    ap.add_argument("--no_profile", action="store_true", help="Skip T2K profile lookup entirely.")
    ap.add_argument("--L0_km", type=float, default=295.0, help="Reference baseline for geometric omega scaling in engine (kept for compatibility).")
    ap.add_argument("--baseline_km", type=float, default=295.0, help="Baseline used for u-profile sampling in delta prediction.")

    args = ap.parse_args()

    print("\n==== CURVEDCUBE: PREDICT delta_CP from geometry (no scan) ====\n")

    profiles = _load_profiles(args.profiles)

    if args.dcp_key.strip():
        key = args.dcp_key.strip()
    else:
        key = _pick_t2k_key(args.ordering, args.t2k_rc)

    if (not args.no_profile) and key not in profiles:
        raise SystemExit(f"ERROR: T2K profile key not found: {key}")

    print(f"T2K profile key : {key}")

    # T2K BF delta, only meaningful for display
    if not args.no_profile:
        centers = profiles[key]["centers"]
        dchi2 = profiles[key]["dchi2"]
        # BF is argmin dchi2
        i0 = min(range(len(dchi2)), key=lambda i: dchi2[i])
        dcp_bf = float(centers[i0])
        print(f"T2K BF delta_CP : {dcp_bf:+.6f} rad")
    else:
        dcp_bf = float("nan")
        print("T2K BF delta_CP : (skipped; --no_profile)")

    # predict delta_cp from geometry (independent of ordering by design)
    dcp_geo = _predict_delta_cp_geo(args)
    print(f"delta_CP^geo    : {dcp_geo:+.6f} rad  (mode={args.geo_dcp_mode}, k_rt={args.k_rt}, phi={args.phi}, zeta={args.zeta})")

    if not args.no_profile:
        t2k_pen = _interp_profile_dchi2(dcp_geo, centers, dchi2)
        print(f"T2K dchi2 at geo: {t2k_pen:.6f}")
    else:
        t2k_pen = 0.0
        print("T2K dchi2 at geo: (skipped; --no_profile)")

    print("\n---- RESULTS (single-shot, predicted delta_CP) ----")

    # Evaluate MINOS/NOvA runners at delta_cp=geo
    # Note: runner pack baseline differences already inside pack; we just call at delta_cp value.
    chi2_sm_minos, chi2_geo_minos, dchi2_minos = _run_runner(args.runner, args.minos_pack, dcp_geo, args)
    chi2_sm_nova,  chi2_geo_nova,  dchi2_nova  = _run_runner(args.runner, args.nova_pack,  dcp_geo, args)

    print(f"MINOS: chi2_SM(geo)={chi2_sm_minos:.3f}  chi2_GEO(geo)={chi2_geo_minos:.3f}  dchi2={dchi2_minos:+.3f}")
    print(f"NOvA : chi2_SM(geo)={chi2_sm_nova:.3f}  chi2_GEO(geo)={chi2_geo_nova:.3f}  dchi2={dchi2_nova:+.3f}")
    if not args.no_profile:
        print(f"T2K  : dchi2(delta_geo)={t2k_pen:.3f}")
    else:
        print("T2K  : (skipped)")

    dsum = dchi2_minos + dchi2_nova
    plus_pen = dsum + t2k_pen
    score = dsum - t2k_pen

    print("\nSUM      = dchi2_MINOS + dchi2_NOVA = {:+.3f}".format(dsum))
    print("PLUS_PEN = SUM + T2K_pen            = {:+.3f}   (chi2-like; lower better)".format(plus_pen))
    print("SCORE    = SUM - T2K_pen            = {:+.3f}   (net-score; higher better)".format(score))
    print("--------------------------------------------------\n")

if __name__ == "__main__":
    main()