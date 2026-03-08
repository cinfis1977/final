import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from integration_artifacts.mastereq.strong_c1_eikonal_amplitude import (
    EikonalC1Params,
    EikonalC1State,
    forward_amplitude_from_state,
    t_from_sqrts,
)


ROOT = Path(__file__).resolve().parents[3]


def _predict_sigma_rho(sqrts: np.ndarray, pars: EikonalC1Params) -> tuple[np.ndarray, np.ndarray]:
    t_arr = t_from_sqrts(sqrts, s0_GeV2=pars.s0_GeV2)
    order = np.argsort(t_arr)
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))

    t_sorted = t_arr[order]
    state = EikonalC1State.initialize(pars)

    sigma = np.empty_like(t_sorted, dtype=float)
    rho = np.empty_like(t_sorted, dtype=float)

    for i, t in enumerate(t_sorted):
        state.advance_to(float(t), pars)
        F = forward_amplitude_from_state(state)
        im = float(np.imag(F))
        re = float(np.real(F))
        sigma[i] = float(pars.sigma_norm_mb) * im
        im_safe = im if abs(im) > 1e-30 else (1e-30 if im >= 0 else -1e-30)
        rho[i] = re / im_safe

    return sigma[inv], rho[inv]


def test_strong_c4_hepdata_like_pack_ingestion(tmp_path: Path):
    """E2E: HEPData-like IO closure (CSV + cov paths) under call-poison.

    Minimum C4 claims:
      - Pack points come from a CSV file (paths.data_csv)
      - Optional covariance comes from CSV paths (paths.cov_*)
      - Chi2 path is exercised for both sigma_tot and rho
      - Anti-fallback call-poison active; runner still succeeds
      - Schema + IO provenance telemetry locked
    """

    runner = ROOT / "strong_amplitude_pack_hepdata_c4.py"
    assert runner.exists(), f"Missing runner: {runner}"

    sqrts = np.asarray([7.0, 20.0, 200.0, 13000.0], dtype=float)
    pars = EikonalC1Params()
    sig, rho = _predict_sigma_rho(sqrts, pars)

    # Build data CSV (data=pred so chi2 -> 0).
    sig_unc = np.full_like(sig, 1.0)
    rho_unc = np.full_like(rho, 0.05)

    df = pd.DataFrame(
        {
            "sqrts_GeV": sqrts,
            "sigma_tot_mb": sig,
            "sigma_tot_unc_mb": sig_unc,
            "rho": rho,
            "rho_unc": rho_unc,
        }
    )

    data_csv = tmp_path / "scan.csv"
    df.to_csv(data_csv, index=False)

    # Full covariance for sigma_tot (exercise cov branch); rho uses diag unc.
    Csig = np.array(
        [
            [1.0, 0.2, 0.0, 0.0],
            [0.2, 1.5, 0.1, 0.0],
            [0.0, 0.1, 2.0, 0.3],
            [0.0, 0.0, 0.3, 2.5],
        ],
        dtype=float,
    )
    cov_sigma = tmp_path / "cov_sigma.csv"
    pd.DataFrame(Csig).to_csv(cov_sigma, index=False)

    pack = {
        "meta": {"name": "synthetic_c4_pack", "note": "hepdata-like paths"},
        "model": {"s0_GeV2": pars.s0_GeV2, "dt_max": pars.dt_max, "nb": pars.nb, "b_max": pars.b_max, "sigma_norm_mb": pars.sigma_norm_mb},
        "geo": {"A": 0.0, "template": "cos", "phi0": 0.0, "omega": 1.0},
        "paths": {"data_csv": data_csv.name, "cov_sigma_tot_csv": cov_sigma.name},
        "columns": {
            "sqrts_GeV": "sqrts_GeV",
            "sigma_tot_mb": "sigma_tot_mb",
            "sigma_tot_unc_mb": "sigma_tot_unc_mb",
            "rho": "rho",
            "rho_unc": "rho_unc",
        },
    }

    pack_path = tmp_path / "pack.json"
    pack_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")

    out_csv = tmp_path / "out.csv"
    out_json = tmp_path / "out.json"

    env = dict(os.environ)
    env["STRONG_C1_POISON_PDG_CALLS"] = "1"

    proc = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--pack",
            str(pack_path),
            "--out_csv",
            str(out_csv),
            "--out_json",
            str(out_json),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, f"Runner failed. stdout=\n{proc.stdout}\n\nstderr=\n{proc.stderr}\n"

    summ = json.loads(out_json.read_text(encoding="utf-8"))
    assert summ["amplitude_core_used"] is True
    assert summ["pdg_baseline_used"] is False
    assert summ["anti_fallback"]["pdg_call_poison_active"] is True

    assert summ["io"]["data_loaded_from_paths"] is True
    assert Path(summ["io"]["data_csv"]).name == data_csv.name
    assert Path(summ["io"]["cov_sigma_tot_csv"]).name == cov_sigma.name

    chi2 = summ["chi2"]
    assert chi2["telemetry"]["sigma_tot_mb"]["kind"] == "cov"
    assert chi2["telemetry"]["rho"]["kind"] == "diag"
    assert float(chi2["total"]) <= 1e-10

    # Schema smoke
    out = pd.read_csv(out_csv)
    for col in ["sqrts_GeV", "sigma_tot_pred_mb", "rho_pred", "F_re", "F_im", "S_abs_max"]:
        assert col in out.columns

    assert summ["framing"]["stability_not_accuracy"] is True
    assert all(summ["integrity"].values())
