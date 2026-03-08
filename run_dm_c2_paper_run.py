#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DM-C2 paper-run mode (real SPARC pack + DM-C1 dynamics runner).

This is a paper-facing IO/provenance artifact:
- builds a deterministic DM-C2 pack from repo SPARC points
- runs the DM dynamics runner in two order modes (forward/reverse)
- writes stable artifacts under out/

It is NOT a fit/accuracy claim.
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


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            "DM-C2 paper run failed\n"
            f"cmd={' '.join(cmd)}\n"
            f"rc={r.returncode}\n"
            f"STDOUT:\n{r.stdout}\n"
            f"STDERR:\n{r.stderr}\n"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_block(title: str, summary: dict[str, Any]) -> str:
    pack = summary.get("pack", {})
    chi2 = summary.get("chi2", {})
    tel = summary.get("telemetry", {})
    p = summary.get("params", {})

    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"- pack.schema_version: {pack.get('schema_version')}")
    lines.append(f"- pack.path: {pack.get('path')}")
    lines.append(f"- dt: {p.get('dt')}  n_steps: {p.get('n_steps')}  order_mode: {p.get('order_mode')}")
    lines.append(f"- chi2.total: {chi2.get('total')}  ndof: {chi2.get('ndof')}")
    b = tel.get("boundedness", {})
    lines.append(
        "- boundedness: "
        f"finite_all={b.get('finite_all')} "
        f"g_in_0_1={b.get('g_in_0_1')} "
        f"epsilon_nonneg={b.get('epsilon_nonneg')}"
    )
    poison = tel.get("poison", {})
    lines.append(f"- DM_POISON_PROXY_CALLS: {poison.get('DM_POISON_PROXY_CALLS')}")
    lines.append(f"- stability_not_accuracy: {summary.get('framing', {}).get('stability_not_accuracy')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out_dir",
        default=str(_repo_root() / "out" / "dm_c2_paper"),
        help="Output directory (default: out/dm_c2_paper)",
    )
    ap.add_argument(
        "--points_csv",
        default=str(_repo_root() / "data" / "sparc" / "sparc_points.csv"),
        help="Input points CSV (default: data/sparc/sparc_points.csv)",
    )
    ap.add_argument("--max_galaxies", type=int, default=5)
    ap.add_argument("--min_points", type=int, default=8)
    ap.add_argument("--seed", type=int, default=2026)

    # Suggested stable defaults for kpc/km/s scaling.
    ap.add_argument("--dt", type=float, default=1e-3)
    ap.add_argument("--n_steps", type=int, default=300)

    args = ap.parse_args()

    repo_root = _repo_root()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    points_csv = Path(args.points_csv).resolve()

    pack_path = out_dir / "pack_dm_c2_sparc.json"
    cfg = BuildConfig(max_galaxies=int(args.max_galaxies), min_points=int(args.min_points), seed=int(args.seed))
    pack = build_pack(points_csv, cfg=cfg)
    _write_json(pack_path, pack)

    env = dict(os.environ)
    env["DM_POISON_PROXY_CALLS"] = "1"

    fwd_csv = out_dir / "dm_c2_pred_forward.csv"
    fwd_json = out_dir / "dm_c2_summary_forward.json"
    rev_csv = out_dir / "dm_c2_pred_reverse.csv"
    rev_json = out_dir / "dm_c2_summary_reverse.json"

    cmd_base = [
        sys.executable,
        str(repo_root / "dm_dynamics_runner_c1.py"),
        "--pack",
        str(pack_path),
        "--dt",
        str(float(args.dt)),
        "--n_steps",
        str(int(args.n_steps)),
        "--seed",
        str(int(args.seed)),
    ]

    _run(cmd_base + ["--order_mode", "forward", "--out_csv", str(fwd_csv), "--out_json", str(fwd_json)], env=env)
    _run(cmd_base + ["--order_mode", "reverse", "--out_csv", str(rev_csv), "--out_json", str(rev_json)], env=env)

    s_fwd = _load_json(fwd_json)
    s_rev = _load_json(rev_json)

    report_md = out_dir / "paper_run_report.md"
    lines: list[str] = []
    lines.append("# DM-C2 paper run report")
    lines.append("")
    lines.append("This report is produced by `run_dm_c2_paper_run.py`.")
    lines.append("It is an IO/schema + runner-smoke artifact; not an accuracy claim.")
    lines.append("")
    lines.append(f"- points_csv: {points_csv}")
    lines.append(f"- n_galaxies: {len(pack.get('galaxies', []))}")
    lines.append(f"- pack_path: {pack_path}")
    lines.append("")
    lines.append(_fmt_block("DM-C2 forward", s_fwd))
    lines.append(_fmt_block("DM-C2 reverse", s_rev))
    report_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print("DM-C2 paper run OK")
    print("out_dir:", str(out_dir))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
