#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ms_particle_specific_dynamic_runner_v1_0_DROPIN.py

Mass Spectrometry (MS) scan-series runner that enforces an explicit
Raw → State → Dynamics → Observables chain.

This is a *drop-in* companion to `multi_target_particle_specific_v1_0_occgate_v1_PREPAPER.py`:
- It consumes the same peaks/points CSV contract: (scan, mz, intensity), with multiple settings.
- It produces the same key legacy artifacts expected by the prereg finalizer:
    - anchors.json
    - targets_used.csv
    - targets_summary.csv
    - alltargets_bin_success_width_stats.csv
    - alltargets_delta_success_width_pairs.csv

In addition, it writes integrity telemetry showing that a stateful dynamics step ran:
  - ms_dynamic_telemetry.json
  - scan_state.csv

Ablations:
  - INTERNAL_ONLY: stateful drift dynamics with fixed gain (no thread/env modulation)
  - THREAD_ONLY: per-scan drift estimate (no state carry; no dynamics)
  - FULL: stateful drift dynamics with thread/env modulation via g(TIC)

Design goal: prevent “proxy/overlay good score” shortcuts by (a) requiring scan-series
input, (b) computing target shifts from raw peaks, and (c) making state evolution explicit
and auditable at the scan level.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


def die(msg: str) -> None:
    raise SystemExit(f"[FATAL] {msg}")


def read_table(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        die(f"Input not found: {path}")
    opener = gzip.open if path.lower().endswith(".gz") else open
    with opener(path, "rb") as f:
        head = f.readline(20000)
    line = head.decode("utf-8-sig", errors="ignore")
    counts = {",": line.count(","), "\t": line.count("\t"), ";": line.count(";")}
    sep = max(counts, key=lambda k: counts[k])
    if counts[sep] == 0:
        sep = ","
    return pd.read_csv(path, sep=sep, engine="python")


def to_num(s: pd.Series, name: str) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    if x.notna().sum() == 0:
        die(f"Column '{name}' not numeric (all NaN).")
    return x


def mad(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if x.size == 0:
        return float("nan")
    m = np.median(x)
    return float(np.median(np.abs(x - m)))


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    m = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(m):
        return float("nan")
    v = values[m]
    w = weights[m]
    order = np.argsort(v)
    v = v[order]
    w = w[order]
    cw = np.cumsum(w)
    cutoff = 0.5 * float(cw[-1])
    idx = int(np.searchsorted(cw, cutoff, side="left"))
    return float(v[min(idx, len(v) - 1)])


def compute_g_from_tic(tic: pd.Series, qlo: float, qhi: float) -> Tuple[pd.Series, Dict]:
    lo = float(np.nanquantile(tic.to_numpy(dtype=float), qlo))
    hi = float(np.nanquantile(tic.to_numpy(dtype=float), qhi))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        die(f"Bad TIC anchors: lo={lo}, hi={hi}.")
    g = (tic - lo) / (hi - lo)
    g = g.clip(0.0, 1.0)
    meta = {"qlo": qlo, "qhi": qhi, "tic_lo": lo, "tic_hi": hi}
    return g, meta


def label_from_filename(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem


def build_balanced_bins(df_sorted: pd.DataFrame, min_n: int, max_bins: int) -> List[Tuple[int, int]]:
    settings = sorted(df_sorted["setting"].unique().tolist())
    if len(settings) < 2:
        die(f"Need at least 2 settings; found: {settings}")
    N = len(df_sorted)
    pos: Dict[str, np.ndarray] = {s: np.flatnonzero(df_sorted["setting"].to_numpy() == s) for s in settings}

    bins: List[Tuple[int, int]] = []
    i = 0
    while i < N and len(bins) < max_bins:
        ends: List[int] = []
        for s in settings:
            p = pos[s]
            j = np.searchsorted(p, i, side="left")
            k = j + (min_n - 1)
            if k >= p.size:
                ends = []
                break
            ends.append(int(p[k]))
        if not ends:
            break
        end = max(ends)
        bins.append((i, end))
        i = end + 1

    if not bins:
        die("Could not form bins (min_n too high or not enough data).")

    if i < N:
        bins[-1] = (bins[-1][0], N - 1)

    # validate; merge invalid into previous
    good: List[Tuple[int, int]] = []
    for a, b in bins:
        sub = df_sorted.iloc[a : b + 1]
        ok = all(int((sub["setting"] == s).sum()) >= min_n for s in settings)
        if ok:
            good.append((a, b))
        else:
            if good:
                good[-1] = (good[-1][0], b)
            else:
                die("First bin invalid. Lower min_n.")

    for a, b in good:
        sub = df_sorted.iloc[a : b + 1]
        if not all(int((sub["setting"] == s).sum()) >= min_n for s in settings):
            die("Bin validation failed. Lower min_n.")
    return good


def auto_targets_from_points(
    df: pd.DataFrame,
    topk: int,
    mz_round: float,
    min_presence_frac: float,
    min_intensity: float,
    window_ppm: float,
) -> pd.DataFrame:
    if topk < 1:
        die("--auto_targets_topk must be >=1")
    d = df.copy()
    d = d[d["intensity"] >= float(min_intensity)]
    d["mz_r"] = (d["mz"] / mz_round).round().astype("int64") * mz_round

    lines = d.groupby(["setting", "scan", "mz_r"], as_index=False)["intensity"].max()
    scan_counts = d.groupby("setting")["scan"].nunique().to_dict()
    pres = lines.groupby(["setting", "mz_r"])["scan"].nunique().reset_index(name="n_scans_present")
    pres["n_scans_total"] = pres["setting"].map(scan_counts)
    pres["presence_frac"] = pres["n_scans_present"] / pres["n_scans_total"]

    settings = sorted(d["setting"].unique().tolist())
    keep: set[float] | None = None
    for s in settings:
        good = set(
            pres[(pres["setting"] == s) & (pres["presence_frac"] >= min_presence_frac)]["mz_r"].tolist()
        )
        keep = good if keep is None else (keep & good)
    keep_list = sorted(list(keep)) if keep else []
    if not keep_list:
        die(
            "Auto-targets found none meeting min_presence in all settings. "
            "Lower --auto_min_presence or mz_round."
        )

    lines_keep = lines[lines["mz_r"].isin(keep_list)]
    rank = (
        lines_keep.groupby("mz_r")["intensity"]
        .sum()
        .reset_index(name="sum_intensity")
        .sort_values("sum_intensity", ascending=False)
    )
    rank = rank.head(topk).reset_index(drop=True)
    rank["target_mz"] = rank["mz_r"].astype(float)
    rank["window_ppm"] = float(window_ppm)
    rank["label"] = ["T%02d" % (i + 1) for i in range(len(rank))]
    return rank[["label", "target_mz", "window_ppm", "sum_intensity"]]


def per_target_estimates_raw(
    df: pd.DataFrame,
    target_mz: float,
    window_ppm: float,
) -> pd.DataFrame:
    """Return per-(setting,scan) raw ppm shift + in-window intensity."""
    w = float(target_mz) * float(window_ppm) * 1e-6
    lo, hi = float(target_mz) - w, float(target_mz) + w
    sub = df[(df["mz"] >= lo) & (df["mz"] <= hi)].copy()
    if len(sub) == 0:
        return pd.DataFrame(columns=["setting", "scan", "ppm_shift_raw", "intensity_window_sum"])

    def agg(g: pd.DataFrame) -> pd.Series:
        mz = g["mz"].to_numpy(dtype=float)
        inten = g["intensity"].to_numpy(dtype=float)
        est = weighted_median(mz, inten)
        ppm = float("nan") if not np.isfinite(est) else 1e6 * (est - target_mz) / target_mz
        return pd.Series(
            {
                "ppm_shift_raw": float(ppm),
                "intensity_window_sum": float(np.nansum(inten[np.isfinite(inten)])),
            }
        )

    out = sub.groupby(["setting", "scan"], as_index=False).apply(agg)
    if isinstance(out, pd.Series):
        out = out.to_frame().reset_index()
    if "setting" not in out.columns:
        out = out.reset_index()
    return out[["setting", "scan", "ppm_shift_raw", "intensity_window_sum"]].copy()


@dataclass(frozen=True)
class DynamicsConfig:
    ablation: str  # internal_only | thread_only | full
    alpha: float
    alpha_g_floor: float


def _alpha_eff(alpha: float, g: float, *, mode: str, alpha_g_floor: float) -> float:
    if mode == "thread_only":
        return 1.0
    if mode == "internal_only":
        return float(alpha)
    # full: modulate with g(TIC)
    gg = float(g) if np.isfinite(g) else 0.0
    gg = float(np.clip(gg, 0.0, 1.0))
    scale = float(alpha_g_floor + (1.0 - alpha_g_floor) * gg)
    return float(alpha) * scale


def evolve_drift_state(scan_df: pd.DataFrame, cfg: DynamicsConfig) -> pd.DataFrame:
    """Given per-scan drift_obs_ppm and g, compute drift_state_ppm with explicit recursion."""
    if len(scan_df) == 0:
        return scan_df

    d = scan_df.sort_values(["setting", "scan"]).copy()

    out_rows = []
    stateful_steps_total = 0
    for setting, gset in d.groupby("setting", sort=True):
        gg = gset.sort_values("scan").reset_index(drop=True)
        scans = gg["scan"].to_numpy(dtype=int)
        drift_obs = gg["drift_obs_ppm"].to_numpy(dtype=float)
        gvals = gg["g"].to_numpy(dtype=float)

        drift_state = np.full_like(drift_obs, np.nan, dtype=float)
        alpha_eff = np.full_like(drift_obs, np.nan, dtype=float)

        # init
        init = drift_obs[0]
        drift_state[0] = float(init) if np.isfinite(init) else 0.0
        alpha_eff[0] = float(_alpha_eff(cfg.alpha, gvals[0], mode=cfg.ablation, alpha_g_floor=cfg.alpha_g_floor))

        for i in range(1, len(scans)):
            aeff = float(_alpha_eff(cfg.alpha, gvals[i], mode=cfg.ablation, alpha_g_floor=cfg.alpha_g_floor))
            alpha_eff[i] = aeff
            if cfg.ablation == "thread_only":
                drift_state[i] = float(drift_obs[i]) if np.isfinite(drift_obs[i]) else float(drift_state[i - 1])
                continue

            # stateful recursion
            prev = float(drift_state[i - 1])
            obs = float(drift_obs[i])
            if np.isfinite(obs):
                drift_state[i] = prev + aeff * (obs - prev)
            else:
                drift_state[i] = prev
            stateful_steps_total += 1

        gset_out = gg.copy()
        gset_out["drift_state_ppm"] = drift_state
        gset_out["alpha_eff"] = alpha_eff
        out_rows.append(gset_out)

    out = pd.concat(out_rows, ignore_index=True)
    out.attrs["stateful_steps_total"] = int(stateful_steps_total)
    return out


def _require_scan_series(df: pd.DataFrame) -> None:
    if "scan" not in df.columns:
        die("Missing required column 'scan'.")
    settings = sorted(df["setting"].unique().tolist())
    if len(settings) < 2:
        die(f"Need at least 2 settings; found: {settings}")
    for s in settings:
        n_scans = int(df[df["setting"] == s]["scan"].nunique())
        if n_scans < 2:
            die(f"Setting '{s}' has <2 scans ({n_scans}). This is not scan-series data.")


def main() -> int:
    ap = argparse.ArgumentParser(description="MS particle-specific dynamic runner (scan-series; integrity-gated)")
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--out_dir", default=os.path.join("out", "particle_specific_dynamic"))
    ap.add_argument("--setting_from", default="filename", help='filename OR "column:<col>"')
    ap.add_argument("--col_scan", default="scan")
    ap.add_argument("--col_mz", default="mz")
    ap.add_argument("--col_intensity", default="intensity")

    # thread/env (TIC -> g)
    ap.add_argument("--tic_qlo", type=float, default=0.1)
    ap.add_argument("--tic_qhi", type=float, default=0.9)
    ap.add_argument("--clip_g", action="store_true")

    # targets
    ap.add_argument("--targets_csv", default="")
    ap.add_argument("--auto_targets_topk", type=int, default=0)
    ap.add_argument("--auto_mz_round", type=float, default=0.01)
    ap.add_argument("--auto_min_presence", type=float, default=0.5)
    ap.add_argument("--auto_min_intensity", type=float, default=0.0)

    # evaluation
    ap.add_argument("--window_ppm", type=float, default=30.0)
    ap.add_argument("--good_ppm", type=float, default=3.0)
    ap.add_argument("--tail3_ppm", type=float, default=-300000.0)
    ap.add_argument("--min_n", type=int, default=8)
    ap.add_argument("--max_bins", type=int, default=8)
    ap.add_argument("--baseline", default="")

    # dynamics / ablation
    ap.add_argument(
        "--ablation",
        default="full",
        choices=["internal_only", "thread_only", "full"],
        help="Ablation mode: internal_only (stateful), thread_only (no state), full (stateful + g-modulated)",
    )
    ap.add_argument("--alpha", type=float, default=0.30, help="State update gain (0<alpha<=1)")
    ap.add_argument(
        "--alpha_g_floor",
        type=float,
        default=0.25,
        help="In FULL mode, alpha_eff = alpha*(alpha_g_floor + (1-alpha_g_floor)*g)",
    )
    ap.add_argument(
        "--require_stateful_dynamics",
        action="store_true",
        help="Fail unless INTERNAL_ONLY/FULL perform a stateful step for each scan transition.",
    )

    # --- Locked prereg observable (paper-facing) ---
    ap.add_argument(
        "--prereg_observable",
        default="raw_ppm",
        choices=["raw_ppm", "corrected_ppm"],
        help=(
            "Which ppm series is used to compute prereg artifacts. "
            "LOCKED default is raw_ppm (legacy-compatible). corrected_ppm is for research only."
        ),
    )

    # --- Telemetry-only dynamics decomposition (does not affect prereg when prereg_observable=raw_ppm) ---
    ap.add_argument(
        "--drift_state_mode",
        default="telemetry_only_commonbaseline",
        choices=["telemetry_only_commonbaseline", "telemetry_commonbaseline_plus_residual"],
        help=(
            "Always computes common drift from baseline setting only. "
            "Optionally writes residual diagnostics. Does not change prereg outputs in raw_ppm mode."
        ),
    )

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    per_target_dir = out_dir / "per_target"
    per_target_dir.mkdir(parents=True, exist_ok=True)

    # Load inputs + attach setting
    dfs = []
    setting_mode = args.setting_from.strip()
    col_setting = None
    if setting_mode.lower().startswith("column:"):
        col_setting = setting_mode.split(":", 1)[1]
        if not col_setting:
            die("--setting_from column:<name> requires column name.")
    elif setting_mode.lower() != "filename":
        die('Unsupported --setting_from. Use "filename" or "column:<col>".')

    for p in args.inputs:
        d0 = read_table(p)
        for req in [args.col_scan, args.col_mz, args.col_intensity]:
            if req not in d0.columns:
                die(f"File '{p}' missing column '{req}'. Columns: {list(d0.columns)}")
        dd = pd.DataFrame(
            {
                "scan": to_num(d0[args.col_scan], args.col_scan).astype("int64"),
                "mz": to_num(d0[args.col_mz], args.col_mz),
                "intensity": to_num(d0[args.col_intensity], args.col_intensity),
            }
        ).dropna()
        if col_setting:
            if col_setting not in d0.columns:
                die(f"File '{p}' missing setting column '{col_setting}'.")
            dd["setting"] = d0[col_setting].astype("string").str.strip()
        else:
            dd["setting"] = str(label_from_filename(p))
        dd = dd[dd["intensity"] > 0].copy()
        dfs.append(dd)

    df = pd.concat(dfs, ignore_index=True)

    # Integrity: reject non-scan-series inputs
    _require_scan_series(df)

    settings = sorted(df["setting"].unique().tolist())
    baseline = args.baseline if args.baseline else settings[0]
    if baseline not in settings:
        die(f"Baseline '{baseline}' not among settings: {settings}")

    # TIC per scan per setting
    tic = (
        df.groupby(["setting", "scan"], as_index=False)["intensity"]
        .sum()
        .rename(columns={"intensity": "tic"})
    )
    g, meta = compute_g_from_tic(tic["tic"], float(args.tic_qlo), float(args.tic_qhi))
    tic["g"] = g.clip(0, 1) if args.clip_g else g
    (out_dir / "anchors.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Targets
    targets_used_path = out_dir / "targets_used.csv"
    if args.targets_csv:
        t0 = read_table(args.targets_csv)
        if "target_mz" not in t0.columns:
            die("targets_csv must contain 'target_mz' column.")
        t = pd.DataFrame(
            {
                "label": t0["label"].astype("string") if "label" in t0.columns else None,
                "target_mz": to_num(t0["target_mz"], "target_mz"),
                "window_ppm": to_num(t0["window_ppm"], "window_ppm")
                if "window_ppm" in t0.columns
                else float(args.window_ppm),
            }
        )
        if t["label"].isna().any() or (t["label"].astype(str).str.len().min() == 0):
            t = t.reset_index(drop=True)
            t["label"] = ["T%02d" % (i + 1) for i in range(len(t))]
        t = t[["label", "target_mz", "window_ppm"]].copy()
        t.to_csv(targets_used_path, index=False)
    else:
        if args.auto_targets_topk <= 0:
            die("Provide --targets_csv OR use --auto_targets_topk K.")
        t = auto_targets_from_points(
            df,
            int(args.auto_targets_topk),
            float(args.auto_mz_round),
            float(args.auto_min_presence),
            float(args.auto_min_intensity),
            float(args.window_ppm),
        )
        t.to_csv(targets_used_path, index=False)

    # --- Raw → Observed drift ---
    raw_rows = []
    for _, tr in t.iterrows():
        label = str(tr["label"])
        target_mz = float(tr["target_mz"])
        window_ppm = float(tr["window_ppm"])
        est_raw = per_target_estimates_raw(df, target_mz, window_ppm)
        if len(est_raw) == 0:
            continue
        est_raw["target_label"] = label
        est_raw["target_mz"] = target_mz
        est_raw["window_ppm"] = window_ppm
        raw_rows.append(est_raw)

    if not raw_rows:
        die("No targets produced any estimates. Increase --window_ppm or check data.")

    raw_all = pd.concat(raw_rows, ignore_index=True)

    # Merge g/tic
    scan_meta = tic[["setting", "scan", "tic", "g"]].copy()

    drift_obs_rows = []
    for (setting, scan), gset in raw_all.groupby(["setting", "scan"], sort=True):
        ppm = gset["ppm_shift_raw"].to_numpy(dtype=float)
        w = gset["intensity_window_sum"].to_numpy(dtype=float)
        drift_obs = weighted_median(ppm, w)
        width_obs = mad(ppm)
        drift_obs_rows.append(
            {
                "setting": setting,
                "scan": int(scan),
                "drift_obs_ppm": float(drift_obs),
                "width_obs_ppm": float(width_obs),
            }
        )
    drift_obs_df = pd.DataFrame(drift_obs_rows)
    drift_obs_df = drift_obs_df.merge(scan_meta, on=["setting", "scan"], how="left")

    # IMPORTANT: Treat drift as an instrument-level state shared across settings.
    # Estimate / evolve the drift state using the BASELINE setting's observations only,
    # then apply that same drift_state_ppm to all settings.
    cfg = DynamicsConfig(ablation=str(args.ablation), alpha=float(args.alpha), alpha_g_floor=float(args.alpha_g_floor))

    baseline_obs = drift_obs_df[drift_obs_df["setting"] == baseline].copy()
    if len(baseline_obs) == 0:
        die(f"Baseline '{baseline}' has no drift observations.")

    scan_state_baseline_full = evolve_drift_state(baseline_obs, cfg)
    stateful_steps_total = int(scan_state_baseline_full.attrs.get("stateful_steps_total", 0))
    scan_state_baseline = scan_state_baseline_full[["scan", "drift_state_ppm", "alpha_eff"]].copy()

    scan_state = drift_obs_df.merge(scan_state_baseline, on=["scan"], how="left", suffixes=("", "_baseline"))

    # Integrity: require that stateful recursion actually happened
    if args.require_stateful_dynamics and args.ablation in ("internal_only", "full"):
        # Expect (n_scans_baseline-1) state transitions, since drift is evolved from baseline only.
        n_scans_baseline = int(scan_state[scan_state["setting"] == baseline]["scan"].nunique())
        expected = max(0, n_scans_baseline - 1)
        if stateful_steps_total < expected:
            die(
                f"Stateful dynamics requirement failed: stateful_steps_total={stateful_steps_total} < expected={expected}. "
                "(Are scans missing drift observations?)"
            )

    scan_state_path = out_dir / "scan_state.csv"
    scan_state.to_csv(scan_state_path, index=False)

    # Telemetry layer: common drift state evolved from baseline only.
    drift_common_csv = out_dir / "drift_common.csv"
    drift_common_out = (
        scan_state[scan_state["setting"] == baseline][
            ["scan", "tic", "g", "drift_obs_ppm", "width_obs_ppm", "drift_state_ppm", "alpha_eff"]
        ]
        .sort_values("scan")
        .reset_index(drop=True)
    )
    drift_common_out.to_csv(drift_common_csv, index=False)

    residuals_csv = out_dir / "residuals.csv"
    if str(args.drift_state_mode) == "telemetry_commonbaseline_plus_residual":
        res = scan_state.copy()
        res["residual_ppm"] = res["drift_obs_ppm"].to_numpy(dtype=float) - res["drift_state_ppm"].to_numpy(dtype=float)
        res = res[["setting", "scan", "tic", "g", "drift_obs_ppm", "drift_state_ppm", "residual_ppm", "width_obs_ppm"]]
        res = res.sort_values(["setting", "scan"]).reset_index(drop=True)
        res.to_csv(residuals_csv, index=False)

    # --- Per-target prereg observable (LOCKED default: raw ppm_shift) ---
    all_bin_rows = []
    all_delta_rows = []
    summary_rows = []

    telemetry = {
        "runner": {"name": "ms_particle_specific_dynamic_runner_v1_0_DROPIN", "path": str(Path(__file__).resolve())},
        "ablation": str(args.ablation),
        "prereg_observable": str(args.prereg_observable),
        "drift_state_mode": str(args.drift_state_mode),
        "dynamics": {
            "internal_dynamics_used": bool(args.ablation in ("internal_only", "full")),
            "thread_env_used": bool(args.ablation == "full"),
            "alpha": float(args.alpha),
            "alpha_g_floor": float(args.alpha_g_floor),
            "stateful_steps_total": int(stateful_steps_total),
        },
        "integrity": {
            "scan_series_required": True,
            "columns_used_for_dynamics": ["ppm_shift_raw", "intensity_window_sum", "g"],
            "setting_not_used_in_dynamics": True,
        },
        "data": {
            "n_settings": int(len(settings)),
            "settings": settings,
            "baseline": str(baseline),
            "n_targets": int(len(t)),
        },
    }

    for _, tr in t.iterrows():
        label = str(tr["label"])
        target_mz = float(tr["target_mz"])
        window_ppm = float(tr["window_ppm"])

        est = raw_all[raw_all["target_label"] == label].copy()
        if len(est) == 0:
            continue
        est = est.merge(scan_state[["setting", "scan", "g", "drift_state_ppm"]], on=["setting", "scan"], how="left")
        est = est.dropna(subset=["g", "ppm_shift_raw"]).copy()

        raw_ppm = est["ppm_shift_raw"].to_numpy(dtype=float)
        drift_state = est["drift_state_ppm"].to_numpy(dtype=float)

        # LOCKED prereg observable: raw ppm_shift (legacy-compatible).
        if str(args.prereg_observable) == "raw_ppm":
            est["ppm_shift"] = raw_ppm
        else:
            # Research-only: drift-corrected observable.
            est["ppm_shift"] = raw_ppm - drift_state

        est_sorted = est.sort_values("g").reset_index(drop=True)
        bins = build_balanced_bins(est_sorted[["setting", "g", "ppm_shift"]], min_n=int(args.min_n), max_bins=int(args.max_bins))

        rows = []
        for bi, (a, b) in enumerate(bins):
            sub = est_sorted.iloc[a : b + 1]
            g_lo = float(np.min(sub["g"]))
            g_hi = float(np.max(sub["g"]))
            g_center = float(0.5 * (g_lo + g_hi))
            for s in settings:
                ss = sub[sub["setting"] == s]
                ppm = ss["ppm_shift"].to_numpy(dtype=float)
                n = int(len(ppm))
                good_mask = np.abs(ppm) < float(args.good_ppm)
                ppm_good = ppm[good_mask]
                rows.append(
                    {
                        "target_label": label,
                        "target_mz": target_mz,
                        "window_ppm": window_ppm,
                        "setting": s,
                        "g_bin": bi,
                        "g_lo": g_lo,
                        "g_hi": g_hi,
                        "g_center": g_center,
                        "n_total": n,
                        "n_good": int(good_mask.sum()),
                        "p_success": float(np.mean(good_mask)) if n else float("nan"),
                        "median_success_ppm": float(np.median(ppm_good)) if ppm_good.size else float("nan"),
                        "mad_success_ppm": mad(ppm_good) if ppm_good.size else float("nan"),
                        "frac_tail3": float(np.mean(ppm < float(args.tail3_ppm))) if n else float("nan"),
                    }
                )
        stats = pd.DataFrame(rows).sort_values(["g_bin", "setting"]).reset_index(drop=True)

        piv = stats.pivot_table(
            index=["g_bin", "g_lo", "g_hi", "g_center"],
            columns="setting",
            values=["p_success", "mad_success_ppm"],
            aggfunc="first",
        )
        if baseline not in piv["p_success"].columns:
            die(f'Baseline "{baseline}" not present for target {label}.')
        delta_rows = []
        for idx in piv.index:
            gbin, _, _, g_center = idx
            base_p = piv.loc[idx, ("p_success", baseline)]
            base_m = piv.loc[idx, ("mad_success_ppm", baseline)]
            for comp in settings:
                if comp == baseline:
                    continue
                comp_p = piv.loc[idx, ("p_success", comp)]
                comp_m = piv.loc[idx, ("mad_success_ppm", comp)]
                delta_rows.append(
                    {
                        "target_label": label,
                        "target_mz": target_mz,
                        "g_bin": int(gbin),
                        "g_center": float(g_center),
                        "baseline": baseline,
                        "compare": comp,
                        "delta_p_success": float(comp_p - base_p),
                        "ratio_mad_success": float(comp_m / base_m)
                        if np.isfinite(comp_m)
                        and np.isfinite(base_m)
                        and base_m not in (0.0, np.nan)
                        else float("nan"),
                    }
                )
        deltas = pd.DataFrame(delta_rows)

        safe_label = re.sub(r"[^A-Za-z0-9_\-]+", "_", label)
        tag = f"{safe_label}_{target_mz:.6f}".replace(".", "p")
        stats.to_csv(per_target_dir / f"TARGET_{tag}.csv", index=False)
        deltas.to_csv(per_target_dir / f"DELTA_{tag}.csv", index=False)

        if len(deltas):
            for comp in sorted(deltas["compare"].unique().tolist()):
                dcomp = deltas[deltas["compare"] == comp]
                summary_rows.append(
                    {
                        "target_label": label,
                        "target_mz": target_mz,
                        "compare": comp,
                        "mean_abs_delta_p_success": float(np.mean(np.abs(dcomp["delta_p_success"].to_numpy()))),
                        "max_abs_delta_p_success": float(np.max(np.abs(dcomp["delta_p_success"].to_numpy()))),
                    }
                )

        all_bin_rows.append(stats)
        all_delta_rows.append(deltas)

    all_stats = pd.concat(all_bin_rows, ignore_index=True)
    all_deltas = pd.concat(all_delta_rows, ignore_index=True) if any(len(x) for x in all_delta_rows) else pd.DataFrame()

    (out_dir / "alltargets_bin_success_width_stats.csv").write_text(all_stats.to_csv(index=False), encoding="utf-8")
    (out_dir / "alltargets_delta_success_width_pairs.csv").write_text(all_deltas.to_csv(index=False), encoding="utf-8")
    pd.DataFrame(summary_rows).to_csv(out_dir / "targets_summary.csv", index=False)

    (out_dir / "ms_dynamic_telemetry.json").write_text(json.dumps(telemetry, indent=2), encoding="utf-8")

    # --- Layer B: audited dynamics integrity report (does NOT affect prereg gate) ---
    def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
        m = np.isfinite(a) & np.isfinite(b)
        if int(np.sum(m)) < 3:
            return float("nan")
        return float(np.corrcoef(a[m], b[m])[0, 1])

    audit: dict = {
        "runner": "ms_particle_specific_dynamic_runner_v1_0_DROPIN",
        "ablation": str(args.ablation),
        "prereg_observable": str(args.prereg_observable),
        "drift_state_mode": str(args.drift_state_mode),
        "baseline": str(baseline),
        "settings": settings,
        "stateful_steps_total": int(stateful_steps_total),
        "paths": {
            "scan_state_csv": str(scan_state_path).replace("\\", "/"),
            "drift_common_csv": str(drift_common_csv).replace("\\", "/"),
            "residuals_csv": str(residuals_csv).replace("\\", "/") if residuals_csv.exists() else None,
        },
    }

    base_ss = scan_state[scan_state["setting"] == baseline].sort_values("scan")
    obs_b = base_ss["drift_obs_ppm"].to_numpy(dtype=float)
    st_b = base_ss["drift_state_ppm"].to_numpy(dtype=float)
    resid_b = obs_b - st_b
    audit["drift_fit_baseline"] = {
        "rmse_ppm": float(np.sqrt(np.nanmean(resid_b**2))) if np.isfinite(resid_b).any() else float("nan"),
        "mae_ppm": float(np.nanmean(np.abs(resid_b))) if np.isfinite(resid_b).any() else float("nan"),
        "corr_obs_vs_state": _safe_corr(obs_b, st_b),
        "median_abs_residual_ppm": float(np.nanmedian(np.abs(resid_b))) if np.isfinite(resid_b).any() else float("nan"),
        "n_scans": int(base_ss["scan"].nunique()),
    }

    resid_by_setting = {}
    for s in settings:
        ss = scan_state[scan_state["setting"] == s].sort_values("scan")
        o = ss["drift_obs_ppm"].to_numpy(dtype=float)
        st = ss["drift_state_ppm"].to_numpy(dtype=float)
        r = o - st
        resid_by_setting[str(s)] = {
            "median_abs_residual_ppm": float(np.nanmedian(np.abs(r))) if np.isfinite(r).any() else float("nan"),
            "mean_abs_residual_ppm": float(np.nanmean(np.abs(r))) if np.isfinite(r).any() else float("nan"),
            "corr_obs_vs_state": _safe_corr(o, st),
        }
    audit["residual_summary_by_setting"] = resid_by_setting

    # Anti-cancel diagnostic: compare target ranking under raw prereg vs corrected-as-if (raw - common drift).
    anti_cancel = {"rank_corr_raw_vs_corrected": None, "top_raw": None, "top_corrected": None, "top_match": None}
    try:
        if len(all_deltas) and "target_label" in all_deltas.columns and "delta_p_success" in all_deltas.columns:
            raw_rank = (
                all_deltas.groupby("target_label")["delta_p_success"]
                .apply(lambda v: float(np.mean(np.abs(v.to_numpy(dtype=float)))))
                .sort_index()
            )
        else:
            raw_rank = None
    except Exception:
        raw_rank = None

    corr_rank = None
    try:
        if raw_rank is not None and len(raw_rank) > 0:
            corr_abs_means = {}
            comps = [s for s in settings if s != baseline]
            comp = comps[0] if comps else None
            if comp is not None:
                for _, tr2 in t.iterrows():
                    lbl = str(tr2["label"])
                    est2 = raw_all[raw_all["target_label"] == lbl].copy()
                    if len(est2) == 0:
                        continue
                    est2 = est2.merge(scan_state[["setting", "scan", "g", "drift_state_ppm"]], on=["setting", "scan"], how="left")
                    est2 = est2.dropna(subset=["g", "ppm_shift_raw", "drift_state_ppm"]).copy()
                    est2["ppm_shift"] = est2["ppm_shift_raw"].to_numpy(dtype=float) - est2["drift_state_ppm"].to_numpy(dtype=float)

                    est2_sorted = est2.sort_values("g").reset_index(drop=True)
                    bins2 = build_balanced_bins(
                        est2_sorted[["setting", "g", "ppm_shift"]],
                        min_n=int(args.min_n),
                        max_bins=int(args.max_bins),
                    )

                    rows2 = []
                    for bi, (a2, b2) in enumerate(bins2):
                        sub2 = est2_sorted.iloc[a2 : b2 + 1]
                        for s2 in settings:
                            ss2 = sub2[sub2["setting"] == s2]
                            ppm2 = ss2["ppm_shift"].to_numpy(dtype=float)
                            n2 = int(len(ppm2))
                            good_mask2 = np.abs(ppm2) < float(args.good_ppm)
                            rows2.append({"g_bin": bi, "setting": s2, "p_success": float(np.mean(good_mask2)) if n2 else float("nan")})

                    st2 = pd.DataFrame(rows2)
                    piv2 = st2.pivot_table(index=["g_bin"], columns="setting", values=["p_success"], aggfunc="first")
                    if baseline not in piv2["p_success"].columns or comp not in piv2["p_success"].columns:
                        continue
                    deltas2 = (piv2[("p_success", comp)] - piv2[("p_success", baseline)]).to_numpy(dtype=float)
                    corr_abs_means[lbl] = float(np.nanmean(np.abs(deltas2))) if np.isfinite(deltas2).any() else float("nan")

                corr_rank = pd.Series(corr_abs_means).sort_index()
    except Exception:
        corr_rank = None

    if raw_rank is not None and corr_rank is not None and len(raw_rank) and len(corr_rank):
        joined = pd.concat([raw_rank.rename("raw"), corr_rank.rename("corrected")], axis=1).dropna()
        if len(joined):
            anti_cancel = {
                "rank_corr_raw_vs_corrected": float(joined["raw"].rank().corr(joined["corrected"].rank())),
                "top_raw": str(joined["raw"].idxmax()),
                "top_corrected": str(joined["corrected"].idxmax()),
                "top_match": bool(str(joined["raw"].idxmax()) == str(joined["corrected"].idxmax())),
            }
    audit["anti_cancel"] = anti_cancel

    (out_dir / "ms_dynamic_state_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print("[OK] wrote:", str(out_dir / "anchors.json"))
    print("[OK] wrote:", str(targets_used_path))
    print("[OK] wrote:", str(out_dir / "alltargets_bin_success_width_stats.csv"))
    print("[OK] wrote:", str(out_dir / "alltargets_delta_success_width_pairs.csv"))
    print("[OK] wrote:", str(out_dir / "targets_summary.csv"))
    print("[OK] wrote:", str(out_dir / "ms_dynamic_telemetry.json"))
    print("[OK] wrote:", str(scan_state_path))
    print("[OK] wrote:", str(drift_common_csv))
    if residuals_csv.exists():
        print("[OK] wrote:", str(residuals_csv))
    print("[OK] wrote:", str(out_dir / "ms_dynamic_state_audit.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
