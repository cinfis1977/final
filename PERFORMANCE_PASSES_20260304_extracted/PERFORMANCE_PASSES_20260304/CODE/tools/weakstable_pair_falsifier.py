#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    build_pair_metrics,
    build_target_windows,
    filter_window,
    percentile_cut,
    read_points,
    read_targets,
    weighted_median,
)


PAIR_KEYS: List[Tuple[str, str]] = [("T05", "T12"), ("T09", "T08")]
TARGET_IDS: List[str] = ["T05", "T12", "T09", "T08"]


@dataclass(frozen=True)
class RunSpec:
    run_name: str
    input_paths: List[Path]


def canonical_pair_id(a: str, b: str) -> str:
    x, y = sorted([str(a), str(b)])
    return f"{x}<->{y}"


def _find_pair_row(df: pd.DataFrame, a: str, b: str) -> Optional[pd.Series]:
    m = (
        ((df["target_a"].astype(str) == a) & (df["target_b"].astype(str) == b))
        | ((df["target_a"].astype(str) == b) & (df["target_b"].astype(str) == a))
    )
    sub = df[m]
    if sub.empty:
        return None
    return sub.iloc[0]


def weighted_mad(values: Iterable[float], weights: Iterable[float]) -> float:
    v = pd.Series(list(values), dtype=float)
    w = pd.Series(list(weights), dtype=float)
    if v.empty:
        return float("nan")
    med = weighted_median(v.to_numpy(), w.to_numpy())
    dev = (v - med).abs()
    return weighted_median(dev.to_numpy(), w.to_numpy())


def ensure_paths_exist(paths: Dict[str, Path]) -> None:
    missing = [f"{k}: {v}" for k, v in paths.items() if not v.exists()]
    if missing:
        raise FileNotFoundError("Missing required input files:\n" + "\n".join(missing))


def compute_target_windows_for_pair_targets(
    points_all: pd.DataFrame, targets_df: pd.DataFrame, run_name: str
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for _, t in targets_df.iterrows():
        target_id = str(t["label"])
        target_mz = float(t["target_mz"])
        window_ppm = float(t["window_ppm"])
        sub = filter_window(points_all, target_mz, window_ppm)
        point_count = int(len(sub))
        summed_intensity = float(sub["intensity"].sum()) if point_count else 0.0
        wmz = (
            weighted_median(sub["mz"].to_numpy(dtype=float), sub["intensity"].to_numpy(dtype=float))
            if point_count
            else float("nan")
        )
        spread = (
            weighted_mad(sub["mz"].to_numpy(dtype=float), sub["intensity"].to_numpy(dtype=float))
            if point_count
            else float("nan")
        )
        rows.append(
            {
                "run_name": run_name,
                "target_id": target_id,
                "weighted_median_mz": wmz,
                "local_spread_mz": spread,
                "local_spread_method": "weighted_mad_fallback",
                "point_count": point_count,
                "summed_intensity": summed_intensity,
                "target_mz_nominal": target_mz,
                "window_ppm": window_ppm,
            }
        )
    return pd.DataFrame(rows)


def build_pair_anatomy(
    run_name: str,
    rebuilt_pairs: pd.DataFrame,
    comparator_pairs: pd.DataFrame,
) -> Tuple[pd.DataFrame, float, float]:
    stable_margins = rebuilt_pairs.loc[
        rebuilt_pairs["classification"] == "STABLE-INTERMEDIATE-CANDIDATE",
        "nearest_stable_boundary_margin",
    ].astype(float)
    weak_cut = percentile_cut(stable_margins.tolist(), FROZEN_CONFIDENCE_QUANTILE)
    stable_abs_dist = (stable_margins - weak_cut).abs().tolist()
    edge_band = float(median(stable_abs_dist)) if stable_abs_dist else 0.0

    comp_stable = comparator_pairs.loc[
        comparator_pairs["classification"] == "STABLE-INTERMEDIATE-CANDIDATE",
        "nearest_stable_boundary_margin",
    ].astype(float)
    comp_weak_cut = percentile_cut(comp_stable.tolist(), FROZEN_CONFIDENCE_QUANTILE)

    rows: List[Dict[str, object]] = []
    for a, b in PAIR_KEYS:
        pid = canonical_pair_id(a, b)
        r = _find_pair_row(rebuilt_pairs, a, b)
        c = _find_pair_row(comparator_pairs, a, b)
        if r is None:
            raise ValueError(f"Pair missing in rebuilt run {run_name}: {a}<->{b}")
        if c is None:
            raise ValueError(f"Pair missing in archived comparator: {a}<->{b}")

        stable_margin = float(r["nearest_stable_boundary_margin"])
        signed_dist = stable_margin - weak_cut
        abs_dist = abs(signed_dist)
        near_edge = abs_dist <= edge_band

        comp_stable_margin = float(c["nearest_stable_boundary_margin"])
        comp_signed_dist = comp_stable_margin - comp_weak_cut
        comp_abs_dist = abs(comp_signed_dist)

        base_label = str(r["classification"])
        boundary_confidence = str(r["boundary_confidence"])
        comp_label = str(c["classification"])
        comp_conf = str(c["boundary_confidence"])
        conf_changed = boundary_confidence != comp_conf

        if near_edge and (not conf_changed or abs_dist <= edge_band):
            pair_verdict = "BOUNDARY-PROXIMITY-SUPPORTED"
        elif conf_changed and not near_edge:
            pair_verdict = "CONFIDENCE-LAYER-TOO-SHARP"
        else:
            pair_verdict = "MIXED / INCONCLUSIVE"

        rows.append(
            {
                "run_name": run_name,
                "pair_id": pid,
                "target_a": str(r["target_a"]),
                "target_b": str(r["target_b"]),
                "delta_mz": float(r["delta_mz"]),
                "sep_norm": float(r["sep_norm"]),
                "overlap_proxy": float(r["overlap_proxy"]),
                "corridor_proxy": float(r["corridor_proxy"]),
                "rejection_proxy": float(r["rejection_proxy"]),
                "leak_reduction_proxy": float(r["leak_reduction_proxy"]),
                "base_label": base_label,
                "boundary_confidence": boundary_confidence,
                "stable_margin": float(r["stable_margin"]),
                "distance_to_weak_stable_edge": abs_dist,
                "signed_distance_to_weak_stable_edge": signed_dist,
                "weak_stable_edge_cut": weak_cut,
                "edge_band_median_abs_distance": edge_band,
                "comparator_base_label": comp_label,
                "comparator_boundary_confidence": comp_conf,
                "comparator_stable_margin": float(c["stable_margin"]),
                "comparator_distance_to_weak_stable_edge": comp_abs_dist,
                "comparator_signed_distance_to_weak_stable_edge": comp_signed_dist,
                "confidence_changed_vs_comparator": conf_changed,
                "near_weak_stable_edge": near_edge,
                "pair_level_verdict": pair_verdict,
            }
        )
    return pd.DataFrame(rows), weak_cut, edge_band


def write_run_verdict_md(
    out_path: Path,
    *,
    run: RunSpec,
    targets_csv: Path,
    comparator_csv: Path,
    context_refs: Dict[str, Path],
    windows_df: pd.DataFrame,
    anatomy_df: pd.DataFrame,
    weak_cut: float,
    edge_band: float,
) -> None:
    lines: List[str] = []
    lines.append(f"# Weak-Stable Pair Verdict: {run.run_name}")
    lines.append("")
    lines.append("## Exact Input Paths")
    for p in run.input_paths:
        lines.append(f"- raw_points: `{p}`")
    lines.append(f"- targets_csv: `{targets_csv}`")
    lines.append(f"- archived_track8_comparator_csv: `{comparator_csv}`")
    lines.append("")
    lines.append("## Reference Context Files (Not Threshold Source)")
    for k, v in context_refs.items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Frozen Thresholds")
    lines.append(f"- width_scale = {FROZEN_WIDTH_SCALE}")
    lines.append(f"- corridor_min = {FROZEN_CORRIDOR_MIN}")
    lines.append(f"- reject_max = {FROZEN_REJECT_MAX}")
    lines.append(f"- leak_ratio_max = {FROZEN_LEAK_RATIO_MAX}")
    lines.append(f"- sep_s0 = {FROZEN_SEP_S0}")
    lines.append(f"- confidence_quantile = {FROZEN_CONFIDENCE_QUANTILE}")
    lines.append("")
    lines.append("## Analyzed Pairs")
    lines.append("- T05<->T12")
    lines.append("- T09<->T08")
    lines.append("")
    lines.append("## Raw Target Window Stats (T05, T12, T09, T08)")
    for _, r in windows_df.iterrows():
        lines.append(
            f"- {r['target_id']}: weighted_median_mz={float(r['weighted_median_mz']):.12g}, "
            f"local_spread_mz={float(r['local_spread_mz']):.12g}, "
            f"point_count={int(r['point_count'])}, summed_intensity={float(r['summed_intensity']):.12g}"
        )
    lines.append("")
    lines.append("## Pair Metrics + Comparator (Archived Track8)")
    lines.append(f"- weak_stable_edge_cut (run): {weak_cut:.12g}")
    lines.append(f"- edge_band_median_abs_distance (run): {edge_band:.12g}")
    for _, r in anatomy_df.iterrows():
        lines.append(
            f"- {r['pair_id']}: delta_mz={float(r['delta_mz']):.12g}, sep_norm={float(r['sep_norm']):.12g}, "
            f"corridor={float(r['corridor_proxy']):.12g}, rejection={float(r['rejection_proxy']):.12g}, "
            f"leak_reduction={float(r['leak_reduction_proxy']):.12g}, "
            f"base_label={r['base_label']}, boundary_confidence={r['boundary_confidence']}, "
            f"signed_dist={float(r['signed_distance_to_weak_stable_edge']):.12g}, "
            f"abs_dist={float(r['distance_to_weak_stable_edge']):.12g}, "
            f"comp_label={r['comparator_base_label']}, comp_conf={r['comparator_boundary_confidence']}, "
            f"comp_signed_dist={float(r['comparator_signed_distance_to_weak_stable_edge']):.12g}, "
            f"near_edge={bool(r['near_weak_stable_edge'])}, "
            f"pair_verdict={r['pair_level_verdict']}"
        )
    lines.append("")
    lines.append("## Pair-Level Verdicts")
    for _, r in anatomy_df.iterrows():
        lines.append(f"- {r['pair_id']}: {r['pair_level_verdict']}")
    lines.append("")
    lines.append("Note: local_spread_mz uses weighted MAD fallback (no separate robust spread formula found in project scripts).")
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_rollup_md(out_path: Path, rows: List[pd.DataFrame]) -> None:
    all_df = pd.concat(rows, ignore_index=True)
    lines: List[str] = []
    lines.append("# Weak-Stable Pair Falsifier Rollup")
    lines.append("")
    lines.append("| run | pair | base_label | confidence | signed_dist | abs_dist | near_edge | conf_changed_vs_track8 | pair_verdict |")
    lines.append("|---|---|---|---|---:|---:|---|---|---|")
    for _, r in all_df.iterrows():
        lines.append(
            f"| {r['run_name']} | {r['pair_id']} | {r['base_label']} | {r['boundary_confidence']} | "
            f"{float(r['signed_distance_to_weak_stable_edge']):.12g} | {float(r['distance_to_weak_stable_edge']):.12g} | "
            f"{bool(r['near_weak_stable_edge'])} | {bool(r['confidence_changed_vs_comparator'])} | {r['pair_level_verdict']} |"
        )
    lines.append("")

    answers: Dict[str, str] = {}
    for pair in [canonical_pair_id(*PAIR_KEYS[0]), canonical_pair_id(*PAIR_KEYS[1])]:
        sub = all_df[all_df["pair_id"] == pair].copy()
        all_stable = bool((sub["base_label"] == "STABLE-INTERMEDIATE-CANDIDATE").all())
        all_near = bool(sub["near_weak_stable_edge"].all())
        any_conf_change = bool(sub["confidence_changed_vs_comparator"].any())
        conf_change_far = bool((sub["confidence_changed_vs_comparator"] & (~sub["near_weak_stable_edge"])).any())
        if all_stable and all_near:
            answers[pair] = "YES"
        elif conf_change_far:
            answers[pair] = "NO (confidence drift appears too sharp)"
        else:
            answers[pair] = "MIXED / INCONCLUSIVE"
        # keep vars used for Q3/Q4
        _ = any_conf_change

    any_too_sharp = bool(
        (all_df["confidence_changed_vs_comparator"] & (~all_df["near_weak_stable_edge"])).any()
    )
    drifts_consistent = not any_too_sharp

    lines.append("## Explicit Answers")
    lines.append(f"1. Is T05<->T12 a genuine weak-stable boundary pair across arms? **{answers.get('T05<->T12','MIXED / INCONCLUSIVE')}**")
    lines.append(f"2. Is T09<->T08 a genuine weak-stable boundary pair across arms? **{answers.get('T08<->T09','MIXED / INCONCLUSIVE')}**")
    lines.append(
        f"3. Are observed confidence drifts physically consistent with boundary proximity? **{'YES' if drifts_consistent else 'NO'}**"
    )
    lines.append(
        f"4. Or does the confidence layer appear too sharp? **{'YES' if any_too_sharp else 'NO'}**"
    )
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Per-pair weak-stable falsifier for T05<->T12 and T09<->T08.")
    ap.add_argument("--modea_points", required=True)
    ap.add_argument("--modeb_points", required=True)
    ap.add_argument("--modeb_holdout_points", required=True)
    ap.add_argument("--targets_csv", required=True)
    ap.add_argument("--comparator_csv", required=True, help="Archived Track8 comparator CSV (must exist).")
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
    ensure_paths_exist(required)

    context_candidates = {
        "arm_by_arm_rebuild_rollup.md": out_dir.parent / "arm_by_arm_rebuild_frozen_20260227" / "arm_by_arm_rebuild_rollup.md",
        "rebuilt_two_center_verdict_A1_B2_ModeA.md": out_dir.parent / "arm_by_arm_rebuild_frozen_20260227" / "rebuilt_two_center_verdict_A1_B2_ModeA.md",
        "rebuilt_two_center_verdict_A1_B2_ModeB.md": out_dir.parent / "arm_by_arm_rebuild_frozen_20260227" / "rebuilt_two_center_verdict_A1_B2_ModeB.md",
        "rebuilt_two_center_verdict_A1_B2_direct_ModeB_holdout.md": out_dir.parent / "arm_by_arm_rebuild_frozen_20260227" / "rebuilt_two_center_verdict_A1_B2_direct_ModeB_holdout.md",
        "rebuilt_two_center_verdict_Combined_A1_B2_plus_holdout.md": out_dir.parent / "arm_by_arm_rebuild_frozen_20260227" / "rebuilt_two_center_verdict_Combined_A1_B2_plus_holdout.md",
    }
    context_refs = {k: v.resolve() for k, v in context_candidates.items() if v.exists()}

    print("=== RESOLVED INPUT PATHS ===")
    for k, p in required.items():
        print(f"{k}={p}")
    print("=== REFERENCE CONTEXT PATHS (OPTIONAL) ===")
    if context_refs:
        for k, p in context_refs.items():
            print(f"{k}={p}")
    else:
        print("none")

    targets = read_targets(targets_csv)
    targets_df = pd.DataFrame(
        [{"label": t.label, "target_mz": t.target_mz, "window_ppm": t.window_ppm} for t in targets]
    )
    pair_targets_df = targets_df[targets_df["label"].isin(TARGET_IDS)].copy()
    if len(pair_targets_df) != len(TARGET_IDS):
        have = set(pair_targets_df["label"].astype(str).tolist())
        miss = [x for x in TARGET_IDS if x not in have]
        raise ValueError(f"Required pair targets missing in targets_csv: {miss}")

    comparator_pairs = pd.read_csv(comparator_csv)
    all_anatomy_rows: List[pd.DataFrame] = []
    output_paths: List[Path] = []

    runs = [
        RunSpec("A1_B2_ModeA", [modea]),
        RunSpec("A1_B2_ModeB", [modeb]),
        RunSpec("A1_B2_direct_ModeB_holdout", [hold]),
        RunSpec("Combined_A1_B2_plus_holdout", [modea, modeb, hold]),
    ]

    for run in runs:
        frames = [read_points(p, p.stem) for p in run.input_paths]
        points_all = pd.concat(frames, ignore_index=True)

        windows_df = compute_target_windows_for_pair_targets(points_all, pair_targets_df, run.run_name)
        windows_csv = out_dir / f"weakstable_pair_windows_{run.run_name}.csv"
        windows_df.to_csv(windows_csv, index=False)
        output_paths.append(windows_csv)

        all_target_windows = build_target_windows(targets, points_all)
        rebuilt_pairs = build_pair_metrics(all_target_windows[all_target_windows["source"] == "ALL"].copy())

        anatomy_df, weak_cut, edge_band = build_pair_anatomy(run.run_name, rebuilt_pairs, comparator_pairs)
        anatomy_csv = out_dir / f"weakstable_pair_anatomy_{run.run_name}.csv"
        anatomy_df.to_csv(anatomy_csv, index=False)
        output_paths.append(anatomy_csv)

        verdict_md = out_dir / f"weakstable_pair_verdict_{run.run_name}.md"
        write_run_verdict_md(
            verdict_md,
            run=run,
            targets_csv=targets_csv,
            comparator_csv=comparator_csv,
            context_refs=context_refs,
            windows_df=windows_df,
            anatomy_df=anatomy_df,
            weak_cut=weak_cut,
            edge_band=edge_band,
        )
        output_paths.append(verdict_md)
        all_anatomy_rows.append(anatomy_df)

    rollup_md = out_dir / "weakstable_pair_falsifier_rollup.md"
    build_rollup_md(rollup_md, all_anatomy_rows)
    output_paths.append(rollup_md)

    print("=== OUTPUT FILES ===")
    for p in output_paths:
        print(str(p))


if __name__ == "__main__":
    main()
