#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DM thread integrity-pack v1 driver.

Single-command driver that runs three DM proxy ablations using
`dm_holdout_cv_thread.py`:

- THREAD_ONLY: env_model=thread, poison env_scale calls
- INTERNAL_ONLY: env_model=global, poison thread env calls
- FULL: env_model=global_thread

This is an integrity/closure deliverable (prove the ablations are real and
cannot silently fall back). It is not a performance/fit claim.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_and_capture(
    cmd: list[str],
    *,
    env: dict[str, str],
    run_dir: Path,
    command_txt: str = "command.txt",
    terminal_txt: str = "terminal_output_and_exit_code.txt",
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_text(run_dir / command_txt, " ".join(cmd).rstrip() + "\n")
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    blob = []
    blob.append(f"rc={r.returncode}")
    blob.append("--- STDOUT ---")
    blob.append(r.stdout.rstrip())
    blob.append("--- STDERR ---")
    blob.append(r.stderr.rstrip())
    _write_text(run_dir / terminal_txt, "\n".join(blob).rstrip() + "\n")
    if r.returncode != 0:
        raise RuntimeError(
            "DM integrity-pack run failed\n"
            f"cmd={' '.join(cmd)}\n"
            f"rc={r.returncode}\n"
            f"STDOUT:\n{r.stdout}\n"
            f"STDERR:\n{r.stderr}\n"
        )


@dataclass(frozen=True)
class _Mode:
    key: str
    title: str
    env_model: str
    poison_env: dict[str, str]
    expect_env_scale: bool
    expect_thread_env: bool


def _integrity_checks(*, summary: dict[str, Any], mode: _Mode) -> tuple[bool, list[str]]:
    tel = summary.get("telemetry", {})
    used = tel.get("env_components_used", {})
    poison = tel.get("poison", {})

    problems: list[str] = []

    eff = used.get("effective_env_model")
    if eff != mode.env_model:
        problems.append(f"effective_env_model={eff} (expected {mode.env_model})")

    if bool(used.get("env_scale")) is not bool(mode.expect_env_scale):
        problems.append(f"env_scale_used={used.get('env_scale')} (expected {mode.expect_env_scale})")
    if bool(used.get("thread_env")) is not bool(mode.expect_thread_env):
        problems.append(f"thread_env_used={used.get('thread_env')} (expected {mode.expect_thread_env})")

    # Poison evidence (only assert for vars we set in this mode)
    for k, v in mode.poison_env.items():
        if poison.get(k) != v:
            problems.append(f"poison[{k}]={poison.get(k)} (expected {v})")

    return (len(problems) == 0), problems


def _fmt_scorecard_block(*, mode: _Mode, summary: dict[str, Any]) -> str:
    io = summary.get("io", {})
    tel = summary.get("telemetry", {})
    params = summary.get("params", {})

    ok, problems = _integrity_checks(summary=summary, mode=mode)
    used = tel.get("env_components_used", {})
    poison = tel.get("poison", {})
    d = tel.get("delta_chi2_test", {})

    lines: list[str] = []
    lines.append(f"## {mode.title}")
    lines.append("")
    lines.append(f"- env_model: {params.get('env_model')}")
    lines.append(f"- points_csv: {io.get('points_csv')}")
    lines.append(f"- kfold: {params.get('kfold')}  seed: {params.get('seed')}")
    lines.append(f"- integrity_ok: {ok}")
    lines.append(
        "- env_components_used: "
        f"env_scale={used.get('env_scale')} thread_env={used.get('thread_env')} effective={used.get('effective_env_model')}"
    )
    lines.append(
        "- poison: "
        f"DM_POISON_ENV_SCALE_CALLS={poison.get('DM_POISON_ENV_SCALE_CALLS')} "
        f"DM_POISON_THREAD_ENV_CALLS={poison.get('DM_POISON_THREAD_ENV_CALLS')} "
        f"DM_POISON_PROXY_CALLS={poison.get('DM_POISON_PROXY_CALLS')}"
    )
    lines.append(f"- all_folds_delta_test_positive: {tel.get('all_folds_delta_test_positive')}")
    lines.append(f"- delta_chi2_test.min: {d.get('min')}  max: {d.get('max')}  mean: {d.get('mean')}")
    lines.append(f"- stability_not_accuracy: {summary.get('framing', {}).get('stability_not_accuracy')}")
    if problems:
        lines.append("- problems: " + " | ".join(problems))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        "--out_dir",
        dest="out_dir",
        default=str(_repo_root() / "out" / "dm_thread_integrity_v1"),
        help="Output directory (default: out/dm_thread_integrity_v1)",
    )
    ap.add_argument(
        "--points_csv",
        default=str(_repo_root() / "data" / "sparc" / "sparc_points.csv"),
        help="Input points CSV (default: data/sparc/sparc_points.csv)",
    )
    ap.add_argument("--kfold", type=int, default=5)
    ap.add_argument("--seed", type=int, default=2026)

    # Scan-free defaults: exercise env plumbing without fit/scan claims.
    ap.add_argument("--A", type=float, default=0.0)
    ap.add_argument("--alpha", type=float, default=0.0)

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    points_csv = Path(args.points_csv).resolve()
    if not points_csv.exists():
        raise FileNotFoundError(f"points_csv not found: {points_csv}")

    modes = [
        _Mode(
            key="thread_only",
            title="THREAD_ONLY (env_model=thread, poison env_scale)",
            env_model="thread",
            poison_env={"DM_POISON_ENV_SCALE_CALLS": "1"},
            expect_env_scale=False,
            expect_thread_env=True,
        ),
        _Mode(
            key="internal_only",
            title="INTERNAL_ONLY (env_model=global, poison thread env)",
            env_model="global",
            poison_env={"DM_POISON_THREAD_ENV_CALLS": "1"},
            expect_env_scale=True,
            expect_thread_env=False,
        ),
        _Mode(
            key="full",
            title="FULL (env_model=global_thread)",
            env_model="global_thread",
            poison_env={},
            expect_env_scale=True,
            expect_thread_env=True,
        ),
    ]

    env_base = dict(os.environ)

    summaries: dict[str, dict[str, Any]] = {}
    for mode in modes:
        run_dir = out_dir / mode.key
        run_dir.mkdir(parents=True, exist_ok=True)

        out_csv = run_dir / "dm_cv.csv"
        out_json = run_dir / "dm_cv_summary.json"

        env = dict(env_base)
        env.update(mode.poison_env)
        # Be explicit: if a poison var is not used for this mode, keep it off.
        if "DM_POISON_ENV_SCALE_CALLS" not in mode.poison_env:
            env.pop("DM_POISON_ENV_SCALE_CALLS", None)
        if "DM_POISON_THREAD_ENV_CALLS" not in mode.poison_env:
            env.pop("DM_POISON_THREAD_ENV_CALLS", None)

        cmd = [
            sys.executable,
            str(_repo_root() / "dm_holdout_cv_thread.py"),
            "--points_csv",
            str(points_csv),
            "--model",
            "geo_add_const",
            "--g0",
            "1.2e-10",
            "--env_model",
            str(mode.env_model),
            "--A_min",
            str(float(args.A)),
            "--A_max",
            str(float(args.A)),
            "--nA",
            "1",
            "--alpha_min",
            str(float(args.alpha)),
            "--alpha_max",
            str(float(args.alpha)),
            "--nAlpha",
            "1",
            "--kfold",
            str(int(args.kfold)),
            "--seed",
            str(int(args.seed)),
            "--out_csv",
            str(out_csv),
            "--out_json",
            str(out_json),
        ]

        _run_and_capture(cmd, env=env, run_dir=run_dir)
        summaries[mode.key] = _load_json(out_json)

    scorecard = out_dir / "DM_THREAD_INTEGRITY_SCORECARD.md"
    lines: list[str] = []
    lines.append("# DM thread integrity scorecard (v1)")
    lines.append("")
    lines.append("Produced by `run_dm_thread_integrity_pack_v1.py`.")
    lines.append("Integrity/closure artifact; not a performance claim.")
    lines.append("")
    lines.append(f"- points_csv: {str(points_csv)}")
    lines.append(f"- kfold: {int(args.kfold)}  seed: {int(args.seed)}")
    lines.append(f"- scan_free: A={float(args.A)}  alpha={float(args.alpha)}")
    lines.append("")

    for mode in modes:
        lines.append(_fmt_scorecard_block(mode=mode, summary=summaries[mode.key]))

    _write_text(scorecard, "\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
