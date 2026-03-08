#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_ms_papersafe_strict_evidence_with_logs_v1.py

Runs MS paper-safe strict 3-arm pipeline(s) (raw_ppm prereg) and writes
reproducibility logs + a self-contained artifact copy under:

  logs/ms/<run_id>/
    cmd_01_.../command.txt
    cmd_01_.../terminal_output_and_exit_code.txt
    artifacts/out/MS/<run_id>/...

This is designed for upload/review workflows where we want explicit command
provenance and the exact produced artifacts.

Notes
- This script treats "PASS" as prereg-gate PASS (Layer A) + dynamics-integrity
  evidence presence (Layer B). It does not claim physical accuracy.
- The 3-arm driver internally runs the per-arm runner + finalizer via subprocess.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_and_log(*, cmd: list[str], cwd: Path, env: dict[str, str], out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_text(out_dir / "command.txt", " ".join(cmd) + "\n")

    r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    combined = []
    combined.append(f"exit_code: {r.returncode}")
    combined.append("\n=== STDOUT ===\n")
    combined.append(r.stdout or "")
    combined.append("\n=== STDERR ===\n")
    combined.append(r.stderr or "")
    _write_text(out_dir / "terminal_output_and_exit_code.txt", "\n".join(combined).rstrip() + "\n")
    return int(r.returncode)


def _ensure_exists(p: Path, label: str) -> None:
    if not p.exists():
        raise FileNotFoundError(f"Missing {label}: {p}")


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--logs_root",
        default=str(_repo_root() / "logs" / "ms"),
        help="Where to write command logs + artifact copies (default: logs/ms)",
    )

    ap.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use for subprocess runs (default: current)",
    )

    ap.add_argument(
        "--ablations",
        nargs="+",
        default=["internal_only", "full"],
        choices=["internal_only", "thread_only", "full"],
        help="Which ablation(s) to run (default: internal_only full)",
    )

    # Inputs (default to the repo-local copied real data inputs)
    ap.add_argument(
        "--mode_a1_points",
        default=str(_repo_root() / "out" / "particle_specific_cytofull_A1_B2" / "ModeA_points.csv"),
    )
    ap.add_argument(
        "--mode_b2_points",
        default=str(_repo_root() / "out" / "particle_specific_cytofull_A1_B2" / "ModeB_points.csv"),
    )
    ap.add_argument(
        "--mode_b3_points",
        default=str(_repo_root() / "out" / "particle_specific_cytofull_A1_B2_direct" / "ModeB_holdout_points.csv"),
    )
    ap.add_argument(
        "--mode_a2_points",
        default=str(_repo_root() / "out" / "particle_specific_cytofull_A2_B3" / "ModeA_points.csv"),
    )
    ap.add_argument(
        "--targets_csv",
        default=str(_repo_root() / "out" / "particle_specific_cytofull_A1_B2_direct" / "targets_used.csv"),
        help="Frozen targets CSV (default: out/particle_specific_cytofull_A1_B2_direct/targets_used.csv)",
    )

    ap.add_argument(
        "--run_id_prefix",
        default="ms_papersafe_raw_ppm",
        help="Prefix used to form run_id(s)",
    )

    args = ap.parse_args()

    root = _repo_root()
    logs_root = Path(args.logs_root).resolve()

    mode_a1 = Path(args.mode_a1_points).resolve()
    mode_b2 = Path(args.mode_b2_points).resolve()
    mode_b3 = Path(args.mode_b3_points).resolve()
    mode_a2 = Path(args.mode_a2_points).resolve()
    targets_csv = Path(args.targets_csv).resolve()

    _ensure_exists(mode_a1, "mode_a1_points")
    _ensure_exists(mode_b2, "mode_b2_points")
    _ensure_exists(mode_b3, "mode_b3_points")
    _ensure_exists(mode_a2, "mode_a2_points")
    _ensure_exists(targets_csv, "targets_csv")

    driver_py = (root / "run_ms_particle_specific_dynamic_3arm_v1_0.py").resolve()
    agg_py = (root / "ms_dynamics_integrity_aggregate_v1_DROPIN.py").resolve()

    _ensure_exists(driver_py, "3-arm driver")
    _ensure_exists(agg_py, "aggregator")

    env = dict(os.environ)

    # Two paper-safe strict modes:
    # 1) common baseline drift telemetry only
    # 2) common baseline + residual decomposition (still telemetry-only, prereg stays raw_ppm)
    run_specs = [
        ("raw_common", "telemetry_only_commonbaseline"),
        ("raw_common_resid", "telemetry_commonbaseline_plus_residual"),
    ]

    for suffix, drift_state_mode in run_specs:
        run_id = f"{args.run_id_prefix}_{suffix}_{_ts()}"
        run_log_dir = logs_root / run_id
        run_log_dir.mkdir(parents=True, exist_ok=True)

        # 1) Driver
        cmd_driver = [
            str(args.python),
            str(driver_py),
            "--run_id",
            run_id,
            "--mode_a1_points",
            str(mode_a1),
            "--mode_b2_points",
            str(mode_b2),
            "--mode_b3_points",
            str(mode_b3),
            "--mode_a2_points",
            str(mode_a2),
            "--targets_csv",
            str(targets_csv),
            "--prereg_observable",
            "raw_ppm",
            "--drift_state_mode",
            str(drift_state_mode),
            "--ablations",
            *[str(x) for x in args.ablations],
        ]

        rc = _run_and_log(
            cmd=cmd_driver,
            cwd=root,
            env=env,
            out_dir=run_log_dir / "cmd_01_run_driver",
        )
        if rc != 0:
            return rc

        # 2) Aggregator
        cmd_agg = [
            str(args.python),
            str(agg_py),
            "--run_id",
            run_id,
            "--root",
            ".",
        ]

        rc = _run_and_log(
            cmd=cmd_agg,
            cwd=root,
            env=env,
            out_dir=run_log_dir / "cmd_02_aggregate",
        )
        if rc != 0:
            return rc

        # 3) Copy artifacts (out/MS/<run_id>/...) into logs/ms/<run_id>/artifacts/... for upload
        src_out = (root / "out" / "MS" / run_id).resolve()
        _ensure_exists(src_out, f"out/MS/{run_id}")

        # Keep this path short to avoid Windows path length issues during copy.
        # (Nested output trees can be deep, and run_id is long.)
        dst_out = run_log_dir / "artifacts" / "out_MS"
        _copy_tree(src_out, dst_out)

        # Small run index for humans
        _write_text(
            run_log_dir / "RUN_INDEX.txt",
            "\n".join(
                [
                    f"run_id: {run_id}",
                    f"drift_state_mode: {drift_state_mode}",
                    f"prereg_observable: raw_ppm",
                    f"ablations: {' '.join(args.ablations)}",
                    f"artifacts_copied_from: {src_out}",
                    f"artifacts_copied_to: {dst_out}",
                ]
            )
            + "\n",
        )

    print("OK: wrote logs under", str(logs_root).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
