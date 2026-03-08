#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DM-C2 holdout/CV paper-run mode.

Produces deterministic artifacts under out/:
- builds a real-data DM-C2 pack from SPARC points
- runs galaxy-holdout k-fold CV with train-only A_dm calibration
- writes CSV + JSON summary + MD report

This is an IO/leakage-safety + schema-stability artifact; not an accuracy claim.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from dm_c2_build_sparc_pack_v1 import BuildConfig, build_pack


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            "DM-C2 CV paper run failed\n"
            f"cmd={' '.join(cmd)}\n"
            f"rc={r.returncode}\n"
            f"STDOUT:\n{r.stdout}\n"
            f"STDERR:\n{r.stderr}\n"
        )


def _fmt_block(summary: dict[str, Any]) -> str:
    tel = summary.get("telemetry", {})
    p = summary.get("params", {})
    pack = summary.get("pack", {})

    lines: list[str] = []
    lines.append("## DM-C2 holdout/CV")
    lines.append("")
    lines.append(f"- pack.schema_version: {pack.get('schema_version')}")
    lines.append(f"- pack.path: {pack.get('path')}")
    lines.append(f"- kfold: {p.get('kfold')}  seed: {p.get('seed')}")
    lines.append(f"- dt: {p.get('dt')}  n_steps: {p.get('n_steps')}  order_mode: {p.get('order_mode')}")
    lines.append(f"- A_grid: [{p.get('A_min')}, {p.get('A_max')}]  nA: {p.get('nA')}")
    d = tel.get("delta_chi2_test", {})
    lines.append(f"- delta_chi2_test.min: {d.get('min')}")
    lines.append(f"- delta_chi2_test.max: {d.get('max')}")
    lines.append(f"- leakage_guard_disjoint_train_test: {tel.get('leakage_guard_disjoint_train_test')}")
    poison = tel.get("poison", {})
    lines.append(f"- DM_POISON_PROXY_CALLS: {poison.get('DM_POISON_PROXY_CALLS')}")
    lines.append(f"- stability_not_accuracy: {summary.get('framing', {}).get('stability_not_accuracy')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out_dir",
        default=str(_repo_root() / "out" / "dm_c2_cv_paper"),
        help="Output directory (default: out/dm_c2_cv_paper)",
    )
    ap.add_argument(
        "--points_csv",
        default=str(_repo_root() / "data" / "sparc" / "sparc_points.csv"),
        help="Input points CSV (default: data/sparc/sparc_points.csv)",
    )
    ap.add_argument("--max_galaxies", type=int, default=8)
    ap.add_argument("--min_points", type=int, default=8)

    ap.add_argument("--kfold", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2026)

    ap.add_argument("--dt", type=float, default=0.001)
    ap.add_argument("--n_steps", type=int, default=240)
    ap.add_argument("--order_mode", default="forward", choices=["forward", "reverse", "shuffle"])
    ap.add_argument("--sigma_floor", type=float, default=1e-6)

    ap.add_argument("--A_min", type=float, default=0.0)
    ap.add_argument("--A_max", type=float, default=0.2)
    ap.add_argument("--nA", type=int, default=21)

    args = ap.parse_args()

    repo_root = _repo_root()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    points_csv = Path(args.points_csv).resolve()

    pack_path = out_dir / "pack_dm_c2_sparc.json"
    cfg = BuildConfig(max_galaxies=int(args.max_galaxies), min_points=int(args.min_points), seed=int(args.seed))
    pack = build_pack(points_csv, cfg=cfg)
    _write_json(pack_path, pack)

    out_csv = out_dir / "dm_c2_cv.csv"
    out_json = out_dir / "dm_c2_cv_summary.json"

    env = dict(os.environ)
    env["DM_POISON_PROXY_CALLS"] = "1"

    cmd = [
        sys.executable,
        str(repo_root / "dm_holdout_cv_dynamics_c2.py"),
        "--pack",
        str(pack_path),
        "--kfold",
        str(int(args.kfold)),
        "--seed",
        str(int(args.seed)),
        "--dt",
        str(float(args.dt)),
        "--n_steps",
        str(int(args.n_steps)),
        "--order_mode",
        str(args.order_mode),
        "--sigma_floor",
        str(float(args.sigma_floor)),
        "--A_min",
        str(float(args.A_min)),
        "--A_max",
        str(float(args.A_max)),
        "--nA",
        str(int(args.nA)),
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]

    _run(cmd, env=env)

    summary = _load_json(out_json)

    report_md = out_dir / "paper_run_report.md"
    lines: list[str] = []
    lines.append("# DM-C2 holdout/CV paper run report")
    lines.append("")
    lines.append("This report is produced by `run_dm_c2_cv_paper_run.py`.")
    lines.append("It is a leakage-safety + determinism artifact; not an accuracy claim.")
    lines.append("")
    lines.append(f"- points_csv: {points_csv}")
    lines.append(f"- pack_path: {pack_path}")
    lines.append(f"- out_csv: {out_csv}")
    lines.append(f"- out_json: {out_json}")
    lines.append("")
    lines.append(_fmt_block(summary))
    report_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print("DM-C2 CV paper run OK")
    print("out_dir:", str(out_dir))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
