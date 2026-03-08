from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _pick_galaxy_col(df: pd.DataFrame) -> str:
    for c in ["galaxy", "galaxy_id", "gal", "name", "gal_name", "SPARC_galaxy"]:
        if c in df.columns:
            return c
    for c in df.columns:
        if "gal" in c.lower():
            return c
    raise RuntimeError(f"Could not find a galaxy identifier column. Columns={list(df.columns)}")


def _write_small_points_csv(*, src_csv: Path, dst_csv: Path, n_galaxies: int = 2, n_points_per_gal: int = 6) -> None:
    df = pd.read_csv(src_csv)
    gal_col = _pick_galaxy_col(df)
    df[gal_col] = df[gal_col].astype(str)

    gals = df[gal_col].dropna().astype(str).unique().tolist()
    if not gals:
        raise RuntimeError("No galaxies found in points CSV")

    keep = set(gals[: int(n_galaxies)])
    sub = df[df[gal_col].isin(keep)].copy()
    sub = sub.groupby(gal_col, sort=True, group_keys=False).head(int(n_points_per_gal)).reset_index(drop=True)

    dst_csv.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(dst_csv, index=False)


def test_e2e_dm_thread_integrity_pack_v1_driver_creates_scorecard_and_runs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = tmp_path / "out" / "dm_thread_integrity_v1"

    # Keep the test fast by running on a small subset.
    full_points = repo_root / "data" / "sparc" / "sparc_points.csv"
    points_small = tmp_path / "_points_small.csv"
    _write_small_points_csv(src_csv=full_points, dst_csv=points_small, n_galaxies=2, n_points_per_gal=6)

    env = dict(os.environ)

    cmd = [
        sys.executable,
        str(repo_root / "run_dm_thread_integrity_pack_v1.py"),
        "--out",
        str(out_dir),
        "--points_csv",
        str(points_small),
        "--kfold",
        "2",
        "--seed",
        "2026",
        "--A",
        "0.0",
        "--alpha",
        "0.0",
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"driver failed (rc={r.returncode})\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    scorecard = out_dir / "DM_THREAD_INTEGRITY_SCORECARD.md"
    assert scorecard.exists(), f"missing artifact: {scorecard}"
    md = scorecard.read_text(encoding="utf-8")
    assert "DM thread integrity scorecard" in md
    assert "THREAD_ONLY" in md
    assert "INTERNAL_ONLY" in md
    assert "FULL" in md

    for mode in ["thread_only", "internal_only", "full"]:
        run_dir = out_dir / mode
        assert run_dir.exists(), f"missing run dir: {run_dir}"
        assert (run_dir / "command.txt").exists()
        assert (run_dir / "terminal_output_and_exit_code.txt").exists()
        assert (run_dir / "dm_cv.csv").exists()
        assert (run_dir / "dm_cv_summary.json").exists()

    s_thread = json.loads((out_dir / "thread_only" / "dm_cv_summary.json").read_text(encoding="utf-8"))
    s_internal = json.loads((out_dir / "internal_only" / "dm_cv_summary.json").read_text(encoding="utf-8"))
    s_full = json.loads((out_dir / "full" / "dm_cv_summary.json").read_text(encoding="utf-8"))

    u = s_thread["telemetry"]["env_components_used"]
    assert u["effective_env_model"] == "thread"
    assert u["thread_env"] is True
    assert u["env_scale"] is False
    assert s_thread["telemetry"]["poison"]["DM_POISON_ENV_SCALE_CALLS"] == "1"

    u = s_internal["telemetry"]["env_components_used"]
    assert u["effective_env_model"] == "global"
    assert u["thread_env"] is False
    assert u["env_scale"] is True
    assert s_internal["telemetry"]["poison"]["DM_POISON_THREAD_ENV_CALLS"] == "1"

    u = s_full["telemetry"]["env_components_used"]
    assert u["effective_env_model"] == "global_thread"
    assert u["thread_env"] is True
    assert u["env_scale"] is True
