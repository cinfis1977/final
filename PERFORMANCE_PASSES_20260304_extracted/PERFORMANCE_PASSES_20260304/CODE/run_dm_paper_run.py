#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DM paper-run mode.

Single-command driver that runs the DM holdout-CV runners (SPARC/RAR proxy) on
repo-hosted SPARC points and writes deterministic artifacts under out/.

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
            "DM paper run failed\n"
            f"cmd={' '.join(cmd)}\n"
            f"rc={r.returncode}\n"
            f"STDOUT:\n{r.stdout}\n"
            f"STDERR:\n{r.stderr}\n"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_block(title: str, summary: dict[str, Any]) -> str:
    io = summary.get("io", {})
    tel = summary.get("telemetry", {})
    p = summary.get("params", {})

    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"- points_csv: {io.get('points_csv')}")
    lines.append(f"- env_model: {p.get('env_model')}")
    lines.append(f"- kfold: {p.get('kfold')}  seed: {p.get('seed')}")
    lines.append(f"- data_loaded_from_paths: {io.get('data_loaded_from_paths')}")
    lines.append(f"- all_folds_delta_test_positive: {tel.get('all_folds_delta_test_positive')}")
    d = tel.get("delta_chi2_test", {})
    lines.append(f"- delta_chi2_test.min: {d.get('min')}")
    lines.append(f"- delta_chi2_test.max: {d.get('max')}")
    lines.append(f"- stability_not_accuracy: {summary.get('framing', {}).get('stability_not_accuracy')}")
    if tel.get("thread_calibration_used") is not None:
        lines.append(f"- thread_calibration_used: {tel.get('thread_calibration_used')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out_dir",
        default=str(_repo_root() / "out" / "dm_paper"),
        help="Output directory (default: out/dm_paper)",
    )
    ap.add_argument(
        "--points_csv",
        default=str(_repo_root() / "data" / "sparc" / "sparc_points.csv"),
        help="Input points CSV (default: data/sparc/sparc_points.csv)",
    )
    ap.add_argument("--kfold", type=int, default=5)
    ap.add_argument("--seed", type=int, default=2026)

    # Locked scan-free parameters (Codex canonical PASS mode).
    ap.add_argument("--A", type=float, default=0.1778279410)
    ap.add_argument("--alpha", type=float, default=0.001)

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)

    points_csv = Path(args.points_csv).resolve()

    stiff_csv = out_dir / "dm_cv_thread_STIFFGATE_fixed.csv"
    stiff_json = out_dir / "dm_cv_thread_STIFFGATE_summary.json"

    none_csv = out_dir / "dm_cv_none_fixed.csv"
    none_json = out_dir / "dm_cv_none_summary.json"

    report_md = out_dir / "paper_run_report.md"

    # Thread + STIFFGATE (explicit calibration branch)
    cmd_stiff = [
        sys.executable,
        str(_repo_root() / "dm_holdout_cv_thread_STIFFGATE.py"),
        "--points_csv",
        str(points_csv),
        "--model",
        "geo_add_const",
        "--g0",
        "1.2e-10",
        "--env_model",
        "thread",
        "--thread_mode",
        "down",
        "--thread_q",
        "0.6",
        "--thread_xi",
        "0.5",
        "--thread_norm",
        "median",
        "--thread_gate_p",
        "4",
        "--thread_k2",
        "1.0",
        "--thread_calibrate_from_galaxy",
        "--gal_hi_p",
        "99.9",
        "--gal_gate_eps",
        "1e-6",
        "--thread_Sc_factor",
        "10",
        "--A_min",
        str(args.A),
        "--A_max",
        str(args.A),
        "--nA",
        "1",
        "--alpha_min",
        str(args.alpha),
        "--alpha_max",
        str(args.alpha),
        "--nAlpha",
        "1",
        "--kfold",
        str(int(args.kfold)),
        "--seed",
        str(int(args.seed)),
        "--out_csv",
        str(stiff_csv),
        "--out_json",
        str(stiff_json),
    ]
    _run(cmd_stiff, env=env)

    # Env disabled branch
    cmd_none = [
        sys.executable,
        str(_repo_root() / "dm_holdout_cv_thread.py"),
        "--points_csv",
        str(points_csv),
        "--model",
        "geo_add_const",
        "--g0",
        "1.2e-10",
        "--env_model",
        "none",
        "--A_min",
        str(args.A),
        "--A_max",
        str(args.A),
        "--nA",
        "1",
        "--alpha_min",
        str(args.alpha),
        "--alpha_max",
        str(args.alpha),
        "--nAlpha",
        "1",
        "--kfold",
        str(int(args.kfold)),
        "--seed",
        str(int(args.seed)),
        "--out_csv",
        str(none_csv),
        "--out_json",
        str(none_json),
    ]
    _run(cmd_none, env=env)

    s_stiff = _load_json(stiff_json)
    s_none = _load_json(none_json)

    report_lines: list[str] = []
    report_lines.append("# DM paper run report")
    report_lines.append("")
    report_lines.append("This report is produced by `run_dm_paper_run.py`.")
    report_lines.append("It is an IO/closure + schema-stability artifact for the declared DM proxy; not a physical-accuracy claim.")
    report_lines.append("")
    report_lines.append(_fmt_block("DM thread + STIFFGATE", s_stiff))
    report_lines.append(_fmt_block("DM env_model=none", s_none))

    report_md.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
