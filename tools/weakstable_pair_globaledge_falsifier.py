#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from rebuild_two_center_diagnostic_frozen import (
    FROZEN_CONFIDENCE_QUANTILE,
    FROZEN_CORRIDOR_MIN,
    FROZEN_LEAK_RATIO_MAX,
    FROZEN_REJECT_MAX,
    FROZEN_SEP_S0,
    FROZEN_WIDTH_SCALE,
    filter_window,
    percentile_cut,
    read_points,
    read_targets,
    weighted_median,
)


PAIR_KEYS: List[Tuple[str, str]] = [("T05", "T12"), ("T09", "T08")]
PAIR_TARGETS: List[str] = ["T05", "T12", "T09", "T08"]


@dataclass(frozen=True)
class RunSpec:
    run_name: str
    input_paths: List[Path]


def canonical_pair_id(a: str, b: str) -> str:
    x, y = sorted([str(a), str(b)])
    return f"{x}<->{y}"


def weighted_mad(values: Iterable[float], weights: Iterable[float]) -> float:
    vals = pd.Series(list(values), dtype=float)
    wts = pd.Series(list(weights), dtype=float)
    if vals.empty:
        return float("nan")
    med = weighted_median(vals.to_numpy(dtype=float), wts.to_numpy(dtype=float))
    dev = (vals - med).abs()
    return weighted_median(dev.to_numpy(dtype=float), wts.to_numpy(dtype=float))


def ensure_exists(paths: Dict[str, Path]) -> None:
    missing = [f"{k}: {v}" for k, v in paths.items() if not v.exists()]
    if missing:
        raise FileNotFoundError("Missing required input files:\n" + "\n".join(missing))


def read_comparator(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "pair_shell",
        "target_a",
        "target_b",
        "classification",
        "boundary_confidence",
        "nearest_stable_boundary_margin",
        "repulsive_margin",
        "stable_margin",
        "delta_mz",
        "sep_norm",
        "overlap_proxy",
        "corridor_proxy",
        "rejection_proxy",
        "leak_reduction_proxy",
    }
    missing = sorted(required.difference(set(df.columns)))
    if missing:
        raise ValueError(f"Comparator CSV missing required columns: {missing}")
    return df


def compute_global_edges_from_comparator(comparator: pd.DataFrame) -> Tuple[float, float, float]:
    stable = comparator.loc[
        comparator["classification"].astype(str) == "STABLE-INTERMEDIATE-CANDIDATE",
        "nearest_stable_boundary_margin",
    ].astype(float)
    if stable.empty:
        raise ValueError("Comparator has no stable rows; cannot compute global weak-stable edge.")

    repulsive = comparator.loc[
        comparator["classification"].astype(str) == "REPULSIVE",
        "repulsive_margin",
    ].astype(float)

    global_weak_edge = percentile_cut(stable.tolist(), FROZEN_CONFIDENCE_QUANTILE)
    stable_abs_dists = [abs(float(x) - global_weak_edge) for x in stable.tolist()]
    global_edge_band = float(median(stable_abs_dists)) if stable_abs_dists else 0.0
    global_repulsive_cut = percentile_cut(repulsive.tolist(), 1.0 - FROZEN_CONFIDENCE_QUANTILE) if not repulsive.empty else 0.0
    return float(global_weak_edge), float(global_edge_band), float(global_repulsive_cut)


def build_target_windows(points: pd.DataFrame, targets_df: pd.DataFrame, run_name: str) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for _, t in targets_df.iterrows():
        target_id = str(t["label"])
        target_mz = float(t["target_mz"])
        window_ppm = float(t["window_ppm"])
        sub = filter_window(points, target_mz, window_ppm)
        n = int(len(sub))
        wmz = weighted_median(sub["mz"].to_numpy(dtype=float), sub["intensity"].to_numpy(dtype=float)) if n else float("nan")
        spread = weighted_mad(sub["mz"].to_numpy(dtype=float), sub["intensity"].to_numpy(dtype=float)) if n else float("nan")
        rows.append(
            {
                "run_name": run_name,
                "target_id": target_id,
                "weighted_median_mz": wmz,
                "local_spread_mz": spread,
                "local_spread_method": "weighted_mad_fallback",
                "point_count": n,
                "summed_intensity": float(sub["intensity"].sum()) if n else 0.0,
                "target_mz_nominal": target_mz,
                "window_ppm": window_ppm,
            }
        )
    return pd.DataFrame(rows)


def classify_base_label(corridor: float, rejection: float, effective_leak_ratio: float) -> str:
    if corridor >= FROZEN_CORRIDOR_MIN and rejection <= FROZEN_REJECT_MAX and effective_leak_ratio <= FROZEN_LEAK_RATIO_MAX:
        return "STABLE-INTERMEDIATE-CANDIDATE"
    if corridor < FROZEN_CORRIDOR_MIN and rejection > FROZEN_REJECT_MAX:
        return "REPULSIVE"
    return "INCONCLUSIVE"


def compute_pair_metrics(
    run_name: str,
    windows_df: pd.DataFrame,
    comparator: pd.DataFrame,
    global_weak_edge: float,
    global_edge_band: float,
    global_repulsive_cut: float,
) -> pd.DataFrame:
    by_target = {str(r["target_id"]): float(r["weighted_median_mz"]) for _, r in windows_df.iterrows()}
    rows: List[Dict[str, object]] = []

    for a, b in PAIR_KEYS:
        pid = canonical_pair_id(a, b)
        if a not in by_target or b not in by_target:
            raise ValueError(f"Missing target window for pair {pid} in run {run_name}")

        mz_a = by_target[a]
        mz_b = by_target[b]
        delta = abs(mz_b - mz_a)
        overlap = math.exp(-delta / max(FROZEN_WIDTH_SCALE, 1e-12))
        corridor = overlap
        rejection = 1.0 - overlap
        leak_reduction = 0.5 * overlap
        effective_leak_ratio = max(0.0, 1.0 - leak_reduction)
        sep_norm = delta / (delta + FROZEN_SEP_S0) if (delta + FROZEN_SEP_S0) > 0 else 0.0

        stable_margin = corridor - FROZEN_CORRIDOR_MIN
        reject_margin = FROZEN_REJECT_MAX - rejection
        leak_margin = FROZEN_LEAK_RATIO_MAX - effective_leak_ratio
        nearest_stable = min(stable_margin, reject_margin, leak_margin)
        repulsive_margin = min(FROZEN_CORRIDOR_MIN - corridor, rejection - FROZEN_REJECT_MAX)
        base_label = classify_base_label(corridor, rejection, effective_leak_ratio)

        if base_label == "STABLE-INTERMEDIATE-CANDIDATE":
            boundary_conf = "WEAK_STABLE" if nearest_stable <= global_weak_edge else "STRONG_STABLE"
        elif base_label == "REPULSIVE":
            boundary_conf = "STRONG_REPULSIVE" if repulsive_margin >= global_repulsive_cut else "BORDERLINE"
        else:
            boundary_conf = "BORDERLINE"

        signed_dist = nearest_stable - global_weak_edge
        abs_dist = abs(signed_dist)
        near_global_edge = abs_dist <= global_edge_band

        comp_row = comparator[
            (
                (comparator["target_a"].astype(str) == a)
                & (comparator["target_b"].astype(str) == b)
            )
            | (
                (comparator["target_a"].astype(str) == b)
                & (comparator["target_b"].astype(str) == a)
            )
        ]
        if comp_row.empty:
            raise ValueError(f"Pair {pid} missing in archived comparator.")
        comp = comp_row.iloc[0]
        comp_nearest = float(comp["nearest_stable_boundary_margin"])
        comp_signed = comp_nearest - global_weak_edge
        comp_abs = abs(comp_signed)
        comp_conf = str(comp["boundary_confidence"])
        confidence_changed = comp_conf != boundary_conf

        rows.append(
            {
                "run_name": run_name,
                "pair_id": pid,
                "target_a": a,
                "target_b": b,
                "delta_mz": delta,
                "sep_norm": sep_norm,
                "overlap_proxy": overlap,
                "corridor_proxy": corridor,
                "rejection_proxy": rejection,
                "leak_reduction_proxy": leak_reduction,
                "base_label": base_label,
                "boundary_confidence": boundary_conf,
                "stable_margin": stable_margin,
                "nearest_stable_boundary_margin": nearest_stable,
                "distance_to_global_frozen_weak_stable_edge": abs_dist,
                "signed_distance_to_global_frozen_weak_stable_edge": signed_dist,
                "near_global_edge_flag": near_global_edge,
                "comparator_base_label": str(comp["classification"]),
                "comparator_boundary_confidence": comp_conf,
                "comparator_stable_margin": float(comp["stable_margin"]),
                "comparator_nearest_stable_boundary_margin": comp_nearest,
                "comparator_distance_to_global_frozen_weak_stable_edge": comp_abs,
                "comparator_signed_distance_to_global_frozen_weak_stable_edge": comp_signed,
                "confidence_changed_vs_comparator": confidence_changed,
            }
        )
    return pd.DataFrame(rows)


def pair_verdict_for_run(row: pd.Series, global_edge_band: float) -> str:
    near_edge = bool(row["near_global_edge_flag"])
    conf_changed = bool(row["confidence_changed_vs_comparator"])
    signed_dist = float(row["signed_distance_to_global_frozen_weak_stable_edge"])
    if near_edge and (not conf_changed or abs(signed_dist) <= global_edge_band):
        return "GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED"
    if conf_changed and (not near_edge):
        return "EDGE-RECALC-DEPENDENT / NOT-HARD-SUPPORTED"
    return "MIXED / INCONCLUSIVE"


def write_run_verdict_md(
    out_md: Path,
    *,
    run: RunSpec,
    targets_csv: Path,
    comparator_csv: Path,
    context_refs: Dict[str, Path],
    windows_df: pd.DataFrame,
    anatomy_df: pd.DataFrame,
    global_weak_edge: float,
    global_edge_band: float,
) -> None:
    lines: List[str] = []
    lines.append(f"# Weak-Stable Global-Edge Verdict: {run.run_name}")
    lines.append("")
    lines.append("## Exact Input Paths")
    for p in run.input_paths:
        lines.append(f"- raw_points: `{p}`")
    lines.append(f"- targets_csv: `{targets_csv}`")
    lines.append(f"- archived_track8_comparator_csv: `{comparator_csv}`")
    lines.append("")
    lines.append("## Reference-Only Context")
    if context_refs:
        for k, p in context_refs.items():
            lines.append(f"- {k}: `{p}`")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Frozen Thresholds")
    lines.append(f"- width_scale = {FROZEN_WIDTH_SCALE}")
    lines.append(f"- corridor_min = {FROZEN_CORRIDOR_MIN}")
    lines.append(f"- reject_max = {FROZEN_REJECT_MAX}")
    lines.append(f"- leak_ratio_max = {FROZEN_LEAK_RATIO_MAX}")
    lines.append(f"- sep_s0 = {FROZEN_SEP_S0}")
    lines.append(f"- confidence_quantile = {FROZEN_CONFIDENCE_QUANTILE}")
    lines.append("")
    lines.append("## Single Global Frozen Weak-Stable Edge")
    lines.append(f"- global_frozen_weak_stable_edge = {global_weak_edge:.12g}")
    lines.append(f"- global_edge_band_median_abs_distance = {global_edge_band:.12g}")
    lines.append("")
    lines.append("## Analyzed Pairs")
    lines.append("- T05<->T12")
    lines.append("- T09<->T08")
    lines.append("")
    lines.append("## Raw Target Window Stats")
    for _, r in windows_df.iterrows():
        lines.append(
            f"- {r['target_id']}: weighted_median_mz={float(r['weighted_median_mz']):.12g}, "
            f"local_spread_mz={float(r['local_spread_mz']):.12g}, point_count={int(r['point_count'])}, "
            f"summed_intensity={float(r['summed_intensity']):.12g}"
        )
    lines.append("")
    lines.append("## Pair Metrics + Archived Comparator")
    for _, r in anatomy_df.iterrows():
        lines.append(
            f"- {r['pair_id']}: delta_mz={float(r['delta_mz']):.12g}, sep_norm={float(r['sep_norm']):.12g}, "
            f"overlap={float(r['overlap_proxy']):.12g}, corridor={float(r['corridor_proxy']):.12g}, "
            f"rejection={float(r['rejection_proxy']):.12g}, leak_reduction={float(r['leak_reduction_proxy']):.12g}, "
            f"base_label={r['base_label']}, boundary_confidence={r['boundary_confidence']}, "
            f"stable_margin={float(r['stable_margin']):.12g}, "
            f"signed_dist_global={float(r['signed_distance_to_global_frozen_weak_stable_edge']):.12g}, "
            f"abs_dist_global={float(r['distance_to_global_frozen_weak_stable_edge']):.12g}, "
            f"near_global_edge={bool(r['near_global_edge_flag'])}, "
            f"comp_label={r['comparator_base_label']}, comp_conf={r['comparator_boundary_confidence']}, "
            f"comp_signed_dist_global={float(r['comparator_signed_distance_to_global_frozen_weak_stable_edge']):.12g}"
        )
    lines.append("")
    lines.append("## Pair-Level Verdicts")
    for _, r in anatomy_df.iterrows():
        pv = pair_verdict_for_run(r, global_edge_band)
        lines.append(f"- {r['pair_id']}: {pv}")
    lines.append("")
    lines.append("Note: local_spread_mz uses weighted MAD fallback (no separate robust spread method found in current project scripts).")
    lines.append("")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_rollup_md(out_md: Path, all_df: pd.DataFrame, global_weak_edge: float, global_edge_band: float) -> None:
    lines: List[str] = []
    lines.append("# Weak-Stable Global-Edge Falsifier Rollup")
    lines.append("")
    lines.append(f"- global_frozen_weak_stable_edge: {global_weak_edge:.12g}")
    lines.append(f"- global_edge_band_median_abs_distance: {global_edge_band:.12g}")
    lines.append("")
    lines.append("| run | pair | base_label | confidence | signed_dist_global | abs_dist_global | near_global_edge | conf_changed_vs_track8 | pair_verdict |")
    lines.append("|---|---|---|---|---:|---:|---|---|---|")
    for _, r in all_df.iterrows():
        pv = pair_verdict_for_run(r, global_edge_band)
        lines.append(
            f"| {r['run_name']} | {r['pair_id']} | {r['base_label']} | {r['boundary_confidence']} | "
            f"{float(r['signed_distance_to_global_frozen_weak_stable_edge']):.12g} | {float(r['distance_to_global_frozen_weak_stable_edge']):.12g} | "
            f"{bool(r['near_global_edge_flag'])} | {bool(r['confidence_changed_vs_comparator'])} | {pv} |"
        )
    lines.append("")

    def answer_for_pair(pid: str) -> str:
        sub = all_df[all_df["pair_id"] == pid].copy()
        if sub.empty:
            return "MIXED / INCONCLUSIVE"
        all_near = bool(sub["near_global_edge_flag"].all())
        all_stable = bool((sub["base_label"].astype(str) == "STABLE-INTERMEDIATE-CANDIDATE").all())
        any_far_conf = bool((sub["confidence_changed_vs_comparator"] & (~sub["near_global_edge_flag"])).any())
        if all_near and all_stable:
            return "GLOBAL-BOUNDARY-PROXIMITY-SUPPORTED"
        if any_far_conf:
            return "EDGE-RECALC-DEPENDENT / NOT-HARD-SUPPORTED"
        return "MIXED / INCONCLUSIVE"

    ans_t05_t12 = answer_for_pair("T05<->T12")
    ans_t08_t09 = answer_for_pair("T08<->T09")
    any_not_supported = any(
        x == "EDGE-RECALC-DEPENDENT / NOT-HARD-SUPPORTED" for x in [ans_t05_t12, ans_t08_t09]
    )

    lines.append("## Explicit Answers")
    lines.append(f"1. Is T05<->T12 still a genuine weak-stable boundary pair under one single frozen edge? **{ans_t05_t12}**")
    lines.append(f"2. Is T09<->T08 still a genuine weak-stable boundary pair under one single frozen edge? **{ans_t08_t09}**")
    lines.append(
        f"3. Are observed confidence drifts still physically consistent with boundary proximity under one single frozen edge? **{'YES' if not any_not_supported else 'NO'}**"
    )
    lines.append(
        f"4. Or were earlier near-edge conclusions dependent on run-specific edge recalculation? **{'YES' if any_not_supported else 'NO'}**"
    )
    lines.append("")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Global frozen weak-stable edge falsifier for T05<->T12 and T09<->T08.")
    ap.add_argument("--modea_points", required=True)
    ap.add_argument("--modeb_points", required=True)
    ap.add_argument("--modeb_holdout_points", required=True)
    ap.add_argument("--targets_csv", required=True)
    ap.add_argument("--comparator_csv", required=True, help="Archived comparator; must already exist.")
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()

    modea = Path(args.modea_points).resolve()
    modeb = Path(args.modeb_points).resolve()
    hold = Path(args.modeb_holdout_points).resolve()
    targets_csv = Path(args.targets_csv).resolve()
    comparator_csv = Path(args.comparator_csv).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    required = {
        "modea_points": modea,
        "modeb_points": modeb,
        "modeb_holdout_points": hold,
        "targets_csv": targets_csv,
        "comparator_csv": comparator_csv,
    }
    ensure_exists(required)

    context_candidates = {
        "weakstable_pair_falsifier_rollup.md": out_dir.parent / "weakstable_pair_falsifier_20260227" / "weakstable_pair_falsifier_rollup.md",
        "weakstable_pair_verdict_A1_B2_ModeA.md": out_dir.parent / "weakstable_pair_falsifier_20260227" / "weakstable_pair_verdict_A1_B2_ModeA.md",
        "weakstable_pair_verdict_A1_B2_ModeB.md": out_dir.parent / "weakstable_pair_falsifier_20260227" / "weakstable_pair_verdict_A1_B2_ModeB.md",
        "weakstable_pair_verdict_A1_B2_direct_ModeB_holdout.md": out_dir.parent / "weakstable_pair_falsifier_20260227" / "weakstable_pair_verdict_A1_B2_direct_ModeB_holdout.md",
        "weakstable_pair_verdict_Combined_A1_B2_plus_holdout.md": out_dir.parent / "weakstable_pair_falsifier_20260227" / "weakstable_pair_verdict_Combined_A1_B2_plus_holdout.md",
    }
    context_refs = {k: p.resolve() for k, p in context_candidates.items() if p.exists()}

    print("=== RESOLVED REQUIRED INPUT PATHS ===")
    for k, p in required.items():
        print(f"{k}={p}")
    print("=== RESOLVED REFERENCE CONTEXT PATHS ===")
    if context_refs:
        for k, p in context_refs.items():
            print(f"{k}={p}")
    else:
        print("none")

    comparator = read_comparator(comparator_csv)
    global_weak_edge, global_edge_band, global_repulsive_cut = compute_global_edges_from_comparator(comparator)
    print(f"global_frozen_weak_stable_edge={global_weak_edge:.12g}")
    print(f"global_edge_band_median_abs_distance={global_edge_band:.12g}")
    print(f"global_frozen_repulsive_cut={global_repulsive_cut:.12g}")

    targets = read_targets(targets_csv)
    targets_df = pd.DataFrame([{"label": t.label, "target_mz": t.target_mz, "window_ppm": t.window_ppm} for t in targets])
    pair_targets_df = targets_df[targets_df["label"].isin(PAIR_TARGETS)].copy()
    missing_targets = sorted(set(PAIR_TARGETS).difference(set(pair_targets_df["label"].astype(str).tolist())))
    if missing_targets:
        raise ValueError(f"Missing required pair targets in targets_csv: {missing_targets}")

    runs = [
        RunSpec("A1_B2_ModeA", [modea]),
        RunSpec("A1_B2_ModeB", [modeb]),
        RunSpec("A1_B2_direct_ModeB_holdout", [hold]),
        RunSpec("Combined_A1_B2_plus_holdout", [modea, modeb, hold]),
    ]

    output_paths: List[Path] = []
    all_rows: List[pd.DataFrame] = []
    for run in runs:
        frames = [read_points(p, p.stem) for p in run.input_paths]
        points_all = pd.concat(frames, ignore_index=True)

        win = build_target_windows(points_all, pair_targets_df, run.run_name)
        win_csv = out_dir / f"weakstable_pair_windows_globaledge_{run.run_name}.csv"
        win.to_csv(win_csv, index=False)
        output_paths.append(win_csv)

        anatomy = compute_pair_metrics(
            run_name=run.run_name,
            windows_df=win,
            comparator=comparator,
            global_weak_edge=global_weak_edge,
            global_edge_band=global_edge_band,
            global_repulsive_cut=global_repulsive_cut,
        )
        anatomy["pair_level_verdict"] = anatomy.apply(lambda r: pair_verdict_for_run(r, global_edge_band), axis=1)
        anatomy_csv = out_dir / f"weakstable_pair_anatomy_globaledge_{run.run_name}.csv"
        anatomy.to_csv(anatomy_csv, index=False)
        output_paths.append(anatomy_csv)
        all_rows.append(anatomy)

        verdict_md = out_dir / f"weakstable_pair_verdict_globaledge_{run.run_name}.md"
        write_run_verdict_md(
            verdict_md,
            run=run,
            targets_csv=targets_csv,
            comparator_csv=comparator_csv,
            context_refs=context_refs,
            windows_df=win,
            anatomy_df=anatomy,
            global_weak_edge=global_weak_edge,
            global_edge_band=global_edge_band,
        )
        output_paths.append(verdict_md)

    all_df = pd.concat(all_rows, ignore_index=True)
    rollup_md = out_dir / "weakstable_pair_globaledge_rollup.md"
    write_rollup_md(rollup_md, all_df, global_weak_edge, global_edge_band)
    output_paths.append(rollup_md)

    print("=== OUTPUT FILE PATHS ===")
    for p in output_paths:
        print(str(p))


if __name__ == "__main__":
    main()
