from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_e2e_em_paper_run_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = tmp_path / "out" / "em_paper"

    env = dict(os.environ)

    cmd = [
        sys.executable,
        str(repo_root / "run_em_paper_run.py"),
        "--out_dir",
        str(out_dir),
        "--cov",
        "total",
        "--A",
        "0.0",
        "--shape_only",
        "--freeze_betas",
        "--beta_nonneg",
        "--require_positive",
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"EM paper run failed (rc={r.returncode})\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    bhabha_csv = out_dir / "bhabha_pred.csv"
    bhabha_json = out_dir / "bhabha_summary.json"
    bhabha_imp_csv = out_dir / "bhabha_import_pred.csv"
    bhabha_imp_json = out_dir / "bhabha_import_summary.json"
    mumu_csv = out_dir / "mumu_pred.csv"
    mumu_json = out_dir / "mumu_summary.json"
    report_md = out_dir / "paper_run_report.md"

    for p in (bhabha_csv, bhabha_json, bhabha_imp_csv, bhabha_imp_json, mumu_csv, mumu_json, report_md):
        assert p.exists(), f"missing artifact: {p}"

    s_b = json.loads(bhabha_json.read_text(encoding="utf-8"))
    s_bi = json.loads(bhabha_imp_json.read_text(encoding="utf-8"))
    s_m = json.loads(mumu_json.read_text(encoding="utf-8"))

    # IO/provenance
    assert s_b["io"]["data_loaded_from_paths"] is True
    assert s_m["io"]["data_loaded_from_paths"] is True
    assert s_b["io"]["cov_choice"] == "total"
    assert s_m["io"]["cov_choice"] == "total"
    assert s_b["io"]["data_csv"]
    assert s_m["io"]["data_csv"]
    assert s_b["io"]["cov_csv"]
    assert s_m["io"]["cov_csv"]

    # No hidden baseline import for the paper run.
    assert s_b["telemetry"]["baseline_import_used"] is False

    # Explicit baseline import branch is exercised and recorded.
    assert s_bi["telemetry"]["baseline_import_used"] is True
    assert s_bi["io"].get("baseline_csv")

    # Framing lock
    assert s_b["framing"]["stability_not_accuracy"] is True
    assert s_m["framing"]["stability_not_accuracy"] is True

    # CSV schema smoke
    df_b = pd.read_csv(bhabha_csv)
    for col in ["obs_pb", "pred_sm", "pred_geo", "delta", "ratio_geo_sm"]:
        assert col in df_b.columns

    df_bi = pd.read_csv(bhabha_imp_csv)
    for col in ["obs_pb", "pred_sm", "pred_geo", "delta", "ratio_geo_sm"]:
        assert col in df_bi.columns

    df_m = pd.read_csv(mumu_csv)
    for col in ["obs_pb", "pred0_pb", "pred_sm", "pred_geo", "delta"]:
        assert col in df_m.columns

    report = report_md.read_text(encoding="utf-8")
    assert "data_loaded_from_paths" in report
    assert "stability_not_accuracy" in report
