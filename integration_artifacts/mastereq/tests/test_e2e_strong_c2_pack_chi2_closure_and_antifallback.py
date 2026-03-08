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


def test_strong_c2_pack_chi2_closure_and_antifallback(tmp_path: Path):
    """E2E: pack→pred→residual→χ² closure, with anti-fallback call-poison.

    Minimum C2 claims:
      - Pack interface for an energy scan
      - Predicted σ_tot and ρ from amplitude-derived state
      - χ² computation (diag uncertainties)
      - Anti-fallback: PDG baseline eval-calls poisoned; runner still succeeds
      - Stable CSV/JSON schema smoke
    """

    runner = ROOT / "strong_amplitude_pack_chi2_c2.py"
    assert runner.exists(), f"Missing runner: {runner}"

    sqrts = np.asarray([7.0, 20.0, 200.0, 13000.0], dtype=float)
    pars = EikonalC1Params()

    sig, rho = _predict_sigma_rho(sqrts, pars)

    # Synthetic data = prediction => chi2 ~ 0.
    sig_unc = np.full_like(sig, 1.0, dtype=float)  # mb
    rho_unc = np.full_like(rho, 0.05, dtype=float)

    pack = {
        "meta": {"name": "synthetic_strong_c2_pack", "note": "data=pred synthetic closure test"},
        "scan": {"sqrts_GeV": sqrts.tolist(), "channel": "pp"},
        "model": {"s0_GeV2": pars.s0_GeV2, "dt_max": pars.dt_max, "nb": pars.nb, "b_max": pars.b_max, "sigma_norm_mb": pars.sigma_norm_mb},
        "data": {
            "sigma_tot_mb": {"y": sig.tolist(), "unc": sig_unc.tolist()},
            "rho": {"y": rho.tolist(), "unc": rho_unc.tolist()},
        },
    }

    pack_path = tmp_path / "pack.json"
    pack_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")

    out_csv = tmp_path / "out.csv"
    out_json = tmp_path / "out.json"

    env = dict(os.environ)
    env["STRONG_C1_POISON_PDG_CALLS"] = "1"

    cmd = [
        sys.executable,
        str(runner),
        "--pack",
        str(pack_path),
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]

    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert proc.returncode == 0, f"Runner failed. stdout=\n{proc.stdout}\n\nstderr=\n{proc.stderr}\n"

    assert out_csv.exists()
    assert out_json.exists()

    df = pd.read_csv(out_csv)
    assert len(df) == len(sqrts)

    # Schema smoke
    for col in ["sqrts_GeV", "sigma_tot_pred_mb", "rho_pred", "F_re", "F_im", "S_abs_max"]:
        assert col in df.columns

    summ = json.loads(out_json.read_text(encoding="utf-8"))
    assert summ["amplitude_core_used"] is True
    assert summ["pdg_baseline_used"] is False

    anti = summ["anti_fallback"]
    assert anti["pdg_call_poison_active"] is True
    assert len(anti.get("poisoned_targets", [])) >= 3

    chi2 = summ["chi2"]
    assert chi2["total"] is not None
    assert float(chi2["total"]) <= 1e-10

    # Framing lock
    assert summ["framing"]["stability_not_accuracy"] is True

    # Ensure runner asserts integrity too.
    assert all(summ["integrity"].values())

    # -------------------------
    # C2.1 negative control: perturb data => chi2 should grow
    # -------------------------
    pack_shift = dict(pack)
    pack_shift["meta"] = {**pack_shift.get("meta", {}), "note": "negative control: data shifted to force chi2>0"}
    pack_shift["data"] = {
        "sigma_tot_mb": {"y": (sig * 1.01).tolist(), "unc": sig_unc.tolist()},
        "rho": {"y": (rho + 0.01).tolist(), "unc": rho_unc.tolist()},
    }
    pack_shift_path = tmp_path / "pack_shift.json"
    pack_shift_path.write_text(json.dumps(pack_shift, indent=2), encoding="utf-8")

    out_json_shift = tmp_path / "out_shift.json"
    out_csv_shift = tmp_path / "out_shift.csv"
    cmd_shift = [
        sys.executable,
        str(runner),
        "--pack",
        str(pack_shift_path),
        "--out_csv",
        str(out_csv_shift),
        "--out_json",
        str(out_json_shift),
    ]
    proc_shift = subprocess.run(cmd_shift, cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert proc_shift.returncode == 0, f"Shifted-data run failed. stdout=\n{proc_shift.stdout}\n\nstderr=\n{proc_shift.stderr}\n"
    summ_shift = json.loads(out_json_shift.read_text(encoding="utf-8"))
    assert float(summ_shift["chi2"]["total"]) > 0.5

    # -------------------------
    # C2.1 full-covariance path: 2x2 cov loaded from CSV (cov.path)
    # -------------------------
    sq2 = np.asarray([7.0, 13000.0], dtype=float)
    sig2, _rho2 = _predict_sigma_rho(sq2, pars)

    # Build a small correlated covariance in mb^2.
    C = np.array([[1.0, 0.2], [0.2, 1.5]], dtype=float)
    cov_csv = tmp_path / "cov2.csv"
    pd.DataFrame(C).to_csv(cov_csv, index=False)

    # Add a known offset so chi2 is nonzero and check numeric agreement.
    delta = np.array([0.3, -0.1], dtype=float)
    pack_cov = {
        "meta": {"name": "synthetic_strong_c2_pack_cov", "note": "full-cov chi2 path via cov.path"},
        "scan": {"sqrts_GeV": sq2.tolist(), "channel": "pp"},
        "model": {
            "s0_GeV2": pars.s0_GeV2,
            "dt_max": pars.dt_max,
            "nb": pars.nb,
            "b_max": pars.b_max,
            "sigma_norm_mb": pars.sigma_norm_mb,
        },
        "data": {
            "sigma_tot_mb": {"y": (sig2 + delta).tolist(), "cov": {"path": cov_csv.name}}
        },
    }
    pack_cov_path = tmp_path / "pack_cov.json"
    pack_cov_path.write_text(json.dumps(pack_cov, indent=2), encoding="utf-8")

    out_json_cov = tmp_path / "out_cov.json"
    out_csv_cov = tmp_path / "out_cov.csv"
    cmd_cov = [
        sys.executable,
        str(runner),
        "--pack",
        str(pack_cov_path),
        "--out_csv",
        str(out_csv_cov),
        "--out_json",
        str(out_json_cov),
    ]
    proc_cov = subprocess.run(cmd_cov, cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert proc_cov.returncode == 0, f"Full-cov run failed. stdout=\n{proc_cov.stdout}\n\nstderr=\n{proc_cov.stderr}\n"
    summ_cov = json.loads(out_json_cov.read_text(encoding="utf-8"))
    assert summ_cov["chi2"]["telemetry"]["sigma_tot_mb"]["kind"] == "cov"

    expected = float(delta.T @ np.linalg.pinv(C, rcond=1e-12) @ delta)
    got = float(summ_cov["chi2"]["sigma_tot_mb"])
    assert np.isfinite(got)
    assert abs(got - expected) <= 1e-9
