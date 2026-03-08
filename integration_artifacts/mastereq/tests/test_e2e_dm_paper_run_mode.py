from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_e2e_dm_paper_run_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = tmp_path / "out" / "dm_paper"

    env = dict(os.environ)

    cmd = [
        sys.executable,
        str(repo_root / "run_dm_paper_run.py"),
        "--out_dir",
        str(out_dir),
        "--kfold",
        "2",
        "--seed",
        "2026",
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"DM paper run failed (rc={r.returncode})\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    stiff_csv = out_dir / "dm_cv_thread_STIFFGATE_fixed.csv"
    stiff_json = out_dir / "dm_cv_thread_STIFFGATE_summary.json"
    none_csv = out_dir / "dm_cv_none_fixed.csv"
    none_json = out_dir / "dm_cv_none_summary.json"
    report_md = out_dir / "paper_run_report.md"

    for p in (stiff_csv, stiff_json, none_csv, none_json, report_md):
        assert p.exists(), f"missing artifact: {p}"

    s_stiff = json.loads(stiff_json.read_text(encoding="utf-8"))
    s_none = json.loads(none_json.read_text(encoding="utf-8"))

    # IO/provenance
    assert s_stiff["io"]["data_loaded_from_paths"] is True
    assert s_none["io"]["data_loaded_from_paths"] is True
    assert s_stiff["io"].get("points_csv")
    assert s_none["io"].get("points_csv")

    # Branch coverage locks
    assert s_stiff["params"]["env_model"] == "thread"
    assert s_stiff["telemetry"]["thread_calibration_used"] is True
    assert s_none["params"]["env_model"] == "none"

    # Framing lock
    assert s_stiff["framing"]["stability_not_accuracy"] is True
    assert s_none["framing"]["stability_not_accuracy"] is True

    # CSV schema smoke
    df_stiff = pd.read_csv(stiff_csv)
    df_none = pd.read_csv(none_csv)
    for df in (df_stiff, df_none):
        for col in [
            "fold",
            "A_best",
            "alpha_best",
            "chi2_train_base",
            "chi2_train_best",
            "delta_chi2_train",
            "chi2_test_base",
            "chi2_test_best",
            "delta_chi2_test",
        ]:
            assert col in df.columns

    report = report_md.read_text(encoding="utf-8")
    assert "data_loaded_from_paths" in report
    assert "stability_not_accuracy" in report
