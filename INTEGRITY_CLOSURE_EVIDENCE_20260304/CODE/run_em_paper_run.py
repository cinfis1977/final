#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EM paper-run mode.

Single-command driver that runs the EM (Bhabha + mu+mu-) forward harnesses on
repo-hosted HEPData-derived packs and writes deterministic artifacts under out/.

This is an IO/closure + schema-stability deliverable (paper-facing ergonomics),
not an accuracy/fit claim.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            "EM paper run failed\n"
            f"cmd={' '.join(cmd)}\n"
            f"rc={r.returncode}\n"
            f"STDOUT:\n{r.stdout}\n"
            f"STDERR:\n{r.stderr}\n"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_block(title: str, summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"- pack: {summary.get('pack', {}).get('path')}")
    io = summary.get("io", {})
    lines.append(f"- data_loaded_from_paths: {io.get('data_loaded_from_paths')}")
    lines.append(f"- data_csv: {io.get('data_csv')}")
    lines.append(f"- cov_choice: {io.get('cov_choice')}")
    lines.append(f"- cov_csv: {io.get('cov_csv')}")
    chi2 = summary.get("chi2", {})
    lines.append(f"- chi2.sm: {chi2.get('sm')}")
    lines.append(f"- chi2.geo: {chi2.get('geo')}")
    lines.append(f"- chi2.delta: {chi2.get('delta')}")
    lines.append(f"- ndof: {chi2.get('ndof')}")
    lines.append(f"- stability_not_accuracy: {summary.get('framing', {}).get('stability_not_accuracy')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out_dir",
        default=str(_repo_root() / "out" / "em_paper"),
        help="Output directory (default: out/em_paper)",
    )
    ap.add_argument(
        "--cov",
        default="total",
        choices=["total", "stat", "sys_corr", "diag_total"],
        help="Covariance choice passed through to runners",
    )
    ap.add_argument("--A", type=float, default=0.0, help="GEO amplitude (0.0 for IO-closure paper run)")
    ap.add_argument(
        "--alpha",
        type=float,
        default=None,
        help="DEPRECATED (EM only): use --em_alpha_tshape. Kept for backward compatibility.",
    )
    ap.add_argument(
        "--em_alpha_tshape",
        type=float,
        default=7.5e-05,
        help="EM |t|-shape exponent for f(|t|) = (|t|/t_ref)**em_alpha_tshape.",
    )
    ap.add_argument("--phi", type=float, default=1.5707963267948966)
    ap.add_argument("--shape_only", action="store_true", help="Enable shape-only delta (recommended)")
    ap.add_argument("--freeze_betas", action="store_true", help="Freeze betas (recommended)")
    ap.add_argument("--beta_nonneg", action="store_true", help="Enforce nonnegative nuisance betas")
    ap.add_argument("--require_positive", action="store_true", help="Fail if any (1+delta)<=0")
    args = ap.parse_args()

    em_alpha_tshape = float(args.em_alpha_tshape) if args.alpha is None else float(args.alpha)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)

    bhabha_pack = (_repo_root() / "lep_bhabha_pack.json").resolve()
    mumu_pack = (_repo_root() / "lep_mumu_pack.json").resolve()

    bhabha_baseline_csv = (
        _repo_root() / "integration_artifacts" / "mastereq" / "packs" / "em_paper" / "bhabha_baseline_import.csv"
    ).resolve()

    bhabha_csv = out_dir / "bhabha_pred.csv"
    bhabha_json = out_dir / "bhabha_summary.json"
    bhabha_imp_csv = out_dir / "bhabha_import_pred.csv"
    bhabha_imp_json = out_dir / "bhabha_import_summary.json"
    mumu_csv = out_dir / "mumu_pred.csv"
    mumu_json = out_dir / "mumu_summary.json"
    report_md = out_dir / "paper_run_report.md"

    # Bhabha
    cmd_b = [
        sys.executable,
        str(_repo_root() / "em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py"),
        "--pack",
        str(bhabha_pack),
        "--cov",
        str(args.cov),
        "--A",
        str(args.A),
        "--em_alpha_tshape",
        str(em_alpha_tshape),
        "--phi",
        str(args.phi),
        "--out",
        str(bhabha_csv),
        "--out_json",
        str(bhabha_json),
    ]
    if args.shape_only:
        cmd_b.append("--shape_only")
    if args.freeze_betas:
        cmd_b.append("--freeze_betas")
    if args.beta_nonneg:
        cmd_b.append("--beta_nonneg")
    if args.require_positive:
        cmd_b.append("--require_positive")

    _run(cmd_b, env=env)

    # Bhabha (explicit baseline-import branch)
    cmd_bi = [
        sys.executable,
        str(_repo_root() / "em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py"),
        "--pack",
        str(bhabha_pack),
        "--cov",
        str(args.cov),
        "--A",
        str(args.A),
        "--em_alpha_tshape",
        str(em_alpha_tshape),
        "--phi",
        str(args.phi),
        "--baseline_csv",
        str(bhabha_baseline_csv),
        "--baseline_col",
        "pred_sm",
        "--out",
        str(bhabha_imp_csv),
        "--out_json",
        str(bhabha_imp_json),
    ]
    if args.shape_only:
        cmd_bi.append("--shape_only")
    if args.freeze_betas:
        cmd_bi.append("--freeze_betas")
    if args.beta_nonneg:
        cmd_bi.append("--beta_nonneg")
    if args.require_positive:
        cmd_bi.append("--require_positive")

    _run(cmd_bi, env=env)

    # MuMu
    cmd_m = [
        sys.executable,
        str(_repo_root() / "em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py"),
        "--pack",
        str(mumu_pack),
        "--cov",
        str(args.cov),
        "--A",
        str(args.A),
        "--em_alpha_tshape",
        str(em_alpha_tshape),
        "--phi",
        str(args.phi),
        "--out",
        str(mumu_csv),
        "--out_json",
        str(mumu_json),
    ]
    if args.shape_only:
        cmd_m.append("--shape_only")
    if args.freeze_betas:
        cmd_m.append("--freeze_betas")
    if args.beta_nonneg:
        cmd_m.append("--beta_nonneg")
    if args.require_positive:
        cmd_m.append("--require_positive")

    _run(cmd_m, env=env)

    s_b = _load_json(bhabha_json)
    s_bi = _load_json(bhabha_imp_json)
    s_m = _load_json(mumu_json)

    report_lines: list[str] = []
    report_lines.append("# EM paper run report")
    report_lines.append("")
    report_lines.append("This report is produced by `run_em_paper_run.py`.")
    report_lines.append("It is an IO/closure + schema-stability artifact for the declared EM proxy models; not a physical-accuracy claim.")
    report_lines.append("")
    report_lines.append(_fmt_block("Bhabha", s_b))
    report_lines.append(_fmt_block("Bhabha (baseline import)", s_bi))
    report_lines.append(_fmt_block("MuMu", s_m))

    report_md.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
