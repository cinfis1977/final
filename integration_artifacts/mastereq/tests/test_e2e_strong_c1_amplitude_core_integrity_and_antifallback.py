import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def test_strong_c1_amplitude_runner_integrity_and_antifallback(tmp_path: Path):
    """E2E: amplitude-level core runs, satisfies integrity, and locks anti-fallback.

    This is the STRONG analogue of WEAK's anti-fallback closure tests:
      - internal state evolves (chi(b,t))
      - observables computed from forward amplitude proxy
      - integrity checks are enforced
            - PDG/COMPETE baseline *eval calls* are poisoned and must not be called
    """

    runner = ROOT / "strong_amplitude_eikonal_energy_scan_c1.py"
    assert runner.exists(), f"Missing runner: {runner}"

    # Small scan: a few energies spanning low->high.
    df_in = pd.DataFrame(
        {
            "sqrts_GeV": [7.0, 20.0, 200.0, 13000.0],
            "channel": ["pp", "pp", "pp", "pp"],
        }
    )
    data = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    summ = tmp_path / "summary.json"
    df_in.to_csv(data, index=False)

    env = dict(os.environ)
    env["STRONG_C1_POISON_PDG_CALLS"] = "1"

    cmd = [
        sys.executable,
        str(runner),
        "--data",
        str(data),
        "--out",
        str(out),
        "--summary_out",
        str(summ),
        "--A",
        "0.0",
    ]

    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert proc.returncode == 0, f"Runner failed. stdout=\n{proc.stdout}\n\nstderr=\n{proc.stderr}\n"

    assert out.exists(), "Runner did not write CSV"
    assert summ.exists(), "Runner did not write summary JSON"

    df = pd.read_csv(out)
    assert len(df) == 4

    # Integrity expectations (loose but meaningful)
    assert np.min(df["sigma_tot_sm_mb"].to_numpy(float)) >= -1e-10
    assert np.min(df["chiI_min"].to_numpy(float)) >= -1e-10
    assert np.all(np.isfinite(df["rho_sm"].to_numpy(float)))
    assert np.max(np.abs(df["rho_sm"].to_numpy(float))) <= 10.0
    assert np.max(df["S_abs_max"].to_numpy(float)) <= 1.0 + 1e-8

    summary = json.loads(summ.read_text(encoding="utf-8"))
    # Observable-from-state telemetry: sigma_tot = sigma_norm*ImF and rho = ReF/ImF
    assert summary["amplitude_core_used"] is True
    assert summary["pdg_baseline_used"] is False

    anti = summary["anti_fallback"]
    assert anti["pdg_call_poison_active"] is True
    assert len(anti.get("poisoned_targets", [])) >= 3

    sigma_norm = float(summary["pars"]["sigma_norm_mb"])
    F_im = df["F_im"].to_numpy(float)
    F_re = df["F_re"].to_numpy(float)
    assert np.min(F_im) > 0.0
    assert np.allclose(df["sigma_tot_sm_mb"].to_numpy(float), sigma_norm * F_im, rtol=0, atol=1e-10)
    assert np.allclose(df["rho_sm"].to_numpy(float), F_re / F_im, rtol=0, atol=1e-10)

    # Ensure runner asserts its own integrity too.
    assert all(summary["integrity"].values())

    # Step-refinement sanity: halving dt_max should not wildly change sigma.
    out2 = tmp_path / "out_refined.csv"
    summ2 = tmp_path / "summary_refined.json"
    cmd2 = [
        sys.executable,
        str(runner),
        "--data",
        str(data),
        "--out",
        str(out2),
        "--summary_out",
        str(summ2),
        "--A",
        "0.0",
        "--dt_max",
        "0.025",
    ]

    proc2 = subprocess.run(cmd2, cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert proc2.returncode == 0, f"Refined runner failed. stdout=\n{proc2.stdout}\n\nstderr=\n{proc2.stderr}\n"
    df2 = pd.read_csv(out2)

    sig1 = df["sigma_tot_sm_mb"].to_numpy(float)
    sig2 = df2["sigma_tot_sm_mb"].to_numpy(float)
    denom = max(float(np.max(np.abs(sig2))), 1e-12)
    rel = float(np.max(np.abs(sig1 - sig2)) / denom)
    assert rel <= 0.05

    rho1 = df["rho_sm"].to_numpy(float)
    rho2 = df2["rho_sm"].to_numpy(float)
    # rho can be more sensitive than sigma; use a loose absolute tolerance.
    assert float(np.max(np.abs(rho1 - rho2))) <= 0.10

    # b-grid refinement sanity: doubling nb should not wildly change sigma/rho.
    out3 = tmp_path / "out_nb_refined.csv"
    summ3 = tmp_path / "summary_nb_refined.json"
    cmd3 = [
        sys.executable,
        str(runner),
        "--data",
        str(data),
        "--out",
        str(out3),
        "--summary_out",
        str(summ3),
        "--A",
        "0.0",
        "--nb",
        "1200",
    ]
    proc3 = subprocess.run(cmd3, cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert proc3.returncode == 0, f"nb-refined runner failed. stdout=\n{proc3.stdout}\n\nstderr=\n{proc3.stderr}\n"
    df3 = pd.read_csv(out3)

    sig3 = df3["sigma_tot_sm_mb"].to_numpy(float)
    denom3 = max(float(np.max(np.abs(sig3))), 1e-12)
    rel3 = float(np.max(np.abs(sig1 - sig3)) / denom3)
    assert rel3 <= 0.05

    rho3 = df3["rho_sm"].to_numpy(float)
    assert float(np.max(np.abs(rho1 - rho3))) <= 0.10
