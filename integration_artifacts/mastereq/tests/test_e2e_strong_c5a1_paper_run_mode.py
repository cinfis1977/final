from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_e2e_strong_c5a1_paper_run_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]

    out_dir = tmp_path / "out" / "strong_c5a"

    env = dict(os.environ)
    # Keep the evidence mode aligned with C1-C5 discipline.
    env["STRONG_C4_POISON_PDG_CALLS"] = "1"

    cmd = [
        sys.executable,
        str(repo_root / "run_strong_c5a_paper_run.py"),
        "--out_dir",
        str(out_dir),
    ]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"paper run failed (rc={r.returncode})\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    sigma_csv = out_dir / "sigma_tot_pred.csv"
    sigma_json = out_dir / "sigma_tot_summary.json"
    rho_csv = out_dir / "rho_pred.csv"
    rho_json = out_dir / "rho_summary.json"
    report_md = out_dir / "paper_run_report.md"

    for p in (sigma_csv, sigma_json, rho_csv, rho_json, report_md):
        assert p.exists(), f"missing artifact: {p}"

    s_sigma = json.loads(sigma_json.read_text(encoding="utf-8"))
    s_rho = json.loads(rho_json.read_text(encoding="utf-8"))

    # Provenance + anti-fallback locks.
    assert s_sigma["io"]["data_loaded_from_paths"] is True
    assert s_rho["io"]["data_loaded_from_paths"] is True
    assert s_sigma["anti_fallback"]["pdg_call_poison_active"] is True
    assert s_rho["anti_fallback"]["pdg_call_poison_active"] is True

    # Runner identity locks.
    assert s_sigma["amplitude_core_used"] is True
    assert s_rho["amplitude_core_used"] is True
    assert s_sigma["pdg_baseline_used"] is False
    assert s_rho["pdg_baseline_used"] is False

    # Branch coverage: sigma uses cov path, rho uses diag.
    assert s_sigma["chi2"]["telemetry"].get("sigma_tot_mb", {}).get("kind") == "cov"
    assert s_rho["chi2"]["telemetry"].get("rho", {}).get("kind") == "diag"

    # No accuracy claims.
    assert s_sigma["framing"]["stability_not_accuracy"] is True
    assert s_rho["framing"]["stability_not_accuracy"] is True

    # Schema smoke for CSV artifacts.
    df_sig = pd.read_csv(sigma_csv)
    df_rho = pd.read_csv(rho_csv)
    for df in (df_sig, df_rho):
        assert "sqrts_GeV" in df.columns
        assert "sigma_tot_pred_mb" in df.columns
        assert "rho_pred" in df.columns

    report = report_md.read_text(encoding="utf-8")
    assert "IO/closure" in report or "IO" in report
    assert "poison_active" in report
    assert "data_loaded_from_paths" in report
