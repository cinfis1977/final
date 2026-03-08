#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finalize a preregistered particle-specific verdict from three already-run folders:
  - discovery (A1-B2)
  - holdout (A1-B3)
  - third-arm (A2-B3)

This script is FIT-FREE: it only summarizes locked metrics that are already produced
by the multi-target runner (delta_success_width_pairs + bin_success_width_stats).

Outputs:
  - <out_dir>/prereg_lock_and_final_verdict_goodppm<GOOD>.json
  - <out_dir>/FINAL_VERDICT_REPORT_goodppm<GOOD>.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def md5_file(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rp(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


def must_exist(p: Path, what: str) -> Path:
    if not p.exists():
        raise FileNotFoundError(f"[FATAL] missing {what}: {p}")
    return p


def summarize_delta(delta_pairs_csv: Path) -> pd.DataFrame:
    d = pd.read_csv(delta_pairs_csv)
    need = {"target_label", "delta_p_success"}
    missing = need - set(d.columns)
    if missing:
        raise ValueError(f"[FATAL] {delta_pairs_csv} missing columns: {sorted(missing)}")
    g = (
        d.groupby("target_label", as_index=True)
        .agg(
            abs_mean=("delta_p_success", lambda v: float(np.mean(np.abs(v)))),
            signed_mean=("delta_p_success", lambda v: float(np.mean(v))),
        )
        .sort_index()
    )
    return g


def summarize_mad(delta_pairs_csv: Path) -> pd.Series:
    d = pd.read_csv(delta_pairs_csv)
    need = {"target_label", "ratio_mad_success"}
    missing = need - set(d.columns)
    if missing:
        raise ValueError(f"[FATAL] {delta_pairs_csv} missing columns: {sorted(missing)}")
    x = d[["target_label", "ratio_mad_success"]].copy()
    x = x[np.isfinite(x["ratio_mad_success"]) & (x["ratio_mad_success"] > 0)]
    # Use mean(|log(ratio)|) as a stable “width-change magnitude” score per target.
    s = x.groupby("target_label")["ratio_mad_success"].apply(
        lambda v: float(np.mean(np.abs(np.log(v))))
    )
    return s


def psuccess_level(bin_stats_csv: Path) -> dict:
    d = pd.read_csv(bin_stats_csv)
    if "p_success" not in d.columns:
        raise ValueError(f"[FATAL] {bin_stats_csv} missing column: p_success")
    return {
        "mean_p_success": float(d["p_success"].mean()),
        "median_p_success": float(d["p_success"].median()),
        "min_p_success": float(d["p_success"].min()),
        "max_p_success": float(d["p_success"].max()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root (default: .)")
    ap.add_argument("--pair_b2_dir", required=True, help="Run folder for A1-B2 (good_ppm locked).")
    ap.add_argument("--pair_b3_dir", required=True, help="Run folder for A1-B3 holdout (good_ppm locked).")
    ap.add_argument("--third_arm_dir", required=True, help="Run folder for A2-B3 third-arm (good_ppm locked).")
    ap.add_argument("--targets_csv", required=True, help="targets_used.csv used for topK auto-targets.")
    ap.add_argument("--out_dir", required=True, help="Where to write final lock+verdict artifacts.")

    # Locked prereg parameters (defaults match the current locked test)
    ap.add_argument("--good_ppm", type=float, default=3.0)
    ap.add_argument("--window_ppm", type=float, default=30.0)
    ap.add_argument("--tail3_ppm", type=float, default=-300000.0)
    ap.add_argument("--min_n", type=int, default=8)
    ap.add_argument("--max_bins", type=int, default=8)

    # Optional: record MD5s of the frozen points CSVs, if you want the artifact to be fully “signed”.
    ap.add_argument("--mode_a_points", default=None)
    ap.add_argument("--mode_b2_points", default=None)
    ap.add_argument("--mode_b3_points", default=None)
    ap.add_argument("--mode_a2_points", default=None)

    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_dir = (root / args.out_dir).resolve() if not Path(args.out_dir).is_absolute() else Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Required inputs
    pair_b2 = must_exist((root / args.pair_b2_dir).resolve() if not Path(args.pair_b2_dir).is_absolute() else Path(args.pair_b2_dir).resolve(), "pair_b2_dir")
    pair_b3 = must_exist((root / args.pair_b3_dir).resolve() if not Path(args.pair_b3_dir).is_absolute() else Path(args.pair_b3_dir).resolve(), "pair_b3_dir")
    third_arm = must_exist((root / args.third_arm_dir).resolve() if not Path(args.third_arm_dir).is_absolute() else Path(args.third_arm_dir).resolve(), "third_arm_dir")
    targets_csv = must_exist((root / args.targets_csv).resolve() if not Path(args.targets_csv).is_absolute() else Path(args.targets_csv).resolve(), "targets_csv")

    # Expected per-run files
    PairsName = "alltargets_delta_success_width_pairs.csv"
    BinsName = "alltargets_bin_success_width_stats.csv"

    p_b2 = must_exist(pair_b2 / PairsName, "A1-B2 delta_success_width_pairs")
    p_b3 = must_exist(pair_b3 / PairsName, "A1-B3 delta_success_width_pairs")
    p_a23 = must_exist(third_arm / PairsName, "A2-B3 delta_success_width_pairs")

    s_b2 = must_exist(pair_b2 / BinsName, "A1-B2 bin_success_width_stats")
    s_b3 = must_exist(pair_b3 / BinsName, "A1-B3 bin_success_width_stats")
    s_a23 = must_exist(third_arm / BinsName, "A2-B3 bin_success_width_stats")

    # Summaries
    g_b2 = summarize_delta(p_b2)
    g_b3 = summarize_delta(p_b3)
    g_a23 = summarize_delta(p_a23)

    # Holdout stability (B2 vs B3)
    m = g_b2.join(g_b3, lsuffix="_b2", rsuffix="_b3", how="inner")
    if len(m) == 0:
        raise ValueError("[FATAL] No overlapping targets between B2 and B3 summaries.")
    corr_abs = float(m["abs_mean_b2"].corr(m["abs_mean_b3"]))
    rank_corr_abs = float(m["abs_mean_b2"].rank().corr(m["abs_mean_b3"].rank()))
    median_abs_delta_b2 = float(m["abs_mean_b2"].median())
    median_abs_delta_b3 = float(m["abs_mean_b3"].median())
    nz_targets_b2 = int((m["abs_mean_b2"] > 1e-12).sum())
    nz_targets_b3 = int((m["abs_mean_b3"] > 1e-12).sum())

    # MAD stability
    mad_b2 = summarize_mad(p_b2)
    mad_b3 = summarize_mad(p_b3)
    mad_m = pd.concat([mad_b2.rename("b2"), mad_b3.rename("b3")], axis=1).dropna()
    if len(mad_m) == 0:
        raise ValueError("[FATAL] No overlapping targets for MAD summaries.")
    mad_rank_corr = float(mad_m["b2"].rank().corr(mad_m["b3"].rank()))
    mad_top_b2 = str(mad_m["b2"].idxmax())
    mad_top_b3 = str(mad_m["b3"].idxmax())
    mad_top_target_match = bool(mad_top_b2 == mad_top_b3)

    # Third-arm consistency
    tri = g_b2.join(g_b3, lsuffix="_b2", rsuffix="_b3", how="inner").join(g_a23, how="inner")
    tri = tri.rename(columns={"abs_mean": "abs_mean_a23", "signed_mean": "signed_mean_a23"})
    if len(tri) == 0:
        raise ValueError("[FATAL] No overlapping targets across the triplet (B2,B3,A23).")
    rank_corr_b2_a23 = float(tri["abs_mean_b2"].rank().corr(tri["abs_mean_a23"].rank()))
    rank_corr_b3_a23 = float(tri["abs_mean_b3"].rank().corr(tri["abs_mean_a23"].rank()))
    tri_top_b2 = str(tri["abs_mean_b2"].idxmax())
    tri_top_b3 = str(tri["abs_mean_b3"].idxmax())
    tri_top_a23 = str(tri["abs_mean_a23"].idxmax())
    tri_top_all_match = bool(tri_top_b2 == tri_top_b3 == tri_top_a23)

    # Locked criteria (same as current prereg gate)
    C1_psuccess = (
        (median_abs_delta_b2 >= 0.10)
        and (median_abs_delta_b3 >= 0.10)
        and (rank_corr_abs >= 0.90)
        and (nz_targets_b2 >= 10)
        and (nz_targets_b3 >= 10)
    )
    C2_mad = (mad_rank_corr >= 0.80) and mad_top_target_match
    C3_thirdarm = (rank_corr_b2_a23 >= 0.80) and (rank_corr_b3_a23 >= 0.80) and tri_top_all_match
    PASS_FINAL = bool(C1_psuccess and C2_mad and C3_thirdarm)

    ps_b2 = psuccess_level(s_b2)
    ps_b3 = psuccess_level(s_b3)
    ps_a23 = psuccess_level(s_a23)

    frozen_inputs = []
    for tag, p in [
        ("mode_a_points", args.mode_a_points),
        ("mode_b2_points", args.mode_b2_points),
        ("mode_b3_points", args.mode_b3_points),
        ("mode_a2_points", args.mode_a2_points),
    ]:
        if p:
            pp = Path(p)
            if not pp.is_absolute():
                pp = root / pp
            pp = pp.resolve()
            if pp.exists():
                frozen_inputs.append({"path": rp(root, pp), "size": pp.stat().st_size, "md5": md5_file(pp), "tag": tag})
    # Always include targets_csv
    frozen_inputs.append({"path": rp(root, targets_csv), "size": targets_csv.stat().st_size, "md5": md5_file(targets_csv), "tag": "targets_csv"})

    lock = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "prereg_lock": {
            "good_ppm": float(args.good_ppm),
            "window_ppm": float(args.window_ppm),
            "tail3_ppm": float(args.tail3_ppm),
            "min_n": int(args.min_n),
            "max_bins": int(args.max_bins),
            "targets_csv": rp(root, targets_csv),
            "analysis_rule": (
                "particle-specific if target-wise p_success signature is nonzero and stable in holdout; "
                "MAD signature also stable; third-arm consistency required"
            ),
        },
        "run_folders": {
            "pair_b2_dir": rp(root, pair_b2),
            "pair_b3_dir": rp(root, pair_b3),
            "third_arm_dir": rp(root, third_arm),
        },
        "frozen_inputs": frozen_inputs,
        "metrics": {
            "A1_B2_vs_A1_B3": {
                "median_abs_delta_b2": median_abs_delta_b2,
                "median_abs_delta_b3": median_abs_delta_b3,
                "rank_corr_abs": rank_corr_abs,
                "corr_abs": corr_abs,
                "nz_targets_b2": nz_targets_b2,
                "nz_targets_b3": nz_targets_b3,
                "mad_rank_corr": mad_rank_corr,
                "mad_top_b2": mad_top_b2,
                "mad_top_b3": mad_top_b3,
                "mad_top_target_match": mad_top_target_match,
            },
            "third_arm_A2_B3": {
                "rank_corr_b2_a23": rank_corr_b2_a23,
                "rank_corr_b3_a23": rank_corr_b3_a23,
                "top_b2": tri_top_b2,
                "top_b3": tri_top_b3,
                "top_a23": tri_top_a23,
                "top_all_match": tri_top_all_match,
            },
            "psuccess_levels": {
                "A1_B2": ps_b2,
                "A1_B3_holdout": ps_b3,
                "A2_B3": ps_a23,
            },
        },
        "criteria": {"C1_psuccess": C1_psuccess, "C2_mad": C2_mad, "C3_thirdarm": C3_thirdarm},
        "final_verdict": "PASS" if PASS_FINAL else "FAIL",
    }

    good_tag = str(int(args.good_ppm)) if float(args.good_ppm).is_integer() else str(args.good_ppm).replace(".", "p")
    json_path = out_dir / f"prereg_lock_and_final_verdict_goodppm{good_tag}.json"
    md_path = out_dir / f"FINAL_VERDICT_REPORT_goodppm{good_tag}.md"

    json_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")

    md = []
    md.append(f"# Particle-Specific Final Verdict (Prereg Lock: good_ppm={args.good_ppm})")
    md.append("")
    md.append(f"Generated (UTC): {lock['generated_utc']}")
    md.append("")
    md.append("## Prereg Lock")
    md.append(f"- good_ppm: {args.good_ppm}")
    md.append(f"- window_ppm: {args.window_ppm}")
    md.append(f"- tail3_ppm: {args.tail3_ppm}")
    md.append(f"- min_n: {args.min_n}")
    md.append(f"- max_bins: {args.max_bins}")
    md.append(f"- targets: `{rp(root, targets_csv)}`")
    md.append("")
    md.append("## Core Results")
    md.append(f"- median_abs_delta_p_success (A1-B2): {median_abs_delta_b2:.6f}")
    md.append(f"- median_abs_delta_p_success (A1-B3 holdout): {median_abs_delta_b3:.6f}")
    md.append(f"- holdout rank_corr_abs: {rank_corr_abs:.6f}")
    md.append(f"- nz target count (A1-B2 / A1-B3): {nz_targets_b2} / {nz_targets_b3}")
    md.append(f"- MAD rank correlation (A1-B2 vs A1-B3): {mad_rank_corr:.6f}")
    md.append(f"- MAD top target match: {mad_top_b2} vs {mad_top_b3} -> {mad_top_target_match}")
    md.append("")
    md.append("## Third-Arm Consistency (A2-B3)")
    md.append(f"- rank_corr (B2 vs A23): {rank_corr_b2_a23:.6f}")
    md.append(f"- rank_corr (B3 vs A23): {rank_corr_b3_a23:.6f}")
    md.append(f"- top target triplet: {tri_top_b2}, {tri_top_b3}, {tri_top_a23} -> all_match={tri_top_all_match}")
    md.append("")
    md.append("## Criteria")
    md.append(f"- C1 (p_success signature + holdout stability): {C1_psuccess}")
    md.append(f"- C2 (MAD signature stability): {C2_mad}")
    md.append(f"- C3 (third-arm consistency): {C3_thirdarm}")
    md.append("")
    md.append("## Final Verdict")
    md.append(f"**{lock['final_verdict']}**")
    md.append("")
    md.append("## Artifact Paths")
    md.append(f"- JSON lock+verdict: `{rp(root, json_path)}`")
    md.append(f"- MD report: `{rp(root, md_path)}`")
    md.append(f"- A1-B2 run dir: `{rp(root, pair_b2)}`")
    md.append(f"- A1-B3 holdout run dir: `{rp(root, pair_b3)}`")
    md.append(f"- A2-B3 third-arm run dir: `{rp(root, third_arm)}`")

    md_path.write_text("\n".join(md), encoding="utf-8")

    print(f"[WROTE] {json_path}")
    print(f"[WROTE] {md_path}")
    print(f"[FINAL] {lock['final_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
