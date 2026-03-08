from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_e2e_dm_c2_paper_run_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = tmp_path / "out" / "dm_c2_paper"

    env = dict(os.environ)

    cmd = [
        sys.executable,
        str(repo_root / "run_dm_c2_paper_run.py"),
        "--out_dir",
        str(out_dir),
        "--points_csv",
        str(repo_root / "data" / "sparc" / "sparc_points.csv"),
        "--max_galaxies",
        "3",
        "--min_points",
        "8",
        "--seed",
        "2026",
        "--dt",
        "0.001",
        "--n_steps",
        "240",
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"DM-C2 paper run failed (rc={r.returncode})\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    pack = out_dir / "pack_dm_c2_sparc.json"
    fwd_csv = out_dir / "dm_c2_pred_forward.csv"
    fwd_json = out_dir / "dm_c2_summary_forward.json"
    rev_csv = out_dir / "dm_c2_pred_reverse.csv"
    rev_json = out_dir / "dm_c2_summary_reverse.json"
    report_md = out_dir / "paper_run_report.md"

    for p in (pack, fwd_csv, fwd_json, rev_csv, rev_json, report_md):
        assert p.exists(), f"missing artifact: {p}"

    p_obj = json.loads(pack.read_text(encoding="utf-8"))
    assert p_obj["schema_version"] == "dm_c2_pack_v1"
    assert "source" in p_obj and "units" in p_obj["source"]
    assert p_obj["source"]["units"]["r"] == "kpc"

    s_fwd = json.loads(fwd_json.read_text(encoding="utf-8"))
    s_rev = json.loads(rev_json.read_text(encoding="utf-8"))

    # Schema lock
    assert s_fwd["pack"]["schema_version"] == "dm_c2_pack_v1"
    assert s_rev["pack"]["schema_version"] == "dm_c2_pack_v1"

    # Framing lock
    assert s_fwd["framing"]["stability_not_accuracy"] is True
    assert s_rev["framing"]["stability_not_accuracy"] is True

    # Anti-fallback / telemetry locks
    for s in (s_fwd, s_rev):
        assert s["telemetry"]["dm_dynamics_core_used"] is True
        assert s["telemetry"]["proxy_overlay_used"] is False
        assert s["telemetry"]["stiffgate_in_evolution"] is True
        b = s["telemetry"]["boundedness"]
        assert b["finite_all"] is True
        assert b["g_in_0_1"] is True
        assert b["epsilon_nonneg"] is True
        assert s["telemetry"]["poison"]["DM_POISON_PROXY_CALLS"] == "1"

    # Order sensitivity smoke: forward vs reverse should not be numerically identical.
    chi2_f = float(s_fwd["chi2"]["total"])
    chi2_r = float(s_rev["chi2"]["total"])
    assert abs(chi2_f - chi2_r) > 1e-9

    # Basic CSV sanity
    df = pd.read_csv(fwd_csv)
    for col in ["galaxy", "r", "v_obs", "sigma_v", "a_bary", "a_dm", "v_pred", "pull", "g", "epsilon"]:
        assert col in df.columns
    assert df[["r", "v_obs", "sigma_v", "a_bary", "v_pred", "g", "epsilon"]].apply(pd.to_numeric, errors="coerce").notna().all().all()

    report = report_md.read_text(encoding="utf-8")
    assert "DM_POISON_PROXY_CALLS" in report
    assert "stability_not_accuracy" in report
