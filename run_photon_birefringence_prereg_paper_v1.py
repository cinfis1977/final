#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_holdout_template(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser(description="Paper-faithful photon birefringence prereg runner")
    ap.add_argument("--holdout_csv", default=str(_repo_root() / "integration_artifacts" / "entanglement_photon_bridge" / "birefringence_holdouts_v1_TEMPLATE.csv"))
    ap.add_argument("--skyfold_csv", default=None, help="Optional source table with sky-coordinate data for local sky-fold recomputation")
    ap.add_argument("--skyfold_coord_col", default=None, help="Optional sky-fold coordinate column, e.g. dec_deg or b_deg")
    ap.add_argument("--skyfold_beta_col", default=None, help="Optional observable column for sky-fold recomputation")
    ap.add_argument("--skyfold_sigma_col", default=None, help="Optional uncertainty column for sky-fold recomputation")
    ap.add_argument("--out_dir", default=str(_repo_root() / "out" / "photon_paper"))
    ap.add_argument("--prefix", default="photon_birefringence_prereg_paper_v1")
    ap.add_argument("--Om", type=float, default=0.315)
    ap.add_argument("--Ol", type=float, default=0.685)
    ap.add_argument("--Or", type=float, default=0.0)
    ap.add_argument("--cmb_beta_cal_deg", type=float, default=0.34)
    ap.add_argument("--cmb_sigma_cal_deg", type=float, default=0.09)
    ap.add_argument("--cmb_beta_hold_deg", type=float, default=0.215)
    ap.add_argument("--cmb_sigma_hold_deg", type=float, default=0.074)
    ap.add_argument("--acc_z_cal", type=float, default=1100.0)
    ap.add_argument("--acc_beta_cal_deg", type=float, default=0.342)
    ap.add_argument("--acc_sigma_cal_deg", type=float, default=0.094)
    ap.add_argument("--acc_z_hold", type=float, default=2.5)
    ap.add_argument("--acc_beta_hold_deg", type=float, default=-0.8)
    ap.add_argument("--acc_sigma_hold_deg", type=float, default=2.2)
    ap.add_argument("--k_sigma", type=float, default=2.0)
    ap.add_argument("--paper_signed_pvalue", type=float, default=0.3603)
    ap.add_argument("--paper_absolute_pvalue", type=float, default=0.3936)
    ap.add_argument("--paper_skyfold_pvalue", type=float, default=0.1536)
    ap.add_argument("--skyfold_n_perm", type=int, default=20000)
    ap.add_argument("--skyfold_seed", type=int, default=20260307)
    args = ap.parse_args()

    repo = _repo_root()
    sys.path.insert(0, str((repo / "integration_artifacts").resolve()))
    from mastereq.photon_sector import cmb_prereg_locked_check, accumulation_prereg_locked_check, skyfold_anisotropy_prereg_check

    holdout_csv = Path(args.holdout_csv).resolve()
    holdout_rows = _read_holdout_template(holdout_csv)

    cmb = cmb_prereg_locked_check(
        beta_cal_deg=float(args.cmb_beta_cal_deg),
        sigma_cal_deg=float(args.cmb_sigma_cal_deg),
        beta_hold_deg=float(args.cmb_beta_hold_deg),
        sigma_hold_deg=float(args.cmb_sigma_hold_deg),
        k_sigma=float(args.k_sigma),
    )
    accumulation = accumulation_prereg_locked_check(
        z_cal=float(args.acc_z_cal),
        beta_cal_deg=float(args.acc_beta_cal_deg),
        sigma_cal_deg=float(args.acc_sigma_cal_deg),
        z_hold=float(args.acc_z_hold),
        beta_hold_deg=float(args.acc_beta_hold_deg),
        sigma_hold_deg=float(args.acc_sigma_hold_deg),
        Om=float(args.Om),
        Ol=float(args.Ol),
        Or=float(args.Or),
        k_sigma=float(args.k_sigma),
        abs_test=False,
    )

    skyfold_local = None
    if args.skyfold_csv:
        skyfold_csv = Path(args.skyfold_csv).resolve()
        sky_rows = _read_holdout_template(skyfold_csv)
        if not sky_rows:
            raise ValueError(f"No rows found in skyfold CSV: {skyfold_csv}")
        cols = list(sky_rows[0].keys())
        low = {c.lower(): c for c in cols}
        coord_col = args.skyfold_coord_col
        if coord_col is None:
            for cand in ["dec_deg", "declination_deg", "dec", "b_deg", "glat_deg", "lat_deg"]:
                if cand.lower() in low:
                    coord_col = low[cand.lower()]
                    break
        beta_col = args.skyfold_beta_col
        sigma_col = args.skyfold_sigma_col
        for cand in ["beta_deg", "alpha_deg", "beta", "alpha"]:
            if cand.lower() in low:
                if beta_col is None:
                    beta_col = low[cand.lower()]
                break
        for cand in ["sigma_deg", "err_deg", "sigma", "alpha_err_deg", "beta_err_deg"]:
            if cand.lower() in low:
                if sigma_col is None:
                    sigma_col = low[cand.lower()]
                break
        if coord_col is None or beta_col is None:
            raise ValueError(f"Could not detect sky-fold columns in {skyfold_csv}: coord={coord_col} beta={beta_col} sigma={sigma_col}")
        skyfold_local = skyfold_anisotropy_prereg_check(
            [float(r[coord_col]) for r in sky_rows],
            [float(r[beta_col]) for r in sky_rows],
            None if sigma_col is None else [float(r[sigma_col]) for r in sky_rows],
            n_perm=int(args.skyfold_n_perm),
            seed=int(args.skyfold_seed),
            abs_metric=False,
        )
        skyfold_local["source"] = str(skyfold_csv)
        skyfold_local["coord_col"] = coord_col
        skyfold_local["beta_col"] = beta_col
        skyfold_local["sigma_col"] = sigma_col if sigma_col is not None else ""

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / f"{args.prefix}_summary.json"
    report_path = out_dir / f"{args.prefix}_report.md"

    summary: dict[str, Any] = {
        "runner": "run_photon_birefringence_prereg_paper_v1.py",
        "layer": "paper-faithful",
        "claim_boundary": {
            "does": "Reproduces the locked bridge formulas used for the photon-sector prereg checks and records the paper-reference p-values.",
            "does_not": "Does not claim a unique microscopic derivation; this remains a bridge/scaffolding layer.",
        },
        "inputs": {
            "holdout_csv": str(holdout_csv),
            "holdout_sha256": _sha256(holdout_csv),
            "holdout_rows": holdout_rows,
        },
        "locked_cosmology": {"Om": float(args.Om), "Ol": float(args.Ol), "Or": float(args.Or)},
        "cmb_locked_check": cmb,
        "accumulation_locked_check": accumulation,
        "paper_reference_results": {
            "section": "paper/paper_final.md §4.11.5",
            "signed_pvalue": float(args.paper_signed_pvalue),
            "absolute_metric_pvalue": float(args.paper_absolute_pvalue),
            "skyfold_pvalue": float(args.paper_skyfold_pvalue),
            "note": "Paper-reference values remain the canonical benchmark. If a source table with sky coordinates is supplied, this wrapper records a local sky-fold recomputation separately.",
        },
        "skyfold_local_recompute": skyfold_local,
        "no_fit_statement": "No regression coefficient is fitted or tuned in this runner.",
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Photon paper-faithful prereg report\n",
        f"- holdout CSV: {holdout_csv}\n",
        f"- sha256: `{summary['inputs']['holdout_sha256']}`\n",
        "\n## Locked cosmology\n",
        f"- Om = {args.Om}\n",
        f"- Ol = {args.Ol}\n",
        f"- Or = {args.Or}\n",
        "\n## Exact locked-formula checks\n",
        f"- CMB locked z-score = {float(cmb['z_score']):.12g}\n",
        f"- accumulation locked z-score = {float(accumulation['z_score']):.12g}\n",
        "\n## Canonical paper reference p-values\n",
        f"- signed p-value ≈ {float(args.paper_signed_pvalue):.4f}\n",
        f"- absolute-metric p-value ≈ {float(args.paper_absolute_pvalue):.4f}\n",
        f"- sky-fold p-value ≈ {float(args.paper_skyfold_pvalue):.4f}\n",
    ]
    if skyfold_local is not None:
        lines.extend([
            "\n## Local sky-fold recomputation\n",
            f"- source = {skyfold_local['source']}\n",
            f"- coord_col = {skyfold_local['coord_col']}\n",
            f"- statistic = {float(skyfold_local['statistic']):.12g}\n",
            f"- p_value_signed = {float(skyfold_local['p_value_signed']):.12g}\n",
            f"- p_value_abs = {float(skyfold_local['p_value_abs']):.12g}\n",
        ])
    else:
        lines.extend([
            "\n## Local sky-fold recomputation\n",
            "- not run (no `--skyfold_csv` with sky-coordinate data was supplied)\n",
        ])
    lines.extend([
        "\n## Claim boundary\n",
        "- This is a bridge observable / prereg falsifier layer.\n",
        "- It does **not** claim a unique microphysical derivation.\n",
        "- No fit or tuning was performed.\n",
    ])
    report_path.write_text("".join(lines), encoding="utf-8")

    print(f"[WROTE] {summary_path}")
    print(f"[WROTE] {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
