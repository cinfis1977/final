#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_target_particle_specific_v1_0.py

NO-FIT multi-target "particle-specific" test on points/peaks CSV (scan,mz,intensity).

See README for usage.

Outputs:
  anchors.json
  targets_used.csv
  targets_summary.csv
  alltargets_bin_success_width_stats.csv
  alltargets_delta_success_width_pairs.csv
  per_target/*.png + per-target CSVs

Optional hard-regression add-on (disabled by default):
  alltargets_bin_success_width_stats_occgate.csv
  alltargets_delta_success_width_pairs_occgate.csv
  targets_summary_occgate.csv
"""
from __future__ import annotations

import argparse, os, gzip, json, re
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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
    sep = max(counts, key=counts.get)
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
    return float(v[min(idx, len(v)-1)])


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
        ends = []
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
        bins[-1] = (bins[-1][0], N-1)

    # validate; merge invalid into previous
    good: List[Tuple[int, int]] = []
    for a, b in bins:
        sub = df_sorted.iloc[a:b+1]
        ok = all(int((sub["setting"] == s).sum()) >= min_n for s in settings)
        if ok:
            good.append((a, b))
        else:
            if good:
                good[-1] = (good[-1][0], b)
            else:
                die("First bin invalid. Lower min_n.")
    # final check
    for a, b in good:
        sub = df_sorted.iloc[a:b+1]
        if not all(int((sub["setting"] == s).sum()) >= min_n for s in settings):
            die("Bin validation failed. Lower min_n.")
    return good


def auto_targets_from_points(df: pd.DataFrame, topk: int, mz_round: float, min_presence_frac: float,
                             min_intensity: float, window_ppm: float) -> pd.DataFrame:
    if topk < 1:
        die("--auto_targets_topk must be >=1")
    d = df.copy()
    d = d[d["intensity"] >= float(min_intensity)]
    d["mz_r"] = (d["mz"] / mz_round).round().astype("int64") * mz_round
    # presence: exists in scan
    lines = d.groupby(["setting","scan","mz_r"], as_index=False)["intensity"].max()
    scan_counts = d.groupby("setting")["scan"].nunique().to_dict()
    pres = lines.groupby(["setting","mz_r"])["scan"].nunique().reset_index(name="n_scans_present")
    pres["n_scans_total"] = pres["setting"].map(scan_counts)
    pres["presence_frac"] = pres["n_scans_present"] / pres["n_scans_total"]

    settings = sorted(d["setting"].unique().tolist())
    keep = None
    for s in settings:
        good = set(pres[(pres["setting"] == s) & (pres["presence_frac"] >= min_presence_frac)]["mz_r"].tolist())
        keep = good if keep is None else (keep & good)
    keep = sorted(list(keep)) if keep else []
    if not keep:
        die("Auto-targets found none meeting min_presence in all settings. Lower --auto_min_presence or mz_round.")

    lines_keep = lines[lines["mz_r"].isin(keep)]
    rank = lines_keep.groupby("mz_r")["intensity"].sum().reset_index(name="sum_intensity").sort_values("sum_intensity", ascending=False)
    rank = rank.head(topk).reset_index(drop=True)
    rank["target_mz"] = rank["mz_r"].astype(float)
    rank["window_ppm"] = float(window_ppm)
    rank["label"] = ["T%02d" % (i+1) for i in range(len(rank))]
    return rank[["label","target_mz","window_ppm","sum_intensity"]]



def per_target_estimates(
    df: pd.DataFrame,
    target_mz: float,
    window_ppm: float,
    occ_enabled: bool = False,
    occ_rho: float = 0.25,
    occ_core_ppm: float = 10.0,
) -> pd.DataFrame:
    w = float(target_mz) * float(window_ppm) * 1e-6
    lo, hi = float(target_mz) - w, float(target_mz) + w
    sub = df[(df["mz"] >= lo) & (df["mz"] <= hi)].copy()
    if len(sub) == 0:
        cols = ["setting", "scan", "ppm_shift"]
        if occ_enabled:
            cols += ["x_occ", "gate_occ_factor"]
        return pd.DataFrame(columns=cols)

    core_w = float(target_mz) * float(min(occ_core_ppm, window_ppm)) * 1e-6 if occ_enabled else 0.0

    def agg(g: pd.DataFrame) -> pd.Series:
        mz = g["mz"].to_numpy(dtype=float)
        inten = g["intensity"].to_numpy(dtype=float)
        est = weighted_median(mz, inten)
        ppm = float("nan") if not np.isfinite(est) else 1e6 * (est - target_mz) / target_mz
        out = {"ppm_shift": ppm}
        if occ_enabled:
            local_total = float(np.sum(inten[np.isfinite(inten)]))
            core_mask = np.abs(mz - target_mz) <= core_w
            core_total = float(np.sum(inten[np.isfinite(inten) & core_mask]))
            if np.isfinite(local_total) and local_total > 0.0:
                x_occ = float(np.clip(core_total / local_total, 0.0, 1.0))
            else:
                x_occ = float("nan")
            gate_occ_factor = float(np.clip(1.0 - float(occ_rho) * x_occ, 0.0, 1.0)) if np.isfinite(x_occ) else float("nan")
            out["x_occ"] = x_occ
            out["gate_occ_factor"] = gate_occ_factor
        return pd.Series(out)

    out = sub.groupby(["setting", "scan"], as_index=False).apply(agg)
    if isinstance(out, pd.Series):
        out = out.to_frame().reset_index()
    if "setting" not in out.columns:
        out = out.reset_index()
    return out

def plot_stat(stats: pd.DataFrame, ycol: str, title: str, ylabel: str, out_png: str) -> None:
    plt.figure(figsize=(10,6))
    for s in sorted(stats["setting"].unique().tolist()):
        ss = stats[stats["setting"]==s].sort_values("g_center")
        plt.plot(ss["g_center"], ss[ycol], marker="o", linewidth=2.2, label=s)
    plt.xlabel("g")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--out_dir", default=os.path.join("out","particle_specific"))
    ap.add_argument("--setting_from", default="filename", help='filename OR "column:<col>"')
    ap.add_argument("--col_scan", default="scan")
    ap.add_argument("--col_mz", default="mz")
    ap.add_argument("--col_intensity", default="intensity")
    ap.add_argument("--tic_qlo", type=float, default=0.1)
    ap.add_argument("--tic_qhi", type=float, default=0.9)
    ap.add_argument("--targets_csv", default="")
    ap.add_argument("--auto_targets_topk", type=int, default=0)
    ap.add_argument("--auto_mz_round", type=float, default=0.01)
    ap.add_argument("--auto_min_presence", type=float, default=0.5)
    ap.add_argument("--auto_min_intensity", type=float, default=0.0)
    ap.add_argument("--window_ppm", type=float, default=30.0)
    ap.add_argument("--enable_occ_gate", action="store_true", help="Enable optional occupancy-gated hard-regression add-on (legacy outputs unchanged).")
    ap.add_argument("--occ_rho", type=float, default=0.25, help="Frozen occupancy gate strength for optional hard-regression add-on.")
    ap.add_argument("--occ_core_ppm", type=float, default=10.0, help="Inner core width (ppm) used to compute x_occ inside each target window.")
    ap.add_argument("--good_ppm", type=float, default=5000.0)
    ap.add_argument("--tail3_ppm", type=float, default=-300000.0)
    ap.add_argument("--min_n", type=int, default=8)
    ap.add_argument("--max_bins", type=int, default=8)
    ap.add_argument("--baseline", default="")
    ap.add_argument("--clip_g", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    per_target_dir = os.path.join(args.out_dir, "per_target")
    os.makedirs(per_target_dir, exist_ok=True)

    # Load inputs + attach setting
    dfs = []
    setting_mode = args.setting_from.strip()
    col_setting = None
    if setting_mode.lower().startswith("column:"):
        col_setting = setting_mode.split(":",1)[1]
        if not col_setting:
            die("--setting_from column:<name> requires column name.")
    elif setting_mode.lower() != "filename":
        die('Unsupported --setting_from. Use "filename" or "column:<col>".')

    for p in args.inputs:
        d0 = read_table(p)
        for req in [args.col_scan, args.col_mz, args.col_intensity]:
            if req not in d0.columns:
                die(f"File '{p}' missing column '{req}'. Columns: {list(d0.columns)}")
        dd = pd.DataFrame({
            "scan": to_num(d0[args.col_scan], args.col_scan).astype("int64"),
            "mz": to_num(d0[args.col_mz], args.col_mz),
            "intensity": to_num(d0[args.col_intensity], args.col_intensity),
        }).dropna()
        if col_setting:
            if col_setting not in d0.columns:
                die(f"File '{p}' missing setting column '{col_setting}'.")
            dd["setting"] = d0[col_setting].astype("string").str.strip()
        else:
            dd["setting"] = str(label_from_filename(p))
        dd = dd[dd["intensity"] > 0].copy()
        dfs.append(dd)

    df = pd.concat(dfs, ignore_index=True)
    settings = sorted(df["setting"].unique().tolist())
    if len(settings) < 2:
        die(f"Need at least 2 settings; found: {settings}")

    baseline = args.baseline if args.baseline else settings[0]

    # TIC per scan per setting
    tic = df.groupby(["setting","scan"], as_index=False)["intensity"].sum().rename(columns={"intensity":"tic"})
    g, meta = compute_g_from_tic(tic["tic"], args.tic_qlo, args.tic_qhi)
    tic["g"] = g.clip(0,1) if args.clip_g else g
    with open(os.path.join(args.out_dir, "anchors.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Targets
    targets_used_path = os.path.join(args.out_dir, "targets_used.csv")
    if args.targets_csv:
        if not os.path.exists(args.targets_csv):
            die(f"targets_csv not found: {args.targets_csv}")
        t0 = read_table(args.targets_csv)
        if "target_mz" not in t0.columns:
            die("targets_csv must contain 'target_mz' column.")
        t = pd.DataFrame({
            "label": t0["label"].astype("string") if "label" in t0.columns else None,
            "target_mz": to_num(t0["target_mz"], "target_mz"),
            "window_ppm": to_num(t0["window_ppm"], "window_ppm") if "window_ppm" in t0.columns else float(args.window_ppm),
        })
        if t["label"].isna().any() or (t["label"].astype(str).str.len().min() == 0):
            t = t.reset_index(drop=True)
            t["label"] = ["T%02d" % (i+1) for i in range(len(t))]
        t = t[["label","target_mz","window_ppm"]].copy()
        t.to_csv(targets_used_path, index=False)
    else:
        if args.auto_targets_topk <= 0:
            die("Provide --targets_csv OR use --auto_targets_topk K.")
        t = auto_targets_from_points(df, args.auto_targets_topk, args.auto_mz_round, args.auto_min_presence,
                                     args.auto_min_intensity, args.window_ppm)
        t.to_csv(targets_used_path, index=False)

    all_bin_rows = []
    all_delta_rows = []
    summary_rows = []
    all_bin_rows_occ = []
    all_delta_rows_occ = []
    summary_rows_occ = []

    for _, tr in t.iterrows():
        label = str(tr["label"])
        target_mz = float(tr["target_mz"])
        window_ppm = float(tr["window_ppm"])

        est = per_target_estimates(
            df,
            target_mz,
            window_ppm,
            occ_enabled=args.enable_occ_gate,
            occ_rho=args.occ_rho,
            occ_core_ppm=args.occ_core_ppm,
        )
        if len(est) == 0:
            continue
        est = est.merge(tic[["setting","scan","g"]], on=["setting","scan"], how="left")
        est = est.dropna(subset=["g","ppm_shift"]).copy()
        est_sorted = est.sort_values("g").reset_index(drop=True)

        bins = build_balanced_bins(est_sorted[["setting","g","ppm_shift"]], min_n=args.min_n, max_bins=args.max_bins)

        rows = []
        for bi, (a,b) in enumerate(bins):
            sub = est_sorted.iloc[a:b+1]
            g_lo = float(np.min(sub["g"])); g_hi = float(np.max(sub["g"]))
            g_center = float(0.5*(g_lo+g_hi))
            for s in settings:
                ss = sub[sub["setting"]==s]
                ppm = ss["ppm_shift"].to_numpy(dtype=float)
                n = int(len(ppm))
                good_mask = np.abs(ppm) < args.good_ppm
                ppm_good = ppm[good_mask]
                row = {
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
                    "frac_tail3": float(np.mean(ppm < args.tail3_ppm)) if n else float("nan"),
                }
                if args.enable_occ_gate:
                    gate = ss["gate_occ_factor"].to_numpy(dtype=float) if "gate_occ_factor" in ss.columns else np.full(n, np.nan)
                    x_occ = ss["x_occ"].to_numpy(dtype=float) if "x_occ" in ss.columns else np.full(n, np.nan)
                    good_gate = gate[good_mask] if n else np.array([], dtype=float)
                    row.update({
                        "x_occ_mean": float(np.nanmean(x_occ)) if n else float("nan"),
                        "x_occ_median": float(np.nanmedian(x_occ)) if n else float("nan"),
                        "gate_occ_factor_mean": float(np.nanmean(gate)) if n else float("nan"),
                        "gate_occ_factor_min": float(np.nanmin(gate)) if n and np.isfinite(gate).any() else float("nan"),
                        "gate_occ_factor_max": float(np.nanmax(gate)) if n and np.isfinite(gate).any() else float("nan"),
                        "mean_gate_good": float(np.nanmean(good_gate)) if good_gate.size else float("nan"),
                        "p_success_occ": float(np.nansum(np.where(good_mask, gate, 0.0)) / n) if n else float("nan"),
                    })
                rows.append(row)
        stats = pd.DataFrame(rows).sort_values(["g_bin","setting"]).reset_index(drop=True)

        # deltas vs baseline per bin (for p_success and mad ratio)
        piv = stats.pivot_table(index=["g_bin","g_lo","g_hi","g_center"], columns="setting",
                                values=["p_success","mad_success_ppm"], aggfunc="first")
        if baseline not in piv["p_success"].columns:
            die(f'Baseline "{baseline}" not present for target {label}.')
        delta_rows = []
        for idx in piv.index:
            gbin, g_lo, g_hi, g_center = idx
            base_p = piv.loc[idx, ("p_success", baseline)]
            base_m = piv.loc[idx, ("mad_success_ppm", baseline)]
            for comp in settings:
                if comp == baseline:
                    continue
                comp_p = piv.loc[idx, ("p_success", comp)]
                comp_m = piv.loc[idx, ("mad_success_ppm", comp)]
                delta_rows.append({
                    "target_label": label,
                    "target_mz": target_mz,
                    "g_bin": int(gbin),
                    "g_center": float(g_center),
                    "baseline": baseline,
                    "compare": comp,
                    "delta_p_success": float(comp_p - base_p),
                    "ratio_mad_success": float(comp_m / base_m) if np.isfinite(comp_m) and np.isfinite(base_m) and base_m not in (0.0, np.nan) else float("nan"),
                })
        deltas = pd.DataFrame(delta_rows)

        if args.enable_occ_gate:
            delta_rows_occ = []
            piv_occ = stats.pivot_table(index=["g_bin","g_lo","g_hi","g_center"], columns="setting",
                                        values=["p_success_occ","x_occ_mean","gate_occ_factor_mean"], aggfunc="first")
            if baseline not in piv_occ["p_success_occ"].columns:
                die(f'Baseline "{baseline}" not present for OCC target {label}.')
            for idx in piv_occ.index:
                gbin, g_lo, g_hi, g_center = idx
                base_p_occ = piv_occ.loc[idx, ("p_success_occ", baseline)]
                base_x_occ = piv_occ.loc[idx, ("x_occ_mean", baseline)]
                base_gate_occ = piv_occ.loc[idx, ("gate_occ_factor_mean", baseline)]
                for comp in settings:
                    if comp == baseline:
                        continue
                    comp_p_occ = piv_occ.loc[idx, ("p_success_occ", comp)]
                    comp_x_occ = piv_occ.loc[idx, ("x_occ_mean", comp)]
                    comp_gate_occ = piv_occ.loc[idx, ("gate_occ_factor_mean", comp)]
                    delta_rows_occ.append({
                        "target_label": label,
                        "target_mz": target_mz,
                        "g_bin": int(gbin),
                        "g_center": float(g_center),
                        "baseline": baseline,
                        "compare": comp,
                        "delta_p_success_occ": float(comp_p_occ - base_p_occ),
                        "delta_x_occ_mean": float(comp_x_occ - base_x_occ),
                        "delta_gate_occ_factor_mean": float(comp_gate_occ - base_gate_occ),
                    })
            deltas_occ = pd.DataFrame(delta_rows_occ)
        else:
            deltas_occ = pd.DataFrame()

        safe_label = re.sub(r"[^A-Za-z0-9_\-]+", "_", label)
        tag = f"{safe_label}_{target_mz:.6f}".replace(".","p")
        stats.to_csv(os.path.join(per_target_dir, f"TARGET_{tag}.csv"), index=False)
        deltas.to_csv(os.path.join(per_target_dir, f"DELTA_{tag}.csv"), index=False)
        if args.enable_occ_gate:
            stats.to_csv(os.path.join(per_target_dir, f"TARGET_OCC_{tag}.csv"), index=False)
            deltas_occ.to_csv(os.path.join(per_target_dir, f"DELTA_OCC_{tag}.csv"), index=False)

        plot_stat(stats, "p_success", f"p_success vs g — {label} @ {target_mz:.6f}", "fraction",
                  os.path.join(per_target_dir, f"p_success_{tag}.png"))
        plot_stat(stats, "mad_success_ppm", f"MAD_success vs g — {label} @ {target_mz:.6f}", "mad_success_ppm",
                  os.path.join(per_target_dir, f"mad_success_{tag}.png"))
        plot_stat(stats, "median_success_ppm", f"median_success_ppm vs g — {label} @ {target_mz:.6f}", "median_success_ppm",
                  os.path.join(per_target_dir, f"median_success_{tag}.png"))

        # discrimination summary per target per compare
        if len(deltas):
            for comp in sorted(deltas["compare"].unique().tolist()):
                dcomp = deltas[deltas["compare"]==comp]
                summary_rows.append({
                    "target_label": label,
                    "target_mz": target_mz,
                    "compare": comp,
                    "mean_abs_delta_p_success": float(np.mean(np.abs(dcomp["delta_p_success"].to_numpy()))),
                    "max_abs_delta_p_success": float(np.max(np.abs(dcomp["delta_p_success"].to_numpy()))),
                })
        if args.enable_occ_gate and len(deltas_occ):
            for comp in sorted(deltas_occ["compare"].unique().tolist()):
                dcomp = deltas_occ[deltas_occ["compare"]==comp]
                summary_rows_occ.append({
                    "target_label": label,
                    "target_mz": target_mz,
                    "compare": comp,
                    "mean_abs_delta_p_success_occ": float(np.mean(np.abs(dcomp["delta_p_success_occ"].to_numpy()))),
                    "max_abs_delta_p_success_occ": float(np.max(np.abs(dcomp["delta_p_success_occ"].to_numpy()))),
                    "mean_abs_delta_x_occ_mean": float(np.mean(np.abs(dcomp["delta_x_occ_mean"].to_numpy()))),
                })

        all_bin_rows.append(stats)
        all_delta_rows.append(deltas)
        if args.enable_occ_gate:
            all_bin_rows_occ.append(stats.copy())
            all_delta_rows_occ.append(deltas_occ.copy())

    if not all_bin_rows:
        die("No targets produced any estimates. Increase --window_ppm or check data.")


    all_stats = pd.concat(all_bin_rows, ignore_index=True)
    all_deltas = pd.concat(all_delta_rows, ignore_index=True) if any(len(x) for x in all_delta_rows) else pd.DataFrame()

    legacy_bin_path = os.path.join(args.out_dir, "alltargets_bin_success_width_stats.csv")
    legacy_delta_path = os.path.join(args.out_dir, "alltargets_delta_success_width_pairs.csv")
    legacy_summary_path = os.path.join(args.out_dir, "targets_summary.csv")
    all_stats.to_csv(legacy_bin_path, index=False)
    all_deltas.to_csv(legacy_delta_path, index=False)
    pd.DataFrame(summary_rows).to_csv(legacy_summary_path, index=False)

    print("[OK] wrote:", os.path.join(args.out_dir, "anchors.json"))
    print("[OK] wrote:", targets_used_path)
    print("[OK] wrote:", legacy_bin_path)
    print("[OK] wrote:", legacy_delta_path)
    print("[OK] wrote:", legacy_summary_path)

    if args.enable_occ_gate:
        occ_bin_path = os.path.join(args.out_dir, "alltargets_bin_success_width_stats_occgate.csv")
        occ_delta_path = os.path.join(args.out_dir, "alltargets_delta_success_width_pairs_occgate.csv")
        occ_summary_path = os.path.join(args.out_dir, "targets_summary_occgate.csv")
        all_stats_occ = pd.concat(all_bin_rows_occ, ignore_index=True) if any(len(x) for x in all_bin_rows_occ) else pd.DataFrame()
        all_deltas_occ = pd.concat(all_delta_rows_occ, ignore_index=True) if any(len(x) for x in all_delta_rows_occ) else pd.DataFrame()
        all_stats_occ.to_csv(occ_bin_path, index=False)
        all_deltas_occ.to_csv(occ_delta_path, index=False)
        pd.DataFrame(summary_rows_occ).to_csv(occ_summary_path, index=False)
        print("[OK] wrote:", occ_bin_path)
        print("[OK] wrote:", occ_delta_path)
        print("[OK] wrote:", occ_summary_path)

    print("[OK] per-target:", per_target_dir)
    print("[INFO] settings:", settings, "baseline:", baseline)


if __name__ == "__main__":
    main()
