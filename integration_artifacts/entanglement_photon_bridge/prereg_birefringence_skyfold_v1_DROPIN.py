#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_INTEGRATION_ROOT = _REPO_ROOT / "integration_artifacts"
if str(_INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_ROOT))

from mastereq.photon_sector import skyfold_anisotropy_prereg_check


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _auto_col(columns: list[str], candidates: list[str]) -> str | None:
    low = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None


def _float(r: dict[str, str], key: str) -> float:
    return float(r[key])


def main() -> int:
    ap = argparse.ArgumentParser(description="Photon birefringence sky-fold prereg falsifier")
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--coord_col", default=None, help="Sky fold coordinate column, e.g. dec_deg or b_deg")
    ap.add_argument("--beta_col", default=None)
    ap.add_argument("--sigma_col", default=None, help="Optional uncertainty column. If omitted, uniform weights are used.")
    ap.add_argument("--n_perm", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--abs_metric", action="store_true")
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_json", default=None)
    args = ap.parse_args()

    in_csv = Path(args.in_csv)
    rows = _read_csv(in_csv)
    if not rows:
        raise ValueError(f"No rows found in {in_csv}")
    cols = list(rows[0].keys())
    coord_col = args.coord_col or _auto_col(cols, ["dec_deg", "declination_deg", "dec", "b_deg", "glat_deg", "lat_deg"])
    beta_col = args.beta_col or _auto_col(cols, ["beta_deg", "alpha_deg", "beta", "alpha"])
    sigma_col = args.sigma_col or _auto_col(cols, ["sigma_deg", "err_deg", "sigma", "alpha_err_deg", "beta_err_deg"])
    if coord_col is None or beta_col is None:
        raise ValueError(f"Could not detect required columns. coord={coord_col} beta={beta_col} sigma={sigma_col} cols={cols}")

    sigma_vals = None if sigma_col is None else [_float(r, sigma_col) for r in rows]

    result = skyfold_anisotropy_prereg_check(
        [_float(r, coord_col) for r in rows],
        [_float(r, beta_col) for r in rows],
        sigma_vals,
        n_perm=int(args.n_perm),
        seed=int(args.seed),
        abs_metric=bool(args.abs_metric),
    )
    result["in_csv"] = str(in_csv)
    result["coord_col"] = coord_col
    result["beta_col"] = beta_col
    result["sigma_col"] = sigma_col if sigma_col is not None else ""

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(result.keys()))
        w.writeheader()
        w.writerow(result)

    if args.out_json:
        out_json = Path(args.out_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("=== BIREFRINGENCE SKY-FOLD PREREG (NO FIT) ===")
    print(f"IN_CSV={in_csv}")
    print(f"FOLD_COORD={coord_col}")
    print(f"N_TOTAL={result['n_total']} N_POS={result['n_pos']} N_NEG={result['n_neg']}")
    print(f"STAT={result['statistic']}")
    print(f"P_SIGNED={result['p_value_signed']}")
    print(f"P_ABS={result['p_value_abs']}")
    print(f"VERDICT={result['verdict']}")
    print(f"OUT_CSV={out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
