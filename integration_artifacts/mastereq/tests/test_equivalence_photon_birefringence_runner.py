from __future__ import annotations

import csv
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

_INTEGRATION_ROOT = Path(__file__).resolve().parents[2]
if str(_INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_ROOT))

from mastereq.unified_gksl import UnifiedGKSL
from mastereq.photon_sector import (
    cmb_prereg_locked_check,
    accumulation_prereg_locked_check,
    make_photon_birefringence_damping_fn,
)
from mastereq.microphysics import (
    gamma_km_inv_from_n_sigma_v,
    sigma_photon_birefringence_reference_cm2,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _bridge_dir() -> Path:
    return _repo_root() / "integration_artifacts" / "entanglement_photon_bridge"


def _read_single_csv_row(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _run_ps1(script: Path, args: list[str]) -> None:
    if not sys.platform.startswith("win"):
        return
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        *args,
    ]
    proc = subprocess.run(cmd, cwd=str(script.parent), capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"Runner failed: {script}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")


def test_cmb_runner_matches_independent_locked_math(tmp_path: Path):
    if not sys.platform.startswith("win"):
        return

    out_csv = tmp_path / "cmb_birefringence_prereg_v1.csv"
    script = _bridge_dir() / "run_prereg_cmb_birefringence_v1_DROPIN_SELFCONTAINED.ps1"

    args = [
        "-BetaCalDeg", "0.34",
        "-SigmaCalDeg", "0.09",
        "-BetaHoldDeg", "0.215",
        "-SigmaHoldDeg", "0.074",
        "-KSigma", "2.0",
        "-OutCsv", str(out_csv),
    ]
    _run_ps1(script, args)
    got = _read_single_csv_row(out_csv)

    ref = cmb_prereg_locked_check(
        beta_cal_deg=0.34,
        sigma_cal_deg=0.09,
        beta_hold_deg=0.215,
        sigma_hold_deg=0.074,
        k_sigma=2.0,
    )

    assert math.isclose(float(got["C_beta_locked_deg"]), float(ref["C_beta_locked_deg"]), rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(float(got["diff_deg"]), float(ref["diff_deg"]), rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(float(got["sigma_comb_deg"]), float(ref["sigma_comb_deg"]), rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(float(got["z_score"]), float(ref["z_score"]), rel_tol=0.0, abs_tol=1e-12)
    assert got["verdict"] == ref["verdict"]
    assert got["sign_verdict"] == ref["sign_verdict"]


def test_accumulation_runner_matches_independent_locked_math(tmp_path: Path):
    if not sys.platform.startswith("win"):
        return

    out_csv = tmp_path / "birefringence_accumulation_prereg_v1.csv"
    script = _bridge_dir() / "run_prereg_birefringence_accumulation_v1_DROPIN_SELFCONTAINED_FIX.ps1"

    args = [
        "-ZCal", "1100.0",
        "-BetaCalDeg", "0.342",
        "-SigmaCalDeg", "0.094",
        "-ZHold", "2.5",
        "-BetaHoldDeg", "-0.8",
        "-SigmaHoldDeg", "2.2",
        "-Om", "0.315",
        "-Ol", "0.685",
        "-Or", "0.0",
        "-KSigma", "2.0",
        "-OutCsv", str(out_csv),
    ]
    _run_ps1(script, args)
    got = _read_single_csv_row(out_csv)

    ref = accumulation_prereg_locked_check(
        z_cal=1100.0,
        beta_cal_deg=0.342,
        sigma_cal_deg=0.094,
        z_hold=2.5,
        beta_hold_deg=-0.8,
        sigma_hold_deg=2.2,
        Om=0.315,
        Ol=0.685,
        Or=0.0,
        k_sigma=2.0,
        abs_test=False,
    )

    assert math.isclose(float(got["I_cal"]), float(ref["I_cal"]), rel_tol=0.0, abs_tol=5e-9)
    assert math.isclose(float(got["I_hold"]), float(ref["I_hold"]), rel_tol=0.0, abs_tol=5e-9)
    assert math.isclose(float(got["C_beta_locked_per_I"]), float(ref["C_beta_locked_per_I"]), rel_tol=0.0, abs_tol=5e-12)
    assert math.isclose(float(got["beta_pred_hold_deg"]), float(ref["beta_pred_hold_deg"]), rel_tol=0.0, abs_tol=5e-12)
    assert math.isclose(float(got["z_score"]), float(ref["z_score"]), rel_tol=0.0, abs_tol=5e-12)
    assert got["verdict"] == ref["verdict"]


def test_photon_microphysics_wiring_matches_explicit_gamma():
    dm2 = 2.5e-3
    theta = math.radians(33.0)
    L_km = 810.0
    E_GeV = 2.0

    n_cm3 = 1.0e16
    coupling_x = 1.7
    sigma = sigma_photon_birefringence_reference_cm2(E_GeV, coupling_x)
    gamma = gamma_km_inv_from_n_sigma_v(n_cm3, sigma, 3.0e10)

    ug_micro = UnifiedGKSL(dm2, theta)
    ug_micro.add_damping(
        make_photon_birefringence_damping_fn(
            use_microphysics=True,
            n_cm3=n_cm3,
            E_GeV_ref=E_GeV,
            coupling_x=coupling_x,
            v_cm_s=3.0e10,
        )
    )

    ug_explicit = UnifiedGKSL(dm2, theta)
    ug_explicit.add_damping(make_photon_birefringence_damping_fn(gamma=gamma, use_microphysics=False))

    rho_micro = ug_micro.integrate(L_km, E_GeV, steps=340)
    rho_explicit = ug_explicit.integrate(L_km, E_GeV, steps=340)
    assert np.allclose(rho_micro, rho_explicit, atol=5e-13, rtol=0.0)
