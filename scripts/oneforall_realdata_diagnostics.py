#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def chi2_gauss_loose(obs: np.ndarray, pred: np.ndarray, systfrac: float = 0.0, sigma_floor: float = 0.0) -> float:
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    var = np.maximum(pred, 1.0) + (float(systfrac) * pred) ** 2 + float(sigma_floor) ** 2
    return float(np.sum((obs - pred) ** 2 / var))


def chi2_poisson_deviance(obs: np.ndarray, pred: np.ndarray, floor: float = 1e-12) -> float:
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    pred = np.maximum(pred, float(floor))

    term = pred - obs
    m = obs > 0
    term[m] = pred[m] - obs[m] + obs[m] * np.log(obs[m] / pred[m])
    return float(2.0 * np.sum(term))


def _load_cov_matrix(cov_csv: Path) -> np.ndarray:
    """Load a covariance matrix from CSV.

    Repo covariance files are usually headerless numeric CSVs, but some (e.g.
    derived diag-cov tables) may include row/column labels.
    """
    try:
        cov = np.loadtxt(str(cov_csv), delimiter=",")
        cov = np.asarray(cov, float)
        if cov.ndim == 1:
            cov = np.diag(cov)
        return cov
    except Exception:
        # Fall back to pandas and coerce numeric. Try a few common layouts.
        candidates: list[pd.DataFrame] = []

        # 1) Headered matrix with column labels (no explicit index column).
        try:
            candidates.append(pd.read_csv(cov_csv))
        except Exception:
            pass

        # 2) Matrix with an explicit first column index/label.
        try:
            candidates.append(pd.read_csv(cov_csv, index_col=0))
        except Exception:
            pass

        # 3) Raw numeric grid (no header).
        try:
            candidates.append(pd.read_csv(cov_csv, header=None))
        except Exception:
            pass

        last_err: Exception | None = None
        for df in candidates:
            try:
                num = df.apply(pd.to_numeric, errors="coerce")
                num = num.dropna(axis=0, how="all").dropna(axis=1, how="all")
                cov = num.to_numpy(dtype=float)
                if cov.ndim == 1:
                    cov = np.diag(cov)
                # Prefer square matrices (covariance)
                if cov.shape[0] == cov.shape[1]:
                    return cov
                # Otherwise keep searching.
            except Exception as e:
                last_err = e

        if last_err is not None:
            raise last_err
        raise ValueError(f"Could not parse covariance CSV: {cov_csv}")


def chi2_from_cov(resid: np.ndarray, cov: np.ndarray) -> float:
    resid = np.asarray(resid, float)
    cov = np.asarray(cov, float)
    # Solve C x = r then chi2 = r^T x (more stable than explicit inverse)
    try:
        x = np.linalg.solve(cov, resid)
    except np.linalg.LinAlgError:
        x = np.linalg.lstsq(cov, resid, rcond=None)[0]
    return float(resid @ x)


def topk_bin_pulls(resid: np.ndarray, cov: np.ndarray, topk: int) -> list[tuple[int, float, float]]:
    """Return (idx, pull, resid) ranked by |pull| using diag(cov) only.

    With correlated systematics, true per-bin contributions are basis-dependent.
    This is intentionally a *diagnostic* pull (ignoring correlations) to identify
    suspicious bins / mapping issues.
    """
    resid = np.asarray(resid, float)
    cov = np.asarray(cov, float)
    diag = np.diag(cov)
    sigma = np.sqrt(np.maximum(diag, 1e-30))
    pull = resid / sigma
    idx = np.argsort(-np.abs(pull))[: max(int(topk), 1)]
    return [(int(i), float(pull[i]), float(resid[i])) for i in idx]


@dataclass(frozen=True)
class ArtifactPaths:
    run_id: str
    logs_root: Path

    @property
    def run_root(self) -> Path:
        return self.logs_root

    def find_one(self, pattern: str) -> Path | None:
        matches = list(self.logs_root.glob(pattern))
        if not matches:
            return None
        # If multiple, pick deterministic (sorted path)
        return sorted(matches)[0]


def _md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    out = []
    out.append("| " + " | ".join(header) + " |")
    out.append("| " + " | ".join(["---"] * len(header)) + " |")
    for r in body:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def _fmt(x: float) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "nan"
    if abs(x) >= 1e4 or (abs(x) > 0 and abs(x) < 1e-3):
        return f"{x:.6g}"
    return f"{x:.6f}".rstrip("0").rstrip(".")


def analyze_weak(csv_path: Path, *, label: str, topk: int, systfrac: float, sigma_floor: float) -> str:
    df = pd.read_csv(csv_path)
    required = {"channel", "obs", "pred_sm", "pred_geo"}
    missing = required - set(df.columns)
    if missing:
        return f"## WEAK ({label})\n\nMissing columns in {csv_path}: {sorted(missing)}\n"

    obs = df["obs"].to_numpy(float)
    pred_sm = df["pred_sm"].to_numpy(float)
    pred_geo = df["pred_geo"].to_numpy(float)

    chi2_sm_loose = chi2_gauss_loose(obs, pred_sm, systfrac=systfrac, sigma_floor=sigma_floor)
    chi2_geo_loose = chi2_gauss_loose(obs, pred_geo, systfrac=systfrac, sigma_floor=sigma_floor)
    dchi2_loose = chi2_sm_loose - chi2_geo_loose

    chi2_sm_pois = chi2_poisson_deviance(obs, pred_sm)
    chi2_geo_pois = chi2_poisson_deviance(obs, pred_geo)
    dchi2_pois = chi2_sm_pois - chi2_geo_pois

    tot_obs = float(np.sum(obs))
    tot_pred = float(np.sum(pred_sm))
    ratio = (tot_obs / tot_pred) if tot_pred != 0 else float("nan")

    # Per-channel breakdown (loose)
    rows = [["channel", "bins", "sum(obs)", "sum(pred_sm)", "chi2_sm_loose", "chi2_geo_loose", "dchi2_loose"]]
    for ch, g in df.groupby("channel", sort=True):
        o = g["obs"].to_numpy(float)
        psm = g["pred_sm"].to_numpy(float)
        pgeo = g["pred_geo"].to_numpy(float)
        rows.append(
            [
                str(ch),
                str(len(g)),
                _fmt(float(np.sum(o))),
                _fmt(float(np.sum(psm))),
                _fmt(chi2_gauss_loose(o, psm, systfrac=systfrac, sigma_floor=sigma_floor)),
                _fmt(chi2_gauss_loose(o, pgeo, systfrac=systfrac, sigma_floor=sigma_floor)),
                _fmt(chi2_gauss_loose(o, psm, systfrac=systfrac, sigma_floor=sigma_floor)
                     - chi2_gauss_loose(o, pgeo, systfrac=systfrac, sigma_floor=sigma_floor)),
            ]
        )

    # Top contributors (global)
    contrib_sm = (obs - pred_sm) ** 2 / (np.maximum(pred_sm, 1.0) + (systfrac * pred_sm) ** 2 + sigma_floor**2)
    contrib_geo = (obs - pred_geo) ** 2 / (np.maximum(pred_geo, 1.0) + (systfrac * pred_geo) ** 2 + sigma_floor**2)

    def _topk(contrib: np.ndarray) -> pd.DataFrame:
        idx = np.argsort(-contrib)[: max(int(topk), 1)]
        out = df.loc[idx, ["channel", "i", "E_ctr", "obs", "pred_sm", "pred_geo"]].copy()
        out["contrib"] = contrib[idx]
        return out

    top_sm = _topk(contrib_sm)
    top_geo = _topk(contrib_geo)

    out = []
    out.append(f"## WEAK ({label})")
    out.append("")
    out.append(f"- source_csv: {csv_path.as_posix()}")
    out.append(f"- totals: sum(obs)={_fmt(tot_obs)}  sum(pred_sm)={_fmt(tot_pred)}  obs/pred_sm={_fmt(ratio)}")
    out.append(f"- loose-chi2: chi2_SM={_fmt(chi2_sm_loose)}  chi2_GEO={_fmt(chi2_geo_loose)}  dchi2={_fmt(dchi2_loose)}  (systfrac={systfrac}, sigma_floor={sigma_floor})")
    out.append(f"- poisson-dev: chi2_SM={_fmt(chi2_sm_pois)}  chi2_GEO={_fmt(chi2_geo_pois)}  dchi2={_fmt(dchi2_pois)}")
    out.append("")
    out.append("**Per-channel (loose-chi2)**")
    out.append(_md_table(rows))
    out.append("")
    out.append(f"**Top {topk} loose-chi2 contributors (SM)**")
    out.append(_md_table(
        [["channel", "i", "E_ctr", "obs", "pred_sm", "pred_geo", "contrib"]]
        + [[
            str(r.channel),
            str(int(r.i)),
            _fmt(float(r.E_ctr)),
            _fmt(float(r.obs)),
            _fmt(float(r.pred_sm)),
            _fmt(float(r.pred_geo)),
            _fmt(float(r.contrib)),
        ] for r in top_sm.itertuples(index=False)]
    ))
    out.append("")
    out.append(_md_table(
        [["channel", "i", "E_ctr", "obs", "pred_sm", "pred_geo", "contrib"]]
        + [[
            str(r.channel),
            str(int(r.i)),
            _fmt(float(r.E_ctr)),
            _fmt(float(r.obs)),
            _fmt(float(r.pred_sm)),
            _fmt(float(r.pred_geo)),
            _fmt(float(r.contrib)),
        ] for r in top_geo.itertuples(index=False)]
    ))
    out.append("")
    return "\n".join(out) + "\n"


def analyze_em(summary_json: Path, pred_csv: Path, *, label: str, topk: int) -> str:
    s = _read_json(summary_json)
    df = pd.read_csv(pred_csv)

    obs_col = None
    for c in ["obs_pb", "obs"]:
        if c in df.columns:
            obs_col = c
            break
    if obs_col is None:
        return f"## EM ({label})\n\nMissing obs column in {pred_csv}.\n"

    cov_csv = Path(s["io"]["cov_csv"])
    cov = _load_cov_matrix(cov_csv)

    obs = df[obs_col].to_numpy(float)
    pred_sm = df["pred_sm"].to_numpy(float)
    pred_geo = df["pred_geo"].to_numpy(float)

    resid_sm = obs - pred_sm
    resid_geo = obs - pred_geo

    chi2_sm = chi2_from_cov(resid_sm, cov)
    chi2_geo = chi2_from_cov(resid_geo, cov)

    pulls = topk_bin_pulls(resid_sm, cov, topk=topk)

    out = []
    out.append(f"## EM ({label})")
    out.append("")
    out.append(f"- summary_json: {summary_json.as_posix()}")
    out.append(f"- pred_csv: {pred_csv.as_posix()}")
    out.append(f"- cov_csv: {cov_csv.as_posix()}  (choice={s['io'].get('cov_choice')})")
    out.append(f"- ndof(summary): {s['chi2'].get('ndof')}")
    out.append(f"- chi2(recomputed): sm={_fmt(chi2_sm)}  geo={_fmt(chi2_geo)}  delta={_fmt(chi2_sm-chi2_geo)}")
    out.append("")
    out.append(f"**Top {topk} |pull| bins (diag(cov) pull; diagnostic)**")
    out.append(_md_table(
        [["i", "pull", "resid", "cos_ctr", "obs", "pred_sm"]]
        + [[
            str(i),
            _fmt(p),
            _fmt(r),
            _fmt(float(df.loc[i, 'cos_ctr'])) if 'cos_ctr' in df.columns else "",
            _fmt(float(obs[i])),
            _fmt(float(pred_sm[i])),
        ] for (i, p, r) in pulls]
    ))
    out.append("\nNote: With correlated systematics, per-bin pulls are only diagnostic; the official chi2 is the full cov form.")
    out.append("")
    return "\n".join(out) + "\n"


def analyze_strong(summary_json: Path, pred_csv: Path, *, label: str, topk: int) -> str:
    s = _read_json(summary_json)
    df = pd.read_csv(pred_csv)

    # Decide observable kind + columns.
    kind = None
    obs_col = None
    pred_single = None
    pred_sm = None
    pred_geo = None

    if "sigma_tot_data_mb" in df.columns:
        kind = "sigma_tot"
        obs_col = "sigma_tot_data_mb"
        if "sigma_tot_pred_mb_sm" in df.columns and "sigma_tot_pred_mb_geo" in df.columns:
            pred_sm = "sigma_tot_pred_mb_sm"
            pred_geo = "sigma_tot_pred_mb_geo"
        elif "sigma_tot_pred_mb" in df.columns:
            pred_single = "sigma_tot_pred_mb"
    elif "rho_data" in df.columns:
        kind = "rho"
        obs_col = "rho_data"
        if "rho_pred_sm" in df.columns and "rho_pred_geo" in df.columns:
            pred_sm = "rho_pred_sm"
            pred_geo = "rho_pred_geo"
        elif "rho_pred" in df.columns:
            pred_single = "rho_pred"
    elif "rho_pred" in df.columns and "rho" in df.columns and "rho_data" not in df.columns:
        # Legacy alternate naming
        kind = "rho"
        obs_col = "rho"
        pred_single = "rho_pred"

    if kind is None or obs_col is None or (pred_single is None and (pred_sm is None or pred_geo is None)):
        return f"## STRONG ({label})\n\nCould not infer obs/pred columns from {pred_csv}.\n"

    obs = df[obs_col].to_numpy(float)

    cov_sigma_csv = s.get("io", {}).get("cov_sigma_tot_csv")
    cov_rho_csv = s.get("io", {}).get("cov_rho_csv")
    cov_csv = cov_sigma_csv if kind == "sigma_tot" else cov_rho_csv
    cov = _load_cov_matrix(Path(cov_csv)) if cov_csv else None

    def _chi2_for(pred_arr: np.ndarray) -> tuple[float, list[tuple[int, float, float]]]:
        resid = obs - pred_arr
        pulls: list[tuple[int, float, float]] = []
        if cov is not None:
            chi2 = chi2_from_cov(resid, cov)
            pulls = topk_bin_pulls(resid, cov, topk=topk)
            return chi2, pulls

        # Fall back to diagonal uncertainties if present.
        unc_col = None
        for c in ["rho_unc", "sigma_tot_unc_mb", "unc", "err", "err_mb"]:
            if c in df.columns:
                unc_col = c
                break
        if unc_col is not None:
            unc = df[unc_col].to_numpy(float)
            pull = resid / np.maximum(unc, 1e-30)
            chi2 = float(np.sum(pull**2))
            idx = np.argsort(-np.abs(pull))[: max(int(topk), 1)]
            pulls = [(int(i), float(pull[i]), float(resid[i])) for i in idx]
            return chi2, pulls

        return float("nan"), []

    chi2_sm: float | None = None
    chi2_geo: float | None = None
    chi2_single: float | None = None
    pulls: list[tuple[int, float, float]] = []

    if pred_single is not None:
        pred = df[pred_single].to_numpy(float)
        chi2_single, pulls = _chi2_for(pred)
    else:
        if pred_sm is None or pred_geo is None:
            return f"## STRONG ({label})\n\nInternal error: missing pred_sm/pred_geo columns.\n"
        pred_sm_col = str(pred_sm)
        pred_geo_col = str(pred_geo)
        pred_sm_arr = df[pred_sm_col].to_numpy(float)
        pred_geo_arr = df[pred_geo_col].to_numpy(float)
        chi2_sm, pulls = _chi2_for(pred_sm_arr)
        chi2_geo, _ = _chi2_for(pred_geo_arr)

    out = []
    out.append(f"## STRONG ({label})")
    out.append("")
    out.append(f"- summary_json: {summary_json.as_posix()}")
    out.append(f"- pred_csv: {pred_csv.as_posix()}")
    if cov_csv:
        out.append(f"- cov_csv: {Path(cov_csv).as_posix()}")
    out.append(f"- ndof(summary): {s['chi2'].get('ndof')}")
    if chi2_single is not None:
        out.append(f"- chi2(recomputed): {_fmt(float(chi2_single))}")
    else:
        dchi2 = (chi2_sm - chi2_geo) if (chi2_sm is not None and chi2_geo is not None) else float("nan")
        out.append(f"- chi2(recomputed): sm={_fmt(float(chi2_sm))}  geo={_fmt(float(chi2_geo))}  delta={_fmt(float(dchi2))}")

    if pulls:
        out.append("")
        out.append(f"**Top {topk} |pull| points (diag(cov) pull; diagnostic)**")
        out.append(_md_table(
            [["i", "pull", "resid", "sqrts_GeV", "obs", "pred"]]
            + [[
                str(i),
                _fmt(p),
                _fmt(r),
                _fmt(float(df.loc[i, 'sqrts_GeV'])) if 'sqrts_GeV' in df.columns else "",
                _fmt(float(obs[i])),
                _fmt(float(df.loc[i, pred_single]))
                if pred_single is not None
                else _fmt(float(df.loc[i, pred_sm_col])),
            ] for (i, p, r) in pulls]
        ))
    out.append("")
    return "\n".join(out) + "\n"


def write_strong_pointwise_breakdown(
    summary_json: Path,
    pred_csv: Path,
    *,
    out_csv: Path,
    out_json: Path | None = None,
    topk: int = 12,
) -> dict:
    """Write a per-point diagnostic breakdown for STRONG SM vs GEO.

    This is intentionally *diagnostic*: it uses either the provided covariance
    matrix when it is diagonal (diag-only contributions) or falls back to any
    per-point uncertainty column. With correlated covariances, per-bin
    contributions are not unique; in that case we still report diag(cov)
    contributions as an approximation.
    """

    s = _read_json(summary_json)
    df = pd.read_csv(pred_csv)

    # Infer columns (must be dual-run to form delta breakdown)
    kind = None
    obs_col = None
    pred_sm_col = None
    pred_geo_col = None

    if "sigma_tot_data_mb" in df.columns and "sigma_tot_pred_mb_sm" in df.columns and "sigma_tot_pred_mb_geo" in df.columns:
        kind = "sigma_tot"
        obs_col = "sigma_tot_data_mb"
        pred_sm_col = "sigma_tot_pred_mb_sm"
        pred_geo_col = "sigma_tot_pred_mb_geo"
    elif "rho_data" in df.columns and "rho_pred_sm" in df.columns and "rho_pred_geo" in df.columns:
        kind = "rho"
        obs_col = "rho_data"
        pred_sm_col = "rho_pred_sm"
        pred_geo_col = "rho_pred_geo"
    else:
        raise ValueError(f"Need dual-run columns in {pred_csv} (SM+GEO predictions)")

    obs = df[obs_col].to_numpy(float)
    pred_sm = df[pred_sm_col].to_numpy(float)
    pred_geo = df[pred_geo_col].to_numpy(float)

    resid_sm = obs - pred_sm
    resid_geo = obs - pred_geo

    cov_sigma_csv = s.get("io", {}).get("cov_sigma_tot_csv")
    cov_rho_csv = s.get("io", {}).get("cov_rho_csv")
    cov_csv = cov_sigma_csv if kind == "sigma_tot" else cov_rho_csv

    # Determine per-point variance for diag contributions.
    var_diag: np.ndarray | None = None
    cov_diag_only = False
    cov_offdiag_max = None

    if cov_csv:
        cov = _load_cov_matrix(Path(cov_csv))
        diag = np.diag(cov).astype(float)
        off = cov - np.diag(diag)
        cov_offdiag_max = float(np.max(np.abs(off))) if off.size else 0.0
        denom = float(np.max(np.abs(diag))) if diag.size else 0.0
        # Heuristic: treat as diagonal if off-diagonals are numerically tiny.
        cov_diag_only = (cov_offdiag_max <= 1e-12 * max(denom, 1.0))
        var_diag = np.maximum(diag, 1e-30)

    if var_diag is None:
        unc_col = None
        for c in ["sigma_tot_unc_mb", "rho_unc", "unc", "err", "err_mb"]:
            if c in df.columns:
                unc_col = c
                break
        if unc_col is None:
            raise ValueError(f"No cov_csv in summary and no uncertainty column in {pred_csv}")
        unc = df[unc_col].to_numpy(float)
        var_diag = np.maximum(unc, 1e-30) ** 2

    contrib_sm = (resid_sm**2) / var_diag
    contrib_geo = (resid_geo**2) / var_diag
    dcontrib = contrib_sm - contrib_geo

    out_df = df.copy()
    out_df["obs"] = obs
    out_df["pred_sm"] = pred_sm
    out_df["pred_geo"] = pred_geo
    out_df["resid_sm"] = resid_sm
    out_df["resid_geo"] = resid_geo
    out_df["var_diag"] = var_diag
    out_df["chi2_contrib_sm_diag"] = contrib_sm
    out_df["chi2_contrib_geo_diag"] = contrib_geo
    out_df["dchi2_contrib_diag"] = dcontrib

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)

    n = int(len(out_df))
    d_total = float(np.sum(dcontrib))
    d_pos = float(np.sum(dcontrib[dcontrib > 0]))
    d_neg = float(np.sum(dcontrib[dcontrib < 0]))
    n_pos = int(np.sum(dcontrib > 0))
    n_neg = int(np.sum(dcontrib < 0))
    frac_pos = (n_pos / n) if n else float("nan")

    # Concentration of *improvement* (positive delta) among top points.
    pos_sorted = np.sort(dcontrib[dcontrib > 0])[::-1]
    def _top_share(k: int) -> float:
        if pos_sorted.size == 0 or d_pos == 0.0:
            return float("nan")
        return float(np.sum(pos_sorted[:k]) / d_pos)

    breakdown = {
        "kind": kind,
        "n_points": n,
        "delta_chi2_diag_total": d_total,
        "delta_chi2_diag_pos_sum": d_pos,
        "delta_chi2_diag_neg_sum": d_neg,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "frac_pos": frac_pos,
        "top1_share_of_pos": _top_share(1),
        "top3_share_of_pos": _top_share(3),
        "top5_share_of_pos": _top_share(5),
        "cov_csv": str(cov_csv) if cov_csv else None,
        "cov_diag_only_heuristic": bool(cov_diag_only) if cov_csv else None,
        "cov_offdiag_max": cov_offdiag_max,
        "pred_csv": str(pred_csv),
        "summary_json": str(summary_json),
        "out_csv": str(out_csv),
    }

    if out_json is not None:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(breakdown, indent=2, sort_keys=True), encoding="utf-8")
        breakdown["out_json"] = str(out_json)

    # Also include quick top-k lists (by improvement and degradation)
    tmp = out_df.reset_index(drop=False).rename(columns={"index": "i"})
    tmp["i"] = np.arange(len(tmp), dtype=int)

    top_imp = tmp.sort_values("dchi2_contrib_diag", ascending=False).head(max(int(topk), 1))
    top_bad = tmp.sort_values("dchi2_contrib_diag", ascending=True).head(max(int(topk), 1))

    keep_cols = [
        "i",
        "sqrts_GeV" if "sqrts_GeV" in tmp.columns else None,
        "obs",
        "pred_sm",
        "pred_geo",
        "resid_sm",
        "resid_geo",
        "chi2_contrib_sm_diag",
        "chi2_contrib_geo_diag",
        "dchi2_contrib_diag",
    ]
    keep_cols = [c for c in keep_cols if c is not None and c in tmp.columns]

    breakdown["top_improvements"] = [
        {k: (float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v)
         for k, v in row.items() if k in keep_cols}
        for row in top_imp[keep_cols].to_dict(orient="records")
    ]
    breakdown["top_degradations"] = [
        {k: (float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v)
         for k, v in row.items() if k in keep_cols}
        for row in top_bad[keep_cols].to_dict(orient="records")
    ]

    return breakdown


def analyze_dm_holdout_cv(summary_json: Path, cv_csv: Path) -> str:
    s = _read_json(summary_json)
    df = pd.read_csv(cv_csv)

    uniq_A = sorted(set(float(x) for x in df.get("A_best", pd.Series([], dtype=float)).tolist()))
    max_dtest = float(np.max(np.abs(df["delta_chi2_test"].to_numpy(float)))) if "delta_chi2_test" in df.columns else float("nan")
    max_dtrain = float(np.max(np.abs(df["delta_chi2_train"].to_numpy(float)))) if "delta_chi2_train" in df.columns else float("nan")

    out = []
    out.append("## DM (C2 holdout CV)")
    out.append("")
    out.append(f"- summary_json: {summary_json.as_posix()}")
    out.append(f"- cv_csv: {cv_csv.as_posix()}")
    out.append(f"- params: A_min={s['params'].get('A_min')}  A_max={s['params'].get('A_max')}  nA={s['params'].get('nA')}  kfold={s['params'].get('kfold')}")
    out.append(f"- A_best(unique): {uniq_A}")
    out.append(f"- max |delta_chi2_train| across folds: {_fmt(max_dtrain)}")
    out.append(f"- max |delta_chi2_test| across folds: {_fmt(max_dtest)}")

    if len(uniq_A) == 1 and abs(uniq_A[0]) < 1e-15:
        out.append("- interpretation: A collapses to 0 in every fold -> either (a) A has near-zero effect under current scoring/dynamics, or (b) scoring/clamps make A ineffective.")

    out.append("")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Fit-free one-for-all real-data diagnostics from logs/<sector>/<run_id>/artifacts.")
    ap.add_argument("--run_id", default="2026-03-03_run02")
    ap.add_argument("--logs_root", default="logs")
    ap.add_argument("--out", default=None, help="Markdown output path (default logs/ONEFORALL_DIAGNOSTICS_<run_id>.md)")
    ap.add_argument("--topk", type=int, default=8)

    # WEAK-only knobs for alternative distance definitions (no fitting)
    ap.add_argument("--weak_systfrac", type=float, default=0.0)
    ap.add_argument("--weak_sigma_floor", type=float, default=0.0)

    args = ap.parse_args()

    logs_root = Path(args.logs_root)
    run_id = str(args.run_id)
    out_path = Path(args.out) if args.out else (logs_root / f"ONEFORALL_DIAGNOSTICS_{run_id}.md")

    apaths = ArtifactPaths(run_id=run_id, logs_root=logs_root)

    # Resolve artifact paths deterministically
    weak_phase = apaths.find_one(f"weak/{run_id}/*/artifacts/t2k_phase_map.csv")
    weak_gksl = apaths.find_one(f"weak/{run_id}/*/artifacts/t2k_gksl_dynamics.csv")

    em_bhabha_sum = apaths.find_one(f"em/{run_id}/*/artifacts/bhabha_summary.json")
    em_bhabha_csv = apaths.find_one(f"em/{run_id}/*/artifacts/bhabha_pred.csv")
    em_mumu_sum = apaths.find_one(f"em/{run_id}/*/artifacts/mumu_summary.json")
    em_mumu_csv = apaths.find_one(f"em/{run_id}/*/artifacts/mumu_pred.csv")

    strong_sigma_sum = apaths.find_one(f"strong/{run_id}/*/artifacts/sigma_tot_summary.json")
    strong_sigma_csv = apaths.find_one(f"strong/{run_id}/*/artifacts/sigma_tot_pred.csv")
    strong_rho_sum = apaths.find_one(f"strong/{run_id}/*/artifacts/rho_summary.json")
    strong_rho_csv = apaths.find_one(f"strong/{run_id}/*/artifacts/rho_pred.csv")

    dm_cv_sum = apaths.find_one(f"dm/{run_id}/*/artifacts/dm_c2_cv_summary.json")
    dm_cv_csv = apaths.find_one(f"dm/{run_id}/*/artifacts/dm_c2_cv.csv")

    sections: list[str] = []
    sections.append(f"# One-for-all real-data diagnostics ({run_id})\n")
    sections.append("This report is **fit-free**: it does not optimize parameters. It only audits scoring definitions and highlights where mismatch concentrates.\n")

    # WEAK
    if weak_phase is not None:
        sections.append(analyze_weak(weak_phase, label="phase-map (fixedbyclaude)", topk=args.topk, systfrac=args.weak_systfrac, sigma_floor=args.weak_sigma_floor))
    else:
        sections.append("## WEAK (phase-map)\n\nMissing artifact t2k_phase_map.csv\n")

    if weak_gksl is not None:
        sections.append(analyze_weak(weak_gksl, label="GKSL dynamics", topk=args.topk, systfrac=args.weak_systfrac, sigma_floor=args.weak_sigma_floor))
    else:
        sections.append("## WEAK (GKSL dynamics)\n\nMissing artifact t2k_gksl_dynamics.csv\n")

    # EM
    if em_bhabha_sum is not None and em_bhabha_csv is not None:
        sections.append(analyze_em(em_bhabha_sum, em_bhabha_csv, label="Bhabha", topk=args.topk))
    else:
        sections.append("## EM (Bhabha)\n\nMissing artifacts\n")

    if em_mumu_sum is not None and em_mumu_csv is not None:
        sections.append(analyze_em(em_mumu_sum, em_mumu_csv, label="MuMu", topk=args.topk))
    else:
        sections.append("## EM (MuMu)\n\nMissing artifacts\n")

    # STRONG
    if strong_sigma_sum is not None and strong_sigma_csv is not None:
        sections.append(analyze_strong(strong_sigma_sum, strong_sigma_csv, label="sigma_tot", topk=args.topk))
    else:
        sections.append("## STRONG (sigma_tot)\n\nMissing artifacts\n")

    if strong_rho_sum is not None and strong_rho_csv is not None:
        sections.append(analyze_strong(strong_rho_sum, strong_rho_csv, label="rho", topk=args.topk))
    else:
        sections.append("## STRONG (rho)\n\nMissing artifacts\n")

    # DM
    if dm_cv_sum is not None and dm_cv_csv is not None:
        sections.append(analyze_dm_holdout_cv(dm_cv_sum, dm_cv_csv))
    else:
        sections.append("## DM (C2 holdout CV)\n\nMissing artifacts\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(sections), encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
