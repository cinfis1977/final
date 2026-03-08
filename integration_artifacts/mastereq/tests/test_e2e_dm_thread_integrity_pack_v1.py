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


def _run_dm_holdout_cv_thread(
    *,
    repo_root: Path,
    tmp_path: Path,
    points_csv: Path,
    env_model: str,
    extra_env: dict[str, str] | None = None,
) -> dict:
    assert points_csv.exists(), f"missing points csv: {points_csv}"

    out_dir = tmp_path / "dm_thread_integrity_pack_v1" / env_model
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / "cv.csv"
    out_json = out_dir / "summary.json"

    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)

    cmd = [
        sys.executable,
        str(repo_root / "dm_holdout_cv_thread.py"),
        "--points_csv",
        str(points_csv),
        "--model",
        "geo_add_const",
        "--g0",
        "1.2e-10",
        "--env_model",
        str(env_model),
        # scan-free: still computes env vectors (thread/global) but keeps prediction stable
        "--A_min",
        "0.0",
        "--A_max",
        "0.0",
        "--nA",
        "1",
        "--alpha_min",
        "0.0",
        "--alpha_max",
        "0.0",
        "--nAlpha",
        "1",
        "--kfold",
        "2",
        "--seed",
        "2026",
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, (
        f"dm_holdout_cv_thread failed (env_model={env_model}) rc={r.returncode}\n"
        f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )

    assert out_csv.exists(), f"missing artifact: {out_csv}"
    assert out_json.exists(), f"missing artifact: {out_json}"

    return json.loads(out_json.read_text(encoding="utf-8"))


def test_e2e_dm_thread_integrity_pack_v1_ablation_and_poison(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]

    # Keep the test fast by running on a small subset of galaxies/points.
    full_points = repo_root / "data" / "sparc" / "sparc_points.csv"
    points_small = tmp_path / "_points_small.csv"
    _write_small_points_csv(src_csv=full_points, dst_csv=points_small, n_galaxies=2, n_points_per_gal=6)

    # THREAD_ONLY: should not touch env_scale even if present.
    s_thread = _run_dm_holdout_cv_thread(
        repo_root=repo_root,
        tmp_path=tmp_path,
        points_csv=points_small,
        env_model="thread",
        extra_env={"DM_POISON_ENV_SCALE_CALLS": "1"},
    )
    tel = s_thread["telemetry"]
    used = tel["env_components_used"]
    assert used["effective_env_model"] == "thread"
    assert used["thread_env"] is True
    assert used["env_scale"] is False
    assert tel["poison"]["DM_POISON_ENV_SCALE_CALLS"] == "1"

    # INTERNAL_ONLY: should not touch thread env code paths.
    s_internal = _run_dm_holdout_cv_thread(
        repo_root=repo_root,
        tmp_path=tmp_path,
        points_csv=points_small,
        env_model="global",
        extra_env={"DM_POISON_THREAD_ENV_CALLS": "1"},
    )
    tel = s_internal["telemetry"]
    used = tel["env_components_used"]
    assert used["effective_env_model"] == "global"
    assert used["thread_env"] is False
    assert used["env_scale"] is True
    assert tel["poison"]["DM_POISON_THREAD_ENV_CALLS"] == "1"

    # FULL: uses both env components.
    s_full = _run_dm_holdout_cv_thread(
        repo_root=repo_root,
        tmp_path=tmp_path,
        points_csv=points_small,
        env_model="global_thread",
        extra_env=None,
    )
    used = s_full["telemetry"]["env_components_used"]
    assert used["effective_env_model"] == "global_thread"
    assert used["thread_env"] is True
    assert used["env_scale"] is True
