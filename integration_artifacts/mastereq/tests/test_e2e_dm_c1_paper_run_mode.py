from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_e2e_dm_c1_paper_run_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = tmp_path / "out" / "dm_c1_paper"

    env = dict(os.environ)

    cmd = [
        sys.executable,
        str(repo_root / "run_dm_c1_paper_run.py"),
        "--out_dir",
        str(out_dir),
        "--seed",
        "2026",
        "--dt",
        "0.2",
        "--n_steps",
        "240",
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"DM-C1 paper run failed (rc={r.returncode})\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    pack = out_dir / "pack_dm_c1_toy.json"
    fwd_csv = out_dir / "dm_c1_pred_forward.csv"
    fwd_json = out_dir / "dm_c1_summary_forward.json"
    rev_csv = out_dir / "dm_c1_pred_reverse.csv"
    rev_json = out_dir / "dm_c1_summary_reverse.json"
    report_md = out_dir / "paper_run_report.md"

    for p in (pack, fwd_csv, fwd_json, rev_csv, rev_json, report_md):
        assert p.exists(), f"missing artifact: {p}"

    s_fwd = json.loads(fwd_json.read_text(encoding="utf-8"))
    s_rev = json.loads(rev_json.read_text(encoding="utf-8"))

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

    # Order sensitivity smoke: forward vs reverse should differ in prediction.
    df_f = pd.read_csv(fwd_csv)
    df_r = pd.read_csv(rev_csv)
    assert len(df_f) == len(df_r)
    diff = (df_f["v_pred"].astype(float) - df_r["v_pred"].astype(float)).abs().max()
    assert float(diff) >= 1e-3

    report = report_md.read_text(encoding="utf-8")
    assert "DM_POISON_PROXY_CALLS" in report
    assert "stability_not_accuracy" in report
