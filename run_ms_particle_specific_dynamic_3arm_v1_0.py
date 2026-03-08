#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_ms_particle_specific_dynamic_3arm_v1_0.py

Single-command 3-arm driver for the Mass Spectrometry particle-specific pipeline,
using the explicit-dynamics runner:
  - discovery:  A1–B2
  - holdout:    A1–B3
  - third-arm:  A2–B3

For each requested ablation, this:
  1) runs `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py` for each arm
  2) runs the prereg finalizer
       runners/particle_specific_finalize_from_runs_v1_0_DROPIN/finalize_particle_specific_goodppm_lock_from_runs_v1_0.py

Outputs (default): out/MS/<run_id>/<ablation>/...

This is an IO/closure + integrity-gated execution harness.
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


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            "MS 3-arm run failed\n"
            f"cmd={' '.join(cmd)}\n"
            f"rc={r.returncode}\n"
            f"STDOUT:\n{r.stdout}\n"
            f"STDERR:\n{r.stderr}\n"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stem(p: Path) -> str:
    return p.name[: -len("".join(p.suffixes))] if p.suffixes else p.name


def _run_arm(
    *,
    runner_py: Path,
    out_dir: Path,
    points_a: Path,
    points_b: Path,
    targets_csv: Path,
    baseline: str,
    ablation: str,
    alpha: float,
    alpha_g_floor: float,
    window_ppm: float,
    good_ppm: float,
    tail3_ppm: float,
    min_n: int,
    max_bins: int,
    clip_g: bool,
    require_stateful: bool,
    prereg_observable: str,
    drift_state_mode: str,
    env: dict[str, str],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(runner_py),
        "--inputs",
        str(points_a),
        str(points_b),
        "--out_dir",
        str(out_dir),
        "--targets_csv",
        str(targets_csv),
        "--baseline",
        str(baseline),
        "--ablation",
        str(ablation),
        "--alpha",
        str(float(alpha)),
        "--alpha_g_floor",
        str(float(alpha_g_floor)),
        "--window_ppm",
        str(float(window_ppm)),
        "--good_ppm",
        str(float(good_ppm)),
        "--tail3_ppm",
        str(float(tail3_ppm)),
        "--min_n",
        str(int(min_n)),
        "--max_bins",
        str(int(max_bins)),
        "--prereg_observable",
        str(prereg_observable),
        "--drift_state_mode",
        str(drift_state_mode),
    ]
    if clip_g:
        cmd.append("--clip_g")
    if require_stateful:
        cmd.append("--require_stateful_dynamics")

    _run(cmd, cwd=_repo_root(), env=env)


def _finalize(
    *,
    finalizer_py: Path,
    out_dir: Path,
    pair_b2_dir: Path,
    pair_b3_dir: Path,
    third_arm_dir: Path,
    targets_used_csv: Path,
    good_ppm: float,
    window_ppm: float,
    tail3_ppm: float,
    min_n: int,
    max_bins: int,
    mode_a_points: Path | None,
    mode_b2_points: Path | None,
    mode_b3_points: Path | None,
    mode_a2_points: Path | None,
    env: dict[str, str],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(finalizer_py),
        "--root",
        ".",
        "--pair_b2_dir",
        str(pair_b2_dir),
        "--pair_b3_dir",
        str(pair_b3_dir),
        "--third_arm_dir",
        str(third_arm_dir),
        "--targets_csv",
        str(targets_used_csv),
        "--out_dir",
        str(out_dir),
        "--good_ppm",
        str(float(good_ppm)),
        "--window_ppm",
        str(float(window_ppm)),
        "--tail3_ppm",
        str(float(tail3_ppm)),
        "--min_n",
        str(int(min_n)),
        "--max_bins",
        str(int(max_bins)),
    ]

    if mode_a_points is not None:
        cmd += ["--mode_a_points", str(mode_a_points)]
    if mode_b2_points is not None:
        cmd += ["--mode_b2_points", str(mode_b2_points)]
    if mode_b3_points is not None:
        cmd += ["--mode_b3_points", str(mode_b3_points)]
    if mode_a2_points is not None:
        cmd += ["--mode_a2_points", str(mode_a2_points)]

    _run(cmd, cwd=_repo_root(), env=env)


def main() -> int:
    ap = argparse.ArgumentParser(description="MS particle-specific dynamics 3-arm driver")

    ap.add_argument("--run_id", required=True, help="Folder label under out/MS/<run_id>/...")
    ap.add_argument("--out_root", default=str(_repo_root() / "out" / "MS"), help="Root output dir (default: out/MS)")

    ap.add_argument("--mode_a1_points", required=True, help="Points/peaks CSV for mode A1")
    ap.add_argument("--mode_b2_points", required=True, help="Points/peaks CSV for mode B2")
    ap.add_argument("--mode_b3_points", required=True, help="Points/peaks CSV for mode B3 (holdout)")
    ap.add_argument("--mode_a2_points", required=True, help="Points/peaks CSV for mode A2 (third arm)")
    ap.add_argument("--targets_csv", required=True, help="Frozen targets CSV (or targets_used.csv from a prior run)")

    ap.add_argument(
        "--ablations",
        nargs="+",
        default=["internal_only", "thread_only", "full"],
        choices=["internal_only", "thread_only", "full"],
        help="Which ablation(s) to run (default: internal_only thread_only full)",
    )

    ap.add_argument("--alpha", type=float, default=0.30)
    ap.add_argument("--alpha_g_floor", type=float, default=0.25)

    ap.add_argument("--window_ppm", type=float, default=30.0)
    ap.add_argument("--good_ppm", type=float, default=3.0)
    ap.add_argument("--tail3_ppm", type=float, default=-300000.0)
    ap.add_argument("--min_n", type=int, default=8)
    ap.add_argument("--max_bins", type=int, default=8)

    ap.add_argument("--clip_g", action="store_true")

    ap.add_argument(
        "--prereg_observable",
        default="raw_ppm",
        choices=["raw_ppm", "corrected_ppm"],
        help="Prereg observable passed to strict runner (default: raw_ppm; legacy-compatible).",
    )
    ap.add_argument(
        "--drift_state_mode",
        default="telemetry_only_commonbaseline",
        choices=["telemetry_only_commonbaseline", "telemetry_commonbaseline_plus_residual"],
        help="Telemetry/audit mode passed to strict runner (default: telemetry_only_commonbaseline).",
    )
    ap.add_argument(
        "--no_require_stateful",
        action="store_true",
        help="Do not enforce stateful dynamics for INTERNAL_ONLY/FULL (not recommended for evidence runs)",
    )

    args = ap.parse_args()

    root = _repo_root()
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    mode_a1 = Path(args.mode_a1_points).resolve()
    mode_b2 = Path(args.mode_b2_points).resolve()
    mode_b3 = Path(args.mode_b3_points).resolve()
    mode_a2 = Path(args.mode_a2_points).resolve()
    targets_csv = Path(args.targets_csv).resolve()

    runner_py = root / "ms_particle_specific_dynamic_runner_v1_0_DROPIN.py"
    finalizer_py = root / "runners" / "particle_specific_finalize_from_runs_v1_0_DROPIN" / "finalize_particle_specific_goodppm_lock_from_runs_v1_0.py"

    if not runner_py.exists():
        raise FileNotFoundError(f"Missing runner: {runner_py}")
    if not finalizer_py.exists():
        raise FileNotFoundError(f"Missing finalizer: {finalizer_py}")

    # Baselines are derived from filename stem under setting_from=filename.
    baseline_a1 = _stem(mode_a1)
    baseline_a2 = _stem(mode_a2)

    env = dict(os.environ)

    for ablation in args.ablations:
        base_dir = out_root / str(args.run_id) / str(ablation)
        arm_discovery = base_dir / "A1_B2"
        arm_holdout = base_dir / "A1_B3_holdout"
        arm_third = base_dir / "A2_B3_thirdarm"
        final_dir = base_dir / "final"

        require_stateful = (not bool(args.no_require_stateful)) and (ablation in ("internal_only", "full"))

        _run_arm(
            runner_py=runner_py,
            out_dir=arm_discovery,
            points_a=mode_a1,
            points_b=mode_b2,
            targets_csv=targets_csv,
            baseline=baseline_a1,
            ablation=ablation,
            alpha=float(args.alpha),
            alpha_g_floor=float(args.alpha_g_floor),
            window_ppm=float(args.window_ppm),
            good_ppm=float(args.good_ppm),
            tail3_ppm=float(args.tail3_ppm),
            min_n=int(args.min_n),
            max_bins=int(args.max_bins),
            clip_g=bool(args.clip_g),
            require_stateful=require_stateful,
            prereg_observable=str(args.prereg_observable),
            drift_state_mode=str(args.drift_state_mode),
            env=env,
        )

        _run_arm(
            runner_py=runner_py,
            out_dir=arm_holdout,
            points_a=mode_a1,
            points_b=mode_b3,
            targets_csv=targets_csv,
            baseline=baseline_a1,
            ablation=ablation,
            alpha=float(args.alpha),
            alpha_g_floor=float(args.alpha_g_floor),
            window_ppm=float(args.window_ppm),
            good_ppm=float(args.good_ppm),
            tail3_ppm=float(args.tail3_ppm),
            min_n=int(args.min_n),
            max_bins=int(args.max_bins),
            clip_g=bool(args.clip_g),
            require_stateful=require_stateful,
            prereg_observable=str(args.prereg_observable),
            drift_state_mode=str(args.drift_state_mode),
            env=env,
        )

        _run_arm(
            runner_py=runner_py,
            out_dir=arm_third,
            points_a=mode_a2,
            points_b=mode_b3,
            targets_csv=targets_csv,
            baseline=baseline_a2,
            ablation=ablation,
            alpha=float(args.alpha),
            alpha_g_floor=float(args.alpha_g_floor),
            window_ppm=float(args.window_ppm),
            good_ppm=float(args.good_ppm),
            tail3_ppm=float(args.tail3_ppm),
            min_n=int(args.min_n),
            max_bins=int(args.max_bins),
            clip_g=bool(args.clip_g),
            require_stateful=require_stateful,
            prereg_observable=str(args.prereg_observable),
            drift_state_mode=str(args.drift_state_mode),
            env=env,
        )

        # Use targets_used.csv from discovery arm for canonical record.
        targets_used = arm_discovery / "targets_used.csv"
        if not targets_used.exists():
            raise FileNotFoundError(f"Missing targets_used.csv in discovery arm: {targets_used}")

        _finalize(
            finalizer_py=finalizer_py,
            out_dir=final_dir,
            pair_b2_dir=arm_discovery,
            pair_b3_dir=arm_holdout,
            third_arm_dir=arm_third,
            targets_used_csv=targets_used,
            good_ppm=float(args.good_ppm),
            window_ppm=float(args.window_ppm),
            tail3_ppm=float(args.tail3_ppm),
            min_n=int(args.min_n),
            max_bins=int(args.max_bins),
            mode_a_points=mode_a1,
            mode_b2_points=mode_b2,
            mode_b3_points=mode_b3,
            mode_a2_points=mode_a2,
            env=env,
        )

        # Small run-level index for convenience.
        index = {
            "run_id": str(args.run_id),
            "ablation": str(ablation),
            "paths": {
                "discovery": str(arm_discovery).replace("\\", "/"),
                "holdout": str(arm_holdout).replace("\\", "/"),
                "third_arm": str(arm_third).replace("\\", "/"),
                "final": str(final_dir).replace("\\", "/"),
            },
        }
        (base_dir / "RUN_INDEX.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
