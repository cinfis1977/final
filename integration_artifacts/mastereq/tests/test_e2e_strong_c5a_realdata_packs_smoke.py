from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _run_pack(tmp_path: Path, *, pack: Path, stem: str) -> dict:
    out_csv = tmp_path / f"{stem}.csv"
    out_json = tmp_path / f"{stem}.json"

    env = dict(os.environ)
    env["STRONG_C4_POISON_PDG_CALLS"] = "1"

    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[3] / "strong_amplitude_pack_hepdata_c4.py"),
        "--pack",
        str(pack),
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"runner failed (rc={r.returncode})\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    summary = json.loads(out_json.read_text(encoding="utf-8"))

    assert summary["io"]["data_loaded_from_paths"] is True
    assert summary["anti_fallback"]["pdg_call_poison_active"] is True
    assert summary["amplitude_core_used"] is True
    assert summary["pdg_baseline_used"] is False
    assert summary["framing"]["stability_not_accuracy"] is True

    chi2 = summary["chi2"]
    assert chi2["total"] is None or float(chi2["total"]) == float(chi2["total"])

    df = pd.read_csv(out_csv)
    assert "sqrts_GeV" in df.columns
    assert "sigma_tot_pred_mb" in df.columns
    assert "rho_pred" in df.columns

    return summary


def test_e2e_strong_c5a_realdata_packs_smoke(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    pack_dir = repo_root / "integration_artifacts" / "mastereq" / "packs" / "strong_c5a"

    s1 = _run_pack(tmp_path, pack=pack_dir / "pdg_sigma_tot_pack.json", stem="pdg_sigma")
    assert s1["chi2"]["telemetry"].get("sigma_tot_mb", {}).get("kind") == "cov"

    s2 = _run_pack(tmp_path, pack=pack_dir / "pdg_rho_pack.json", stem="pdg_rho")
    assert s2["chi2"]["telemetry"].get("rho", {}).get("kind") == "diag"
