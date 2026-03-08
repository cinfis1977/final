#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def _col(rows: list[dict[str, str]], name: str) -> np.ndarray:
    return np.asarray([float(r[name]) for r in rows], dtype=float)


def _perm_pvalues(values: np.ndarray, side: np.ndarray, *, seed: int, n_perm: int) -> tuple[float, float, float, int, int]:
    n_pos = int(np.sum(side))
    n_neg = int(np.sum(~side))
    if n_pos == 0 or n_neg == 0:
        raise ValueError("partition must place rows on both sides")

    stat = float(np.mean(values[side]) - np.mean(values[~side]))
    rng = np.random.default_rng(int(seed))
    idx = np.arange(values.size)
    perm_stats = np.empty(int(n_perm), dtype=float)
    for i in range(int(n_perm)):
        rng.shuffle(idx)
        perm_side = side[idx]
        perm_stats[i] = float(np.mean(values[perm_side]) - np.mean(values[~perm_side]))

    if stat >= 0.0:
        p_signed = float(np.mean(perm_stats >= stat))
    else:
        p_signed = float(np.mean(perm_stats <= stat))
    p_abs = float(np.mean(np.abs(perm_stats) >= abs(stat)))
    return stat, p_signed, p_abs, n_pos, n_neg


def _ra_hemi_side(ra_deg: np.ndarray, center_deg: float) -> np.ndarray:
    return np.cos(np.deg2rad(ra_deg - float(center_deg))) >= 0.0


def _finite_mask(*arrs: Iterable[float]) -> np.ndarray:
    arr_list = [np.asarray(a, dtype=float) for a in arrs]
    mask = np.ones(arr_list[0].shape, dtype=bool)
    for arr in arr_list:
        mask &= np.isfinite(arr)
    return mask


def main() -> None:
    ap = argparse.ArgumentParser(description="Sky-fold provenance diagnostic scan for birefringence tables")
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--coord_col", default="qso_dec_deg")
    ap.add_argument("--beta_col", default="delta_wrap90_deg")
    ap.add_argument("--ra_col", default="qso_ra_deg")
    ap.add_argument("--target_p", type=float, default=0.1536)
    ap.add_argument("--top_k", type=int, default=12)
    ap.add_argument("--n_perm", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--out_md", required=True)
    args = ap.parse_args()

    in_csv = Path(args.in_csv)
    rows = _load_rows(in_csv)
    if not rows:
        raise SystemExit(f"No rows found in {in_csv}")

    dec = _col(rows, args.coord_col)
    beta_signed = _col(rows, args.beta_col)
    ra = _col(rows, args.ra_col)
    beta_abs = np.abs(beta_signed)

    mask = _finite_mask(dec, beta_signed, ra)
    dec = dec[mask]
    beta_signed = beta_signed[mask]
    beta_abs = beta_abs[mask]
    ra = ra[mask]
    if dec.size < 2:
        raise SystemExit("Need at least two finite rows")

    results: list[dict[str, float | int | str]] = []

    thresholds = sorted(set(float(x) for x in dec.tolist()))
    for thr in thresholds:
        side = dec >= thr
        for metric, values in (("signed", beta_signed), ("abs", beta_abs)):
            try:
                stat, p_signed, p_abs, n_pos, n_neg = _perm_pvalues(values, side, seed=args.seed, n_perm=args.n_perm)
            except ValueError:
                continue
            results.append({
                "partition_family": "dec_threshold",
                "partition_rule": f"{args.coord_col} >= {thr:.6f}",
                "metric": metric,
                "statistic": stat,
                "p_value_signed": p_signed,
                "p_value_abs": p_abs,
                "distance_to_target_abs_p": abs(p_abs - float(args.target_p)),
                "n_pos": n_pos,
                "n_neg": n_neg,
            })

    for center in range(360):
        side = _ra_hemi_side(ra, center)
        for metric, values in (("signed", beta_signed), ("abs", beta_abs)):
            try:
                stat, p_signed, p_abs, n_pos, n_neg = _perm_pvalues(values, side, seed=args.seed, n_perm=args.n_perm)
            except ValueError:
                continue
            results.append({
                "partition_family": "ra_hemisphere",
                "partition_rule": f"cos({args.ra_col} - {center} deg) >= 0",
                "metric": metric,
                "statistic": stat,
                "p_value_signed": p_signed,
                "p_value_abs": p_abs,
                "distance_to_target_abs_p": abs(p_abs - float(args.target_p)),
                "n_pos": n_pos,
                "n_neg": n_neg,
                "center_deg": center,
            })

    results.sort(key=lambda r: float(r["distance_to_target_abs_p"]))
    top = results[: max(1, int(args.top_k))]

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "in_csv": str(in_csv),
                "coord_col": args.coord_col,
                "beta_col": args.beta_col,
                "ra_col": args.ra_col,
                "target_p": float(args.target_p),
                "n_perm": int(args.n_perm),
                "seed": int(args.seed),
                "n_rows": int(dec.size),
                "top_matches": top,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "# Photon sky-fold provenance diagnostic\n",
        f"- input = {in_csv}\n",
        f"- coord_col = {args.coord_col}\n",
        f"- beta_col = {args.beta_col}\n",
        f"- ra_col = {args.ra_col}\n",
        f"- target paper p-value = {float(args.target_p):.4f}\n",
        f"- n_rows = {int(dec.size)}\n",
        f"- permutation null = {int(args.n_perm)} shuffles, seed {int(args.seed)}\n",
        "\n## Closest partitions\n",
    ]
    for i, row in enumerate(top, start=1):
        lines.extend([
            f"\n### {i}. {row['partition_family']}\n",
            f"- rule = {row['partition_rule']}\n",
            f"- metric = {row['metric']}\n",
            f"- statistic = {float(row['statistic']):.12g}\n",
            f"- p_value_signed = {float(row['p_value_signed']):.12g}\n",
            f"- p_value_abs = {float(row['p_value_abs']):.12g}\n",
            f"- |p_abs - target| = {float(row['distance_to_target_abs_p']):.12g}\n",
            f"- n_pos = {int(row['n_pos'])}, n_neg = {int(row['n_neg'])}\n",
        ])
    lines.extend([
        "\n## Interpretation boundary\n",
        "- This is a provenance diagnostic only.\n",
        "- A numerically close partition does not prove canonical identity.\n",
        "- Canonical status still requires an archived source table plus exact fold-rule evidence tied to the paper benchmark.\n",
    ])

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("".join(lines), encoding="utf-8")

    print("=== SKY-FOLD PROVENANCE DIAGNOSTIC ===")
    print(f"IN_CSV={in_csv}")
    print(f"TARGET_P={float(args.target_p):.6g}")
    if top:
        best = top[0]
        print(f"BEST_RULE={best['partition_rule']}")
        print(f"BEST_METRIC={best['metric']}")
        print(f"BEST_P_ABS={float(best['p_value_abs']):.12g}")
    print(f"OUT_JSON={out_json}")
    print(f"OUT_MD={out_md}")


if __name__ == "__main__":
    main()
