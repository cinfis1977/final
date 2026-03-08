from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _make_galaxy_folds(galaxies: list[str], *, kfold: int, seed: int) -> list[list[str]]:
    rng = np.random.default_rng(int(seed))
    gal = np.array(sorted(set([str(g) for g in galaxies])))
    rng.shuffle(gal)
    folds = np.array_split(gal, int(kfold))
    return [list(map(str, f.tolist())) for f in folds]


def test_e2e_dm_c2_holdout_cv_paper_run_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = tmp_path / "out" / "dm_c2_cv_paper"

    env = dict(os.environ)

    cmd = [
        sys.executable,
        str(repo_root / "run_dm_c2_cv_paper_run.py"),
        "--out_dir",
        str(out_dir),
        "--points_csv",
        str(repo_root / "data" / "sparc" / "sparc_points.csv"),
        "--max_galaxies",
        "6",
        "--min_points",
        "8",
        "--kfold",
        "3",
        "--seed",
        "2026",
        "--dt",
        "0.001",
        "--n_steps",
        "180",
        "--order_mode",
        "forward",
        "--A_min",
        "0.0",
        "--A_max",
        "0.2",
        "--nA",
        "11",
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"DM-C2 CV paper run failed (rc={r.returncode})\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    pack = out_dir / "pack_dm_c2_sparc.json"
    out_csv = out_dir / "dm_c2_cv.csv"
    out_json = out_dir / "dm_c2_cv_summary.json"
    report_md = out_dir / "paper_run_report.md"

    for p in (pack, out_csv, out_json, report_md):
        assert p.exists(), f"missing artifact: {p}"

    p_obj = json.loads(pack.read_text(encoding="utf-8"))
    assert p_obj["schema_version"] == "dm_c2_pack_v1"
    galaxies = [str(g.get("name")) for g in p_obj.get("galaxies", [])]
    assert len(galaxies) == 6

    s = json.loads(out_json.read_text(encoding="utf-8"))
    assert s["pack"]["schema_version"] == "dm_c2_pack_v1"
    assert s["framing"]["stability_not_accuracy"] is True

    tel = s["telemetry"]
    assert tel["folds_are_galaxy_holdout"] is True
    assert tel["leakage_guard_disjoint_train_test"] is True
    assert tel["train_only_calibration"] is True
    assert tel["diagonal_sigma_v_used"] is True
    assert tel["poison"]["DM_POISON_PROXY_CALLS"] == "1"

    # Determinism + leakage: fold_details should match recomputed folds.
    kfold = int(s["params"]["kfold"])
    seed = int(s["params"]["seed"])
    folds_expected = _make_galaxy_folds(galaxies, kfold=kfold, seed=seed)

    fold_details = s.get("fold_details")
    assert isinstance(fold_details, list) and len(fold_details) == kfold

    for fd in fold_details:
        test_gals = list(map(str, fd["test_galaxies"]))
        train_gals = list(map(str, fd["train_galaxies"]))
        assert set(test_gals) & set(train_gals) == set()
        assert set(test_gals) | set(train_gals) == set(galaxies)

        fold_idx = int(fd["fold"])
        assert set(test_gals) == set(folds_expected[fold_idx])

    df = pd.read_csv(out_csv)
    for col in [
        "fold",
        "n_train_galaxies",
        "n_test_galaxies",
        "A_best",
        "chi2_train_base",
        "chi2_train_best",
        "delta_chi2_train",
        "chi2_test_base",
        "chi2_test_best",
        "delta_chi2_test",
    ]:
        assert col in df.columns

    numeric_cols = [
        "fold",
        "n_train_galaxies",
        "n_test_galaxies",
        "A_best",
        "chi2_train_base",
        "chi2_train_best",
        "delta_chi2_train",
        "chi2_test_base",
        "chi2_test_best",
        "delta_chi2_test",
    ]
    for c in numeric_cols:
        x = pd.to_numeric(df[c], errors="coerce").astype(float)
        assert x.notna().all()
        assert np.isfinite(x.to_numpy()).all()

    report = report_md.read_text(encoding="utf-8")
    assert "DM_POISON_PROXY_CALLS" in report
    assert "stability_not_accuracy" in report
