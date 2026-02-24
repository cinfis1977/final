"""Golden check for the DM prereg runners (SPARC/RAR).

Purpose
- Re-run the *canonical* DM prereg commands from tools/verdict_commands.txt
  but write outputs under integration_artifacts/out/ so the main project
  outputs are not overwritten.
- Verify the prereg PASS rule: all folds have delta_chi2_test > 0.

This script does NOT change any physics; it only executes the DM runners and
checks their CSV outputs.

Usage (from repo root):
  python integration_artifacts/scripts/dm_prereg_golden_check.py

Notes
- Canonical runners:
    - dm_holdout_cv_thread_STIFFGATE.py  (env_model=thread + galaxy-closed gate)
    - dm_holdout_cv_thread.py            (env_model=none baseline)
- Canonical inputs:
    - data/sparc/sparc_points.csv
    - A=0.1778279410038923, alpha=0.001, kfold=5, seed=2026
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "integration_artifacts" / "out" / "dm_prereg_golden"

A_DM = 0.1778279410038923
ALPHA_DM = 0.001
SEED = 2026
KFOLD = 5


def run_cmd(cmd: list[str]) -> None:
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def check_csv(path: Path) -> dict:
    df = pd.read_csv(path)
    if "delta_chi2_test" not in df.columns:
        raise RuntimeError(f"Missing delta_chi2_test column in {path}")

    deltas = df["delta_chi2_test"].astype(float)
    all_positive = bool((deltas > 0).all())

    summary = {
        "path": str(path),
        "n_folds": int(len(df)),
        "min_delta_chi2_test": float(deltas.min()),
        "max_delta_chi2_test": float(deltas.max()),
        "all_delta_chi2_test_positive": all_positive,
    }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip_run", action="store_true", help="Only check existing CSVs; do not re-run the DM scripts")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    points_csv = REPO_ROOT / "data" / "sparc" / "sparc_points.csv"
    if not points_csv.exists():
        raise FileNotFoundError(points_csv)

    out_thread = OUT_DIR / "dm_cv_thread_STIFFGATE_FIXED_A01778_a0001_seed2026_k5.csv"
    out_none = OUT_DIR / "dm_cv_NONE_FIXED_A01778_a0001_seed2026_k5.csv"

    if not args.skip_run:
        # THREAD env (STIFFGATE) - canonical prereg
        cmd_thread = [
            sys.executable,
            "dm_holdout_cv_thread_STIFFGATE.py",
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
            str(A_DM),
            "--A_max",
            str(A_DM),
            "--nA",
            "1",
            "--alpha_min",
            str(ALPHA_DM),
            "--alpha_max",
            str(ALPHA_DM),
            "--nAlpha",
            "1",
            "--kfold",
            str(KFOLD),
            "--seed",
            str(SEED),
            "--out_csv",
            str(out_thread),
        ]
        run_cmd(cmd_thread)

        # NO-ENV baseline - canonical prereg
        cmd_none = [
            sys.executable,
            "dm_holdout_cv_thread.py",
            "--points_csv",
            str(points_csv),
            "--model",
            "geo_add_const",
            "--g0",
            "1.2e-10",
            "--env_model",
            "none",
            "--A_min",
            str(A_DM),
            "--A_max",
            str(A_DM),
            "--nA",
            "1",
            "--alpha_min",
            str(ALPHA_DM),
            "--alpha_max",
            str(ALPHA_DM),
            "--nAlpha",
            "1",
            "--kfold",
            str(KFOLD),
            "--seed",
            str(SEED),
            "--out_csv",
            str(out_none),
        ]
        run_cmd(cmd_none)

    summary_thread = check_csv(out_thread)
    summary_none = check_csv(out_none)

    ok = bool(summary_thread["all_delta_chi2_test_positive"] and summary_none["all_delta_chi2_test_positive"])

    print("\n=== DM prereg golden check ===")
    print("THREAD/STIFFGATE:", summary_thread)
    print("NONE baseline   :", summary_none)
    print("PASS rule (all folds delta_chi2_test>0) =>", "PASS" if ok else "FAIL")

    # Also write a small markdown summary artifact
    md = OUT_DIR / "DM_GOLDEN_SUMMARY.md"
    md.write_text(
        "# DM prereg golden summary\n\n"
        f"Repo root: `{REPO_ROOT}`\n\n"
        "PASS rule: all folds satisfy `delta_chi2_test > 0`.\n\n"
        "## THREAD/STIFFGATE\n\n"
        f"- CSV: `{out_thread}`\n"
        f"- min(delta_chi2_test) = {summary_thread['min_delta_chi2_test']:.6g}\n"
        f"- max(delta_chi2_test) = {summary_thread['max_delta_chi2_test']:.6g}\n"
        f"- all folds positive = {summary_thread['all_delta_chi2_test_positive']}\n\n"
        "## NONE baseline\n\n"
        f"- CSV: `{out_none}`\n"
        f"- min(delta_chi2_test) = {summary_none['min_delta_chi2_test']:.6g}\n"
        f"- max(delta_chi2_test) = {summary_none['max_delta_chi2_test']:.6g}\n"
        f"- all folds positive = {summary_none['all_delta_chi2_test_positive']}\n\n"
        f"## Verdict\n\n- {('PASS' if ok else 'FAIL')}\n",
        encoding="utf-8",
    )

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
