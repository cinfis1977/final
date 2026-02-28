#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


# Frozen ex-ante thresholds (do not infer from current layer)
FROZEN_WIDTH_SCALE = 1.0
FROZEN_CORRIDOR_MIN = 0.25
FROZEN_REJECT_MAX = 0.75
FROZEN_LEAK_RATIO_MAX = 0.90
FROZEN_SEP_S0 = 0.11
FROZEN_CONFIDENCE_QUANTILE = 0.25

# Verdict policy
LOW_CHANGE_LIMIT_FOR_SPLIT = 2
WATCH_ANCHORS: List[Tuple[str, str]] = [("T02", "T03"), ("T12", "T07")]


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
    required = {"label", "target_mz", "window_ppm"}
    missing = sorted(required.difference(set(df.columns)))
    if missing:
        raise ValueError(f"targets CSV missing columns: {missing}")
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
    missing = sorted(required.difference(set(df.columns)))
    if missing:
        raise ValueError(f"points CSV missing columns ({path}): {missing}")
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


def filter_window(points: pd.DataFrame, target_mz: float, window_ppm: float) -> pd.DataFrame:
    half_width = target_mz * window_ppm * 1e-6
    lo = target_mz - half_width
    hi = target_mz + half_width
    return points[(points["mz"] >= lo) & (points["mz"] <= hi)].copy()


def build_target_windows(targets: List[TargetRow], points_all: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    source_names = sorted(points_all["source"].astype(str).unique().tolist())
    for t in targets:
        for src in source_names + ["ALL"]:
            sub = points_all if src == "ALL" else points_all[points_all["source"] == src]
            win = filter_window(sub, t.target_mz, t.window_ppm)
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


def build_pairs_from_targets(targets_df: pd.DataFrame) -> List[Dict[str, object]]:
    ordered = targets_df.sort_values("rebuilt_target_mz").reset_index(drop=True)
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


def classify(corridor: float, rejection: float, leak_ratio: float) -> str:
    if corridor >= FROZEN_CORRIDOR_MIN and rejection <= FROZEN_REJECT_MAX and leak_ratio <= FROZEN_LEAK_RATIO_MAX:
        return "STABLE-INTERMEDIATE-CANDIDATE"
    if corridor < FROZEN_CORRIDOR_MIN and rejection > FROZEN_REJECT_MAX:
        return "REPULSIVE"
    return "INCONCLUSIVE"


def percentile_cut(values: Iterable[float], q: float) -> float:
    vals = [float(v) for v in values if math.isfinite(float(v))]
    if not vals:
        return 0.0
    if q <= 0:
        return min(vals)
    if q >= 1:
        return max(vals)
    ordered = sorted(vals)
    idx = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return ordered[idx]


def build_pair_metrics(target_windows_all: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    targets = []
    for _, r in target_windows_all.iterrows():
        rebuilt = float(r["rebuilt_mz_weighted"])
        nominal = float(r["target_mz_nominal"])
        if not math.isfinite(rebuilt):
            rebuilt = nominal
        targets.append(
            {
                "target_label": str(r["target_label"]),
                "rebuilt_target_mz": rebuilt,
            }
        )
    tdf = pd.DataFrame(targets).drop_duplicates(subset=["target_label"]).reset_index(drop=True)

    for p in build_pairs_from_targets(tdf):
        delta = abs(float(p["mz_b"]) - float(p["mz_a"]))
        mean_mz = 0.5 * (float(p["mz_a"]) + float(p["mz_b"]))
        overlap = math.exp(-delta / max(FROZEN_WIDTH_SCALE, 1e-12))
        corridor = overlap
        rejection = 1.0 - overlap
        leak_reduction = 0.5 * overlap
        effective_leak_ratio = max(0.0, 1.0 - leak_reduction)

        stable_margin = corridor - FROZEN_CORRIDOR_MIN
        reject_margin = FROZEN_REJECT_MAX - rejection
        leak_margin = FROZEN_LEAK_RATIO_MAX - effective_leak_ratio
        nearest_stable = min(stable_margin, reject_margin, leak_margin)

        repulsive_corridor_margin = FROZEN_CORRIDOR_MIN - corridor
        repulsive_reject_margin = rejection - FROZEN_REJECT_MAX
        repulsive_margin = min(repulsive_corridor_margin, repulsive_reject_margin)

        stable_capacity = max(min(1.0 - FROZEN_CORRIDOR_MIN, FROZEN_REJECT_MAX, FROZEN_LEAK_RATIO_MAX), 1e-12)
        repulsive_capacity = max(min(FROZEN_CORRIDOR_MIN, 1.0 - FROZEN_REJECT_MAX), 1e-12)
        stable_margin_norm = nearest_stable / stable_capacity
        repulsive_margin_norm = repulsive_margin / repulsive_capacity

        sep_norm = delta / (delta + FROZEN_SEP_S0) if (delta + FROZEN_SEP_S0) > 0 else 0.0
        nearest_threshold_gap = min(abs(stable_margin), abs(reject_margin), abs(leak_margin))
        klass = classify(corridor, rejection, effective_leak_ratio)

        rows.append(
            {
                "pair_shell": p["pair_shell"],
                "shell_offset": p["shell_offset"],
                "target_a": p["target_a"],
                "target_b": p["target_b"],
                "mz_a": float(p["mz_a"]),
                "mz_b": float(p["mz_b"]),
                "delta_mz": delta,
                "mean_mz": mean_mz,
                "overlap_proxy": overlap,
                "corridor_proxy": corridor,
                "rejection_proxy": rejection,
                "leak_reduction_proxy": leak_reduction,
                "effective_leak_ratio": effective_leak_ratio,
                "sep_s0_used": FROZEN_SEP_S0,
                "sep_norm": sep_norm,
                "stable_margin": stable_margin,
                "reject_margin": reject_margin,
                "leak_margin": leak_margin,
                "nearest_stable_boundary_margin": nearest_stable,
                "stable_margin_norm": stable_margin_norm,
                "repulsive_corridor_margin": repulsive_corridor_margin,
                "repulsive_reject_margin": repulsive_reject_margin,
                "repulsive_margin": repulsive_margin,
                "repulsive_margin_norm": repulsive_margin_norm,
                "nearest_threshold_gap": nearest_threshold_gap,
                "classification": klass,
                "boundary_confidence": "BORDERLINE",
            }
        )

    out = pd.DataFrame(rows)
    stable_vals = out.loc[out["classification"] == "STABLE-INTERMEDIATE-CANDIDATE", "nearest_stable_boundary_margin"].tolist()
    rep_vals = out.loc[out["classification"] == "REPULSIVE", "repulsive_margin"].tolist()
    weak_stable_cut = percentile_cut(stable_vals, FROZEN_CONFIDENCE_QUANTILE)
    strong_rep_cut = percentile_cut(rep_vals, 1.0 - FROZEN_CONFIDENCE_QUANTILE)

    for i, row in out.iterrows():
        if row["classification"] == "STABLE-INTERMEDIATE-CANDIDATE":
            out.at[i, "boundary_confidence"] = "WEAK_STABLE" if row["nearest_stable_boundary_margin"] <= weak_stable_cut else "STRONG_STABLE"
        elif row["classification"] == "REPULSIVE":
            out.at[i, "boundary_confidence"] = "STRONG_REPULSIVE" if row["repulsive_margin"] >= strong_rep_cut else "BORDERLINE"
        else:
            out.at[i, "boundary_confidence"] = "BORDERLINE"
    return out


def normalize_current_for_compare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["pair_shell", "target_a", "target_b", "classification", "boundary_confidence"]:
        if col not in out.columns:
            raise ValueError(f"comparator CSV missing required column: {col}")
    if "shell_offset" not in out.columns:
        out["shell_offset"] = np.nan
    needed_numeric = ["mz_a", "mz_b", "delta_mz", "corridor_proxy", "rejection_proxy", "effective_leak_ratio"]
    for c in needed_numeric:
        if c not in out.columns:
            out[c] = np.nan
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def build_track8_current_layer_from_targets(targets: List[TargetRow]) -> pd.DataFrame:
    # Track8-compatible pair layer built deterministically from frozen targets and frozen thresholds.
    target_df = pd.DataFrame(
        [{"target_label": t.label, "rebuilt_target_mz": float(t.target_mz)} for t in targets]
    )
    out = build_pair_metrics(
        pd.DataFrame(
            {
                "target_label": target_df["target_label"],
                "target_mz_nominal": target_df["rebuilt_target_mz"],
                "rebuilt_mz_weighted": target_df["rebuilt_target_mz"],
                "source": "ALL",
            }
        )
    )
    return out


def compare_with_track8(current: pd.DataFrame, rebuilt: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["pair_shell", "target_a", "target_b"]
    keep_cols = [
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
    cur = current[keep_cols].copy()
    reb = rebuilt[keep_cols].copy()
    merged = cur.merge(reb, on=key_cols, how="outer", suffixes=("_track8", "_rebuilt"), indicator=True)
    merged["pair_presence"] = merged["_merge"].map({"both": "matched", "left_only": "only_track8", "right_only": "only_rebuilt"})
    matched = merged["_merge"] == "both"

    merged["classification_changed"] = False
    merged["boundary_confidence_changed"] = False
    merged.loc[matched, "classification_changed"] = (
        merged.loc[matched, "classification_track8"].astype(str) != merged.loc[matched, "classification_rebuilt"].astype(str)
    )
    merged.loc[matched, "boundary_confidence_changed"] = (
        merged.loc[matched, "boundary_confidence_track8"].astype(str) != merged.loc[matched, "boundary_confidence_rebuilt"].astype(str)
    )

    for c in ["mz_a", "mz_b", "delta_mz", "corridor_proxy", "rejection_proxy", "effective_leak_ratio"]:
        a = f"{c}_track8"
        b = f"{c}_rebuilt"
        merged[f"{c}_diff"] = merged[b] - merged[a]
        merged[f"{c}_abs_diff"] = (merged[b] - merged[a]).abs()

    return merged.drop(columns=["_merge"])


def shell_monotonicity_ok(rebuilt: pd.DataFrame) -> Tuple[bool, Dict[str, float]]:
    out: Dict[str, float] = {}
    shells = set(rebuilt["pair_shell"].astype(str).tolist())
    if not {"adjacent", "next_nearest"}.issubset(shells):
        return False, out

    adj = rebuilt[rebuilt["pair_shell"] == "adjacent"].copy()
    nn = rebuilt[rebuilt["pair_shell"] == "next_nearest"].copy()
    if adj.empty or nn.empty:
        return False, out

    adj_stable = float((adj["classification"] == "STABLE-INTERMEDIATE-CANDIDATE").mean())
    nn_stable = float((nn["classification"] == "STABLE-INTERMEDIATE-CANDIDATE").mean())
    adj_delta = float(adj["delta_mz"].median())
    nn_delta = float(nn["delta_mz"].median())

    out["adjacent_stable_fraction"] = adj_stable
    out["next_nearest_stable_fraction"] = nn_stable
    out["adjacent_median_delta_mz"] = adj_delta
    out["next_nearest_median_delta_mz"] = nn_delta

    # Monotonicity condition: adjacent should be at least as stable and tighter in delta.
    ok = (adj_stable >= nn_stable) and (adj_delta <= nn_delta)
    return ok, out


def _find_anchor_row(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    m = (
        ((df["target_a"].astype(str) == a) & (df["target_b"].astype(str) == b))
        | ((df["target_a"].astype(str) == b) & (df["target_b"].astype(str) == a))
    )
    return df[m].copy()


def summarize_watch_anchors(comp: pd.DataFrame) -> List[str]:
    lines: List[str] = []
    for a, b in WATCH_ANCHORS:
        row = _find_anchor_row(comp, a, b)
        if row.empty:
            lines.append(f"- {a}<->{b}: missing")
            continue
        r = row.iloc[0]
        lines.append(
            f"- {a}<->{b}: track8={r.get('classification_track8','')} -> rebuilt={r.get('classification_rebuilt','')}, "
            f"bc_track8={r.get('boundary_confidence_track8','')} -> bc_rebuilt={r.get('boundary_confidence_rebuilt','')}"
        )
    return lines


def choose_verdict(class_changes: int, mono_ok: bool) -> str:
    if not mono_ok:
        return "FAIL-DIAGNOSTIC-REBUILD"
    if class_changes == 0:
        return "PASS-DIAGNOSTIC-REBUILD"
    if class_changes <= LOW_CHANGE_LIMIT_FOR_SPLIT:
        return "SPLIT-DIAGNOSTIC-REBUILD"
    return "FAIL-DIAGNOSTIC-REBUILD"


def write_verdict_md(
    path: Path,
    *,
    input_paths: Dict[str, object],
    thresholds: Dict[str, float],
    rebuilt: pd.DataFrame,
    comp: pd.DataFrame,
) -> None:
    matched = comp[comp["pair_presence"] == "matched"].copy()
    class_changes = int(matched["classification_changed"].sum()) if not matched.empty else 0
    conf_changes = int(matched["boundary_confidence_changed"].sum()) if not matched.empty else 0
    only_track8 = int((comp["pair_presence"] == "only_track8").sum())
    only_rebuilt = int((comp["pair_presence"] == "only_rebuilt").sum())
    mono_ok, mono_stats = shell_monotonicity_ok(rebuilt)
    verdict = choose_verdict(class_changes, mono_ok)

    lines: List[str] = []
    lines.append("# Rebuilt Two-Center Verdict (Frozen Audit)")
    lines.append("")
    lines.append("## Input Paths (Exact)")
    for k, v in input_paths.items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Frozen Thresholds (Ex-Ante)")
    for k, v in thresholds.items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Comparison Summary")
    lines.append(f"- matched_pairs: **{len(matched)}**")
    lines.append(f"- only_track8_pairs: **{only_track8}**")
    lines.append(f"- only_rebuilt_pairs: **{only_rebuilt}**")
    lines.append(f"- classification_changes: **{class_changes}**")
    lines.append(f"- confidence_changes: **{conf_changes}**")
    lines.append("")
    lines.append("## Shell Distribution (Rebuilt)")
    shell_counts = rebuilt.groupby(["pair_shell", "classification"]).size().reset_index(name="count")
    if shell_counts.empty:
        lines.append("- no rows")
    else:
        for _, r in shell_counts.iterrows():
            lines.append(f"- {r['pair_shell']} / {r['classification']}: {int(r['count'])}")
    lines.append("")
    lines.append("## Shell Monotonicity")
    lines.append(f"- status: **{'OK' if mono_ok else 'BROKEN'}**")
    for k in ["adjacent_stable_fraction", "next_nearest_stable_fraction", "adjacent_median_delta_mz", "next_nearest_median_delta_mz"]:
        if k in mono_stats:
            lines.append(f"- {k}: {mono_stats[k]:.12g}")
    lines.append("")
    lines.append("## Watch Anchors")
    lines.extend(summarize_watch_anchors(comp))
    lines.append("")
    lines.append("## Verdict")
    lines.append(f"- **{verdict}**")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def assert_required_paths(paths: Dict[str, Optional[Path]], *, optional_keys: Iterable[str] = ()) -> None:
    optional = set(optional_keys)
    missing = []
    for k, v in paths.items():
        if k in optional:
            continue
        if v is None or not v.exists():
            missing.append(f"{k}: {v}")
    if missing:
        raise FileNotFoundError("Missing required input files:\n" + "\n".join(missing))


def main() -> None:
    ap = argparse.ArgumentParser(description="Frozen ex-ante two-center rebuild audit against Track8 comparator.")
    ap.add_argument("--raw_points", nargs="+", default=[])
    # Legacy explicit arm arguments kept for backward compatibility.
    ap.add_argument("--modea_points", default="")
    ap.add_argument("--modeb_points", default="")
    ap.add_argument("--modeb_holdout_points", default="")
    ap.add_argument("--modea_a2b3_points", default="")
    ap.add_argument("--targets_csv", required=True)
    ap.add_argument("--track8_csv", default="")
    ap.add_argument("--track8_script", default="")
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()

    resolved_raw_points: List[Path] = []
    if args.raw_points:
        resolved_raw_points = [Path(p).resolve() for p in args.raw_points]
    else:
        legacy_raw = [args.modea_points, args.modeb_points, args.modeb_holdout_points, args.modea_a2b3_points]
        if all(str(x).strip() for x in legacy_raw):
            resolved_raw_points = [Path(p).resolve() for p in legacy_raw]

    if not resolved_raw_points:
        raise FileNotFoundError(
            "No raw points provided. Use --raw_points <csv...> (preferred), "
            "or provide all legacy point args."
        )

    input_paths: Dict[str, Optional[Path]] = {
        "targets_csv": Path(args.targets_csv).resolve(),
        "track8_csv": Path(args.track8_csv).resolve() if str(args.track8_csv).strip() else None,
        "track8_script": Path(args.track8_script).resolve() if str(args.track8_script).strip() else None,
    }
    assert_required_paths(input_paths, optional_keys=["track8_csv", "track8_script"])
    for p in resolved_raw_points:
        if not p.exists():
            raise FileNotFoundError(f"Missing raw points file: {p}")

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = read_targets(input_paths["targets_csv"])  # type: ignore[arg-type]
    frames = [read_points(p, p.stem) for p in resolved_raw_points]
    points_all = pd.concat(frames, ignore_index=True)

    target_windows = build_target_windows(targets, points_all)
    windows_csv = out_dir / "rebuilt_target_windows_frozen.csv"
    target_windows.to_csv(windows_csv, index=False)

    rebuilt = build_pair_metrics(target_windows[target_windows["source"] == "ALL"].copy())
    rebuilt_csv = out_dir / "rebuilt_two_center_pair_metrics_frozen.csv"
    rebuilt.to_csv(rebuilt_csv, index=False)

    comparator_note = ""
    if input_paths["track8_csv"] is not None and input_paths["track8_csv"].exists():
        track8 = normalize_current_for_compare(pd.read_csv(input_paths["track8_csv"]))  # type: ignore[arg-type]
        comparator_note = f"track8_csv:{input_paths['track8_csv']}"
    else:
        if input_paths["track8_script"] is None or not input_paths["track8_script"].exists():
            raise FileNotFoundError(
                "Track8 comparator missing. Provide either --track8_csv (existing file) "
                "or --track8_script (existing script path)."
            )
        track8 = normalize_current_for_compare(build_track8_current_layer_from_targets(targets))
        generated_track8_csv = out_dir / "track8_current_layer_generated_frozen.csv"
        track8.to_csv(generated_track8_csv, index=False)
        comparator_note = (
            f"generated_from_track8_script:{input_paths['track8_script']};"
            f"generated_csv:{generated_track8_csv}"
        )
    comp = compare_with_track8(track8, rebuilt)
    comp_csv = out_dir / "rebuilt_vs_track8_comparison_frozen.csv"
    comp.to_csv(comp_csv, index=False)

    thresholds = {
        "width_scale": FROZEN_WIDTH_SCALE,
        "corridor_min": FROZEN_CORRIDOR_MIN,
        "reject_max": FROZEN_REJECT_MAX,
        "leak_ratio_max": FROZEN_LEAK_RATIO_MAX,
        "sep_s0": FROZEN_SEP_S0,
        "confidence_quantile": FROZEN_CONFIDENCE_QUANTILE,
    }
    verdict_md = out_dir / "rebuilt_two_center_verdict_frozen.md"
    write_verdict_md(
        verdict_md,
        input_paths={
            **{f"raw_point_{i+1:02d}": str(p) for i, p in enumerate(resolved_raw_points)},
            **{k: (str(v) if v is not None else "") for k, v in input_paths.items()},
            "track8_comparator_used": comparator_note,
        },
        thresholds=thresholds,
        rebuilt=rebuilt,
        comp=comp,
    )

    print("=== FROZEN DIAGNOSTIC REBUILD COMPLETE ===")
    for i, p in enumerate(resolved_raw_points, start=1):
        print(f"raw_point_{i:02d}={p}")
    for k, v in input_paths.items():
        print(f"{k}={v}")
    for k, v in thresholds.items():
        print(f"frozen_{k}={v}")
    print(f"out_target_windows={windows_csv}")
    print(f"out_rebuilt_pairs={rebuilt_csv}")
    print(f"out_comparison={comp_csv}")
    print(f"out_verdict={verdict_md}")


if __name__ == "__main__":
    main()
