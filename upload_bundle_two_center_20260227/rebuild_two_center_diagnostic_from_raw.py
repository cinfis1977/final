#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TargetRow:
    label: str
    target_mz: float
    window_ppm: float


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(mask):
        return float("nan")
    v = values[mask]
    w = weights[mask]
    order = np.argsort(v)
    v = v[order]
    w = w[order]
    cw = np.cumsum(w)
    cutoff = 0.5 * float(cw[-1])
    idx = int(np.searchsorted(cw, cutoff, side="left"))
    return float(v[min(idx, len(v) - 1)])


def read_targets(path: Path) -> List[TargetRow]:
    df = pd.read_csv(path)
    if not {"label", "target_mz", "window_ppm"}.issubset(set(df.columns)):
        raise ValueError(f"targets CSV missing required columns: {path}")
    out: List[TargetRow] = []
    for _, row in df.iterrows():
        out.append(
            TargetRow(
                label=str(row["label"]).strip(),
                target_mz=float(row["target_mz"]),
                window_ppm=float(row["window_ppm"]),
            )
        )
    return out


def read_points(path: Path, source_name: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"scan", "mz", "intensity"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"points CSV missing required columns {required}: {path}")
    out = pd.DataFrame(
        {
            "scan": pd.to_numeric(df["scan"], errors="coerce"),
            "mz": pd.to_numeric(df["mz"], errors="coerce"),
            "intensity": pd.to_numeric(df["intensity"], errors="coerce"),
        }
    ).dropna()
    out = out[(out["intensity"] > 0) & np.isfinite(out["mz"])]
    out["scan"] = out["scan"].astype(np.int64)
    out["source"] = source_name
    return out[["source", "scan", "mz", "intensity"]].copy()


def window_rows(points: pd.DataFrame, target: TargetRow) -> pd.DataFrame:
    half_width = target.target_mz * target.window_ppm * 1e-6
    lo = target.target_mz - half_width
    hi = target.target_mz + half_width
    return points[(points["mz"] >= lo) & (points["mz"] <= hi)].copy()


def build_target_windows(targets: List[TargetRow], points_all: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    source_names = sorted(points_all["source"].astype(str).unique().tolist())

    for t in targets:
        for src in source_names + ["ALL"]:
            sub = points_all if src == "ALL" else points_all[points_all["source"] == src]
            win = window_rows(sub, t)
            n_points = int(len(win))
            n_scans = int(win["scan"].nunique()) if n_points else 0
            rebuilt_mz = (
                weighted_median(
                    win["mz"].to_numpy(dtype=float),
                    win["intensity"].to_numpy(dtype=float),
                )
                if n_points
                else float("nan")
            )
            ppm_shift = (
                1e6 * (rebuilt_mz - t.target_mz) / t.target_mz
                if math.isfinite(rebuilt_mz)
                else float("nan")
            )
            rows.append(
                {
                    "target_label": t.label,
                    "target_mz_nominal": t.target_mz,
                    "window_ppm": t.window_ppm,
                    "source": src,
                    "n_points": n_points,
                    "n_scans": n_scans,
                    "rebuilt_mz_weighted": rebuilt_mz,
                    "ppm_shift_from_nominal": ppm_shift,
                }
            )

    return pd.DataFrame(rows)


def infer_thresholds(current_df: pd.DataFrame) -> Tuple[float, float, float, float, float]:
    cur = current_df.copy()
    for col in [
        "delta_mz",
        "overlap_proxy",
        "corridor_proxy",
        "rejection_proxy",
        "effective_leak_ratio",
        "stable_margin",
        "reject_margin",
        "leak_margin",
    ]:
        if col in cur.columns:
            cur[col] = pd.to_numeric(cur[col], errors="coerce")

    # width_scale from overlap = exp(-delta/width_scale)
    if {"delta_mz", "overlap_proxy"}.issubset(set(cur.columns)):
        good = cur[
            cur["delta_mz"].notna()
            & cur["overlap_proxy"].notna()
            & (cur["overlap_proxy"] > 0)
            & (cur["overlap_proxy"] < 1)
            & (cur["delta_mz"] > 0)
        ]
        width_vals = -good["delta_mz"] / np.log(good["overlap_proxy"])
        width_scale = float(width_vals.median()) if len(width_vals) else 1.0
    else:
        width_scale = 1.0

    corridor_vals = []
    if {"corridor_proxy", "stable_margin"}.issubset(set(cur.columns)):
        x = (cur["corridor_proxy"] - cur["stable_margin"]).dropna()
        corridor_vals.extend(x.tolist())
    corridor_min = float(np.median(corridor_vals)) if corridor_vals else 0.25

    reject_vals = []
    if {"rejection_proxy", "reject_margin"}.issubset(set(cur.columns)):
        x = (cur["rejection_proxy"] + cur["reject_margin"]).dropna()
        reject_vals.extend(x.tolist())
    reject_max = float(np.median(reject_vals)) if reject_vals else 0.75

    leak_vals = []
    if {"effective_leak_ratio", "leak_margin"}.issubset(set(cur.columns)):
        x = (cur["effective_leak_ratio"] + cur["leak_margin"]).dropna()
        leak_vals.extend(x.tolist())
    leak_ratio_max = float(np.median(leak_vals)) if leak_vals else 0.9

    if "sep_s0_used" in cur.columns:
        x = pd.to_numeric(cur["sep_s0_used"], errors="coerce").dropna()
        sep_s0 = float(x.median()) if len(x) else 0.1
    else:
        sep_s0 = 0.1

    return width_scale, corridor_min, reject_max, leak_ratio_max, sep_s0


def percentile_cut(values: Iterable[float], q: float) -> float:
    vals = [float(v) for v in values if math.isfinite(float(v))]
    if not vals:
        return 0.0
    if q <= 0:
        return min(vals)
    if q >= 1:
        return max(vals)
    vals_sorted = sorted(vals)
    idx = max(0, min(len(vals_sorted) - 1, math.ceil(q * len(vals_sorted)) - 1))
    return vals_sorted[idx]


def classify(corridor: float, rejection: float, leak_ratio: float, corridor_min: float, reject_max: float, leak_ratio_max: float) -> str:
    if corridor >= corridor_min and rejection <= reject_max and leak_ratio <= leak_ratio_max:
        return "STABLE-INTERMEDIATE-CANDIDATE"
    if corridor < corridor_min and rejection > reject_max:
        return "REPULSIVE"
    return "INCONCLUSIVE"


def build_track2_pairs(targets_rebuilt: pd.DataFrame) -> List[Dict[str, object]]:
    ordered = targets_rebuilt.sort_values("rebuilt_target_mz").reset_index(drop=True)
    rows: List[Dict[str, object]] = []
    n = len(ordered)
    for i in range(n - 1):
        a = ordered.iloc[i]
        b = ordered.iloc[i + 1]
        rows.append(
            {
                "pair_shell": "adjacent",
                "shell_offset": 1,
                "target_a": str(a["target_label"]),
                "target_b": str(b["target_label"]),
                "mz_a": float(a["rebuilt_target_mz"]),
                "mz_b": float(b["rebuilt_target_mz"]),
            }
        )
    for i in range(n - 2):
        a = ordered.iloc[i]
        b = ordered.iloc[i + 2]
        rows.append(
            {
                "pair_shell": "next_nearest",
                "shell_offset": 2,
                "target_a": str(a["target_label"]),
                "target_b": str(b["target_label"]),
                "mz_a": float(a["rebuilt_target_mz"]),
                "mz_b": float(b["rebuilt_target_mz"]),
            }
        )
    return rows


def add_repulsive_tiebreak(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    rep_mask = out["classification"] == "REPULSIVE"
    rep = out[rep_mask].copy()
    out["repulsive_delta_ref_median"] = np.nan
    out["repulsive_delta_over_median"] = np.nan
    out["repulsive_distance_rank_desc"] = np.nan
    out["repulsive_proximity_rank_asc"] = np.nan
    out["repulsive_geom_bucket"] = ""
    out["repulsive_tiebreak_active"] = 0
    if rep.empty:
        return out
    ref = float(rep["delta_mz"].median())
    rep = rep.sort_values(["delta_mz", "target_a", "target_b"], ascending=[False, True, True], kind="mergesort")
    rep["repulsive_distance_rank_desc"] = np.arange(1, len(rep) + 1)
    rep = rep.sort_values(["delta_mz", "target_a", "target_b"], ascending=[True, True, True], kind="mergesort")
    rep["repulsive_proximity_rank_asc"] = np.arange(1, len(rep) + 1)
    unique_count = rep["delta_mz"].nunique()

    def bucket(rank_asc: int) -> str:
        if unique_count <= 1:
            return "UNRESOLVED"
        if rank_asc <= max(1, unique_count // 3):
            return "NEAR_THRESHOLD"
        if rank_asc > max(1, (2 * unique_count) // 3):
            return "FAR_GEOMETRY"
        return "MID_REPULSIVE"

    rep["repulsive_delta_ref_median"] = ref
    rep["repulsive_delta_over_median"] = rep["delta_mz"] / ref if ref > 0 else np.nan
    rep["repulsive_geom_bucket"] = rep["repulsive_proximity_rank_asc"].astype(int).map(bucket)
    rep["repulsive_tiebreak_active"] = 1

    out.loc[rep.index, "repulsive_delta_ref_median"] = rep["repulsive_delta_ref_median"]
    out.loc[rep.index, "repulsive_delta_over_median"] = rep["repulsive_delta_over_median"]
    out.loc[rep.index, "repulsive_distance_rank_desc"] = rep["repulsive_distance_rank_desc"]
    out.loc[rep.index, "repulsive_proximity_rank_asc"] = rep["repulsive_proximity_rank_asc"]
    out.loc[rep.index, "repulsive_geom_bucket"] = rep["repulsive_geom_bucket"]
    out.loc[rep.index, "repulsive_tiebreak_active"] = rep["repulsive_tiebreak_active"]
    return out


def add_weakstable_tiebreak(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["weak_stable_delta_ref_median"] = np.nan
    out["weak_stable_delta_over_median"] = np.nan
    out["weak_stable_compactness_rank_asc"] = np.nan
    out["weak_stable_edge_rank_desc"] = np.nan
    out["weak_stable_geom_bucket"] = ""
    out["weak_stable_tiebreak_active"] = 0

    weak_mask = (out["classification"] == "STABLE-INTERMEDIATE-CANDIDATE") & (out["boundary_confidence"] == "WEAK_STABLE")
    weak = out[weak_mask].copy()
    if weak.empty:
        return out

    ref = float(weak["delta_mz"].median())
    weak["weak_stable_delta_ref_median"] = ref
    weak["weak_stable_delta_over_median"] = weak["delta_mz"] / ref if ref != 0 else np.nan
    weak["weak_stable_tiebreak_active"] = 1

    weak_edge = weak.sort_values(
        ["delta_mz", "stable_margin", "target_a", "target_b"],
        ascending=[False, True, True, True],
        kind="mergesort",
    ).copy()
    weak_edge["weak_stable_edge_rank_desc"] = np.arange(1, len(weak_edge) + 1)

    weak_comp = weak.sort_values(
        ["delta_mz", "stable_margin", "target_a", "target_b"],
        ascending=[True, False, True, True],
        kind="mergesort",
    ).copy()
    weak_comp["weak_stable_compactness_rank_asc"] = np.arange(1, len(weak_comp) + 1)

    unique_desc = sorted(set(float(x) for x in weak["delta_mz"].tolist()), reverse=True)

    def bucket(delta: float) -> str:
        if not unique_desc:
            return ""
        if len(unique_desc) == 1:
            return "MID_WEAK_STABLE"
        if math.isclose(delta, unique_desc[0], rel_tol=0.0, abs_tol=1e-12):
            return "NEAR_STABLE_EDGE"
        if math.isclose(delta, unique_desc[-1], rel_tol=0.0, abs_tol=1e-12):
            return "DEEP_WEAK_STABLE"
        return "MID_WEAK_STABLE"

    weak["weak_stable_geom_bucket"] = weak["delta_mz"].map(bucket)

    out.loc[weak.index, "weak_stable_delta_ref_median"] = weak["weak_stable_delta_ref_median"]
    out.loc[weak.index, "weak_stable_delta_over_median"] = weak["weak_stable_delta_over_median"]
    out.loc[weak.index, "weak_stable_geom_bucket"] = weak["weak_stable_geom_bucket"]
    out.loc[weak.index, "weak_stable_tiebreak_active"] = weak["weak_stable_tiebreak_active"]
    out.loc[weak_edge.index, "weak_stable_edge_rank_desc"] = weak_edge["weak_stable_edge_rank_desc"]
    out.loc[weak_comp.index, "weak_stable_compactness_rank_asc"] = weak_comp["weak_stable_compactness_rank_asc"]
    return out


def build_rebuilt_pairs(
    targets_all: pd.DataFrame,
    *,
    width_scale: float,
    corridor_min: float,
    reject_max: float,
    leak_ratio_max: float,
    sep_s0: float,
    confidence_quantile: float,
) -> pd.DataFrame:
    target_rows = []
    for _, row in targets_all.iterrows():
        rebuilt = float(row["rebuilt_mz_weighted"])
        nominal = float(row["target_mz_nominal"])
        if not math.isfinite(rebuilt):
            rebuilt = nominal
        target_rows.append({"target_label": row["target_label"], "rebuilt_target_mz": rebuilt, "target_mz_nominal": nominal})
    targets_df = pd.DataFrame(target_rows).drop_duplicates(subset=["target_label"]).reset_index(drop=True)

    pairs = build_track2_pairs(targets_df)
    rows: List[Dict[str, object]] = []
    for p in pairs:
        mz_a = float(p["mz_a"])
        mz_b = float(p["mz_b"])
        delta = abs(mz_b - mz_a)
        mean_mz = 0.5 * (mz_a + mz_b)
        overlap = math.exp(-delta / max(width_scale, 1e-12))
        corridor = overlap
        rejection = 1.0 - overlap
        leak_red = 0.5 * overlap
        leak_ratio = max(0.0, 1.0 - leak_red)
        stable_margin = corridor - corridor_min
        reject_margin = reject_max - rejection
        leak_margin = leak_ratio_max - leak_ratio
        nearest_stable = min(stable_margin, reject_margin, leak_margin)
        rep_corr_margin = corridor_min - corridor
        rep_rej_margin = rejection - reject_max
        rep_margin = min(rep_corr_margin, rep_rej_margin)
        stable_cap = max(min(1.0 - corridor_min, reject_max, leak_ratio_max), 1e-12)
        rep_cap = max(min(corridor_min, 1.0 - reject_max), 1e-12)
        stable_margin_norm = nearest_stable / stable_cap
        repulsive_margin_norm = rep_margin / rep_cap
        nearest_gap = min(abs(stable_margin), abs(reject_margin), abs(leak_margin))
        sep_norm = delta / (delta + max(sep_s0, 1e-12))
        klass = classify(corridor, rejection, leak_ratio, corridor_min, reject_max, leak_ratio_max)
        rows.append(
            {
                "pair_shell": p["pair_shell"],
                "shell_offset": p["shell_offset"],
                "target_a": p["target_a"],
                "target_b": p["target_b"],
                "mz_a": mz_a,
                "mz_b": mz_b,
                "delta_mz": delta,
                "mean_mz": mean_mz,
                "overlap_proxy": overlap,
                "corridor_proxy": corridor,
                "rejection_proxy": rejection,
                "leak_reduction_proxy": leak_red,
                "effective_leak_ratio": leak_ratio,
                "sep_s0_used": sep_s0,
                "sep_norm": sep_norm,
                "stable_margin": stable_margin,
                "reject_margin": reject_margin,
                "leak_margin": leak_margin,
                "nearest_stable_boundary_margin": nearest_stable,
                "stable_margin_norm": stable_margin_norm,
                "repulsive_corridor_margin": rep_corr_margin,
                "repulsive_reject_margin": rep_rej_margin,
                "repulsive_margin": rep_margin,
                "repulsive_margin_norm": repulsive_margin_norm,
                "nearest_threshold_gap": nearest_gap,
                "classification": klass,
                "boundary_confidence": "BORDERLINE",
            }
        )

    out = pd.DataFrame(rows)
    stable_vals = out.loc[out["classification"] == "STABLE-INTERMEDIATE-CANDIDATE", "nearest_stable_boundary_margin"].tolist()
    rep_vals = out.loc[out["classification"] == "REPULSIVE", "repulsive_margin"].tolist()
    weak_stable_cut = percentile_cut(stable_vals, confidence_quantile)
    strong_rep_cut = percentile_cut(rep_vals, 1.0 - confidence_quantile)

    for idx, row in out.iterrows():
        if row["classification"] == "STABLE-INTERMEDIATE-CANDIDATE":
            out.at[idx, "boundary_confidence"] = "WEAK_STABLE" if row["nearest_stable_boundary_margin"] <= weak_stable_cut else "STRONG_STABLE"
        elif row["classification"] == "REPULSIVE":
            out.at[idx, "boundary_confidence"] = "STRONG_REPULSIVE" if row["repulsive_margin"] >= strong_rep_cut else "BORDERLINE"
        else:
            out.at[idx, "boundary_confidence"] = "BORDERLINE"

    out = add_repulsive_tiebreak(out)
    out = add_weakstable_tiebreak(out)
    return out


def build_comparison(current: pd.DataFrame, rebuilt: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["pair_shell", "target_a", "target_b"]
    keep_current = [
        "pair_shell",
        "target_a",
        "target_b",
        "shell_offset",
        "classification",
        "boundary_confidence",
        "mz_a",
        "mz_b",
        "delta_mz",
        "corridor_proxy",
        "rejection_proxy",
        "effective_leak_ratio",
    ]
    for c in keep_current:
        if c not in current.columns:
            current[c] = np.nan
        if c not in rebuilt.columns:
            rebuilt[c] = np.nan

    cur = current[keep_current].copy()
    reb = rebuilt[keep_current].copy()
    merged = cur.merge(reb, on=key_cols, how="outer", suffixes=("_current", "_rebuilt"), indicator=True)
    merged["pair_presence"] = merged["_merge"].map({"both": "matched", "left_only": "only_current", "right_only": "only_rebuilt"})

    matched_mask = merged["_merge"] == "both"
    merged["classification_changed"] = False
    merged["boundary_confidence_changed"] = False
    merged.loc[matched_mask, "classification_changed"] = (
        merged.loc[matched_mask, "classification_current"].astype(str) != merged.loc[matched_mask, "classification_rebuilt"].astype(str)
    )
    merged.loc[matched_mask, "boundary_confidence_changed"] = (
        merged.loc[matched_mask, "boundary_confidence_current"].astype(str) != merged.loc[matched_mask, "boundary_confidence_rebuilt"].astype(str)
    )

    numeric_cols = ["mz_a", "mz_b", "delta_mz", "corridor_proxy", "rejection_proxy", "effective_leak_ratio"]
    for c in numeric_cols:
        c_cur = f"{c}_current"
        c_reb = f"{c}_rebuilt"
        merged[c_cur] = pd.to_numeric(merged[c_cur], errors="coerce")
        merged[c_reb] = pd.to_numeric(merged[c_reb], errors="coerce")
        merged[f"{c}_diff"] = merged[c_reb] - merged[c_cur]
        merged[f"{c}_abs_diff"] = (merged[c_reb] - merged[c_cur]).abs()

    return merged.drop(columns=["_merge"])


def write_verdict(
    path: Path,
    *,
    inputs_used: List[Path],
    targets_csv: Path,
    current_csv: Path,
    windows_csv: Path,
    rebuilt_csv: Path,
    comparison_csv: Path,
    thresholds: Tuple[float, float, float, float, float],
    comparison_df: pd.DataFrame,
) -> None:
    width_scale, corridor_min, reject_max, leak_ratio_max, sep_s0 = thresholds
    matched = comparison_df[comparison_df["pair_presence"] == "matched"].copy()
    only_current = int((comparison_df["pair_presence"] == "only_current").sum())
    only_rebuilt = int((comparison_df["pair_presence"] == "only_rebuilt").sum())
    cls_changes = int(matched["classification_changed"].sum()) if not matched.empty else 0
    bc_changes = int(matched["boundary_confidence_changed"].sum()) if not matched.empty else 0
    max_delta = float(matched["delta_mz_abs_diff"].max()) if "delta_mz_abs_diff" in matched.columns and not matched.empty else float("nan")
    max_corr = float(matched["corridor_proxy_abs_diff"].max()) if "corridor_proxy_abs_diff" in matched.columns and not matched.empty else float("nan")

    if only_current == 0 and only_rebuilt == 0 and cls_changes == 0:
        verdict = "PASS-DIAGNOSTIC-REBUILD"
    elif cls_changes == 0:
        verdict = "PASS-WITH-PAIR-DRIFT"
    else:
        verdict = "SPLIT-DIAGNOSTIC-REBUILD"

    lines: List[str] = []
    lines.append("# Two-Center Diagnostic Rebuild Verdict")
    lines.append("")
    lines.append("## Inputs")
    lines.append(f"- targets_csv: `{targets_csv}`")
    for p in inputs_used:
        lines.append(f"- raw_points: `{p}`")
    lines.append(f"- current_two_center_csv: `{current_csv}`")
    lines.append("")
    lines.append("## Frozen Base Logic")
    lines.append("- fitting: none")
    lines.append("- pair discipline: adjacent + next_nearest")
    lines.append("- label logic: preserved (corridor/reject/leak thresholding)")
    lines.append(f"- inferred width_scale: `{width_scale:.12g}`")
    lines.append(f"- inferred corridor_min: `{corridor_min:.12g}`")
    lines.append(f"- inferred reject_max: `{reject_max:.12g}`")
    lines.append(f"- inferred leak_ratio_max: `{leak_ratio_max:.12g}`")
    lines.append(f"- inferred sep_s0: `{sep_s0:.12g}`")
    lines.append("")
    lines.append("## Comparison Summary")
    lines.append(f"- matched_pairs: **{len(matched)}**")
    lines.append(f"- only_current_pairs: **{only_current}**")
    lines.append(f"- only_rebuilt_pairs: **{only_rebuilt}**")
    lines.append(f"- classification_changes: **{cls_changes}**")
    lines.append(f"- boundary_confidence_changes: **{bc_changes}**")
    if math.isfinite(max_delta):
        lines.append(f"- max_abs_delta_mz_diff: **{max_delta:.12g}**")
    if math.isfinite(max_corr):
        lines.append(f"- max_abs_corridor_proxy_diff: **{max_corr:.12g}**")
    lines.append("")
    lines.append("## Artifacts")
    lines.append(f"- rebuilt_target_windows_csv: `{windows_csv}`")
    lines.append(f"- rebuilt_pair_csv: `{rebuilt_csv}`")
    lines.append(f"- comparison_csv: `{comparison_csv}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append(f"- **{verdict}**")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Rebuild two-center pair diagnostics from raw points and compare with current layer.")
    ap.add_argument("--targets_csv", required=True)
    ap.add_argument("--current_two_center_csv", required=True)
    ap.add_argument("--raw_points", nargs="+", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--confidence_quantile", type=float, default=0.25)
    args = ap.parse_args()

    targets_csv = Path(args.targets_csv).resolve()
    current_csv = Path(args.current_two_center_csv).resolve()
    raw_paths = [Path(p).resolve() for p in args.raw_points]
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = read_targets(targets_csv)
    point_frames = []
    for p in raw_paths:
        point_frames.append(read_points(p, p.stem))
    points_all = pd.concat(point_frames, ignore_index=True)

    target_windows = build_target_windows(targets, points_all)
    windows_csv = out_dir / "rebuilt_target_windows.csv"
    target_windows.to_csv(windows_csv, index=False)

    all_targets = target_windows[target_windows["source"] == "ALL"].copy()
    current_df = pd.read_csv(current_csv)
    thresholds = infer_thresholds(current_df)

    rebuilt_pairs = build_rebuilt_pairs(
        all_targets,
        width_scale=thresholds[0],
        corridor_min=thresholds[1],
        reject_max=thresholds[2],
        leak_ratio_max=thresholds[3],
        sep_s0=thresholds[4],
        confidence_quantile=float(args.confidence_quantile),
    )

    rebuilt_csv = out_dir / "rebuilt_two_center_pair_metrics.csv"
    rebuilt_pairs.to_csv(rebuilt_csv, index=False)

    comparison_df = build_comparison(current_df, rebuilt_pairs)
    comparison_csv = out_dir / "rebuilt_vs_current_comparison.csv"
    comparison_df.to_csv(comparison_csv, index=False)

    verdict_md = out_dir / "rebuilt_two_center_verdict.md"
    write_verdict(
        verdict_md,
        inputs_used=raw_paths,
        targets_csv=targets_csv,
        current_csv=current_csv,
        windows_csv=windows_csv,
        rebuilt_csv=rebuilt_csv,
        comparison_csv=comparison_csv,
        thresholds=thresholds,
        comparison_df=comparison_df,
    )

    print("=== REBUILD COMPLETE ===")
    print(f"targets_csv={targets_csv}")
    for p in raw_paths:
        print(f"raw_points={p}")
    print(f"current_two_center_csv={current_csv}")
    print(f"out_windows_csv={windows_csv}")
    print(f"out_rebuilt_pair_csv={rebuilt_csv}")
    print(f"out_comparison_csv={comparison_csv}")
    print(f"out_verdict_md={verdict_md}")
    print(
        "inferred_params="
        f"width_scale:{thresholds[0]:.12g},"
        f"corridor_min:{thresholds[1]:.12g},"
        f"reject_max:{thresholds[2]:.12g},"
        f"leak_ratio_max:{thresholds[3]:.12g},"
        f"sep_s0:{thresholds[4]:.12g}"
    )


if __name__ == "__main__":
    main()
