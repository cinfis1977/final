import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def _run_runner(tmp_path: Path, pack: Path, extra_args: list[str]) -> pd.DataFrame:
    out = tmp_path / "out.csv"
    cmd = [
        sys.executable,
        str(ROOT / "nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py"),
        "--pack",
        str(pack),
        "--use_rate_kernel",
        "--kernel",
        "none",
        "--A",
        "0.0",
        "--omega",
        "0.0",
        "--omega0_geom",
        "free",
        "--steps",
        "60",
        "--out",
        str(out),
    ]
    cmd.extend(extra_args)
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    return pd.read_csv(out).sort_values(["channel", "i"]).reset_index(drop=True)


def test_dynamics_to_rate_coupling_P_equals_0_collapse(tmp_path: Path):
    """If dynamics yields P(E)=0, the internally computed signal rate must collapse.

    We enforce P(E)=0 exactly by using 3-flavor dynamics with dm21=dm31=0 and all angles=0,
    so the state remains |nu_in>. With nu_in=mu and nu_out=e, Pe=0 for all E.
    """

    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_P0_example.json"
    df = _run_runner(
        tmp_path,
        pack,
        [
            "--flavors",
            "3",
            "--dm21_eV2",
            "0.0",
            "--dm31_eV2",
            "0.0",
            "--theta12_deg",
            "0.0",
            "--theta13_deg",
            "0.0",
            "--theta23_deg",
            "0.0",
            "--delta_cp_deg",
            "0.0",
        ],
    )

    # Robust criterion: signal collapses, total prediction tends to background.
    got_signal = (df["pred_sm"] - df["bkg"]).to_numpy(float)
    assert np.allclose(got_signal, np.zeros_like(got_signal), rtol=0, atol=1e-6)
    assert np.allclose(df["pred_sm"].to_numpy(float), df["bkg"].to_numpy(float), rtol=0, atol=1e-6)


def test_dynamics_to_rate_coupling_P_equals_1_unity(tmp_path: Path):
    """If dynamics yields P(E)=1, the kernel must reproduce the no-oscillation rate.

    Use 3-flavor with dm's and angles zero => rho stays in |nu_in>. With nu_in=mu, nu_out=mu,
    P=1 exactly. With flux=1, sigma=2, eff=0.5, exposure=10, the integrand is 1.
    True bins [0,1] and [1,3] give expected [10,20] (identity smearing, zero bkg).
    """

    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_smearing_example.json"
    df = _run_runner(
        tmp_path,
        pack,
        [
            "--flavors",
            "3",
            "--dm21_eV2",
            "0.0",
            "--dm31_eV2",
            "0.0",
            "--theta12_deg",
            "0.0",
            "--theta13_deg",
            "0.0",
            "--theta23_deg",
            "0.0",
            "--delta_cp_deg",
            "0.0",
        ],
    )

    expected = np.array([10.0, 20.0])
    assert np.allclose((df["pred_sm"] - df["bkg"]).to_numpy(float), expected, rtol=0, atol=2e-2)
    assert np.allclose((df["pred_geo"] - df["bkg"]).to_numpy(float), expected, rtol=0, atol=2e-2)


def test_dynamics_to_rate_coupling_energy_dependent_P_distorts_spectrum(tmp_path: Path):
    """Energy-dependent P(E) must produce the corresponding spectral distortion.

        Use 2-flavor vacuum disappearance and compare against the analytic survival probability
        (with E in GeV and L in km, consistent with the solver's KCONST=1.267 convention):
            P_surv(E) = 1 - sin^2(2θ) * sin^2(1.267 * dm2_runner * L / E)

    The internal rate kernel approximates P(E) per true bin by evaluating it at the bin center,
    so expected N_true[j] = exposure * bin_width[j] * P(E_center[j]) for the toy integrand=1.
    """

    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_energy_dependent_2flavor_example.json"

    L_km = 100.0
    dm2_runner = 2.50e-3
    theta23_deg = 30.0
    theta = math.radians(theta23_deg)

    df = _run_runner(
        tmp_path,
        pack,
        [
            "--flavors",
            "2",
            "--dm2_runner_eV2",
            str(dm2_runner),
            "--theta23_deg",
            str(theta23_deg),
        ],
    )

    E_centers = np.array([0.5, 2.0], dtype=float)
    bin_widths = np.array([1.0, 2.0], dtype=float)
    amp = math.sin(2.0 * theta) ** 2
    phase = 1.267 * dm2_runner * L_km / E_centers
    P = 1.0 - amp * (np.sin(phase) ** 2)
    P = np.clip(P, 0.0, 1.0)

    exposure = 10.0
    expected = exposure * bin_widths * P

    assert np.allclose((df["pred_sm"] - df["bkg"]).to_numpy(float), expected, rtol=0, atol=2e-2)
    assert np.allclose((df["pred_geo"] - df["bkg"]).to_numpy(float), expected, rtol=0, atol=2e-2)


def test_use_rate_kernel_ignores_pack_N_sig_sm_sentinel(tmp_path: Path):
    """Anti-fallback: prove --use_rate_kernel ignores pack-provided bins.N_sig_sm.

    The pack includes N_sig_sm=[999,999] but in kernel mode the runner must compute signal internally.
    We also set nonzero background so the assertion is about signal vs total.
    """

    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_ignores_pack_N_sig_sm_sentinel.json"
    df = _run_runner(
        tmp_path,
        pack,
        [
            "--flavors",
            "3",
            "--dm21_eV2",
            "0.0",
            "--dm31_eV2",
            "0.0",
            "--theta12_deg",
            "0.0",
            "--theta13_deg",
            "0.0",
            "--theta23_deg",
            "0.0",
            "--delta_cp_deg",
            "0.0",
        ],
    )

    # internal kernel signal for integrand=1 with exposure=10 and bin widths [1,2]
    expected_signal = np.array([10.0, 20.0])
    got_signal = (df["pred_sm"] - df["bkg"]).to_numpy(float)
    assert np.allclose(got_signal, expected_signal, rtol=0, atol=2e-2)

    # and specifically: it must NOT equal the sentinel
    assert not np.allclose(got_signal, np.array([999.0, 999.0]), rtol=0, atol=1e-6)


def test_energy_dependent_P_is_solver_driven_L0_vs_Lnonzero(tmp_path: Path):
    """Sanity: P(E) variation must come from the solver (baseline dependence), not a stub.

    With the same 2-flavor parameters:
    - at L=0 km, P_sm should be (approximately) equal across bins
    - at L>0, P_sm should differ across bins
    """

    pack_L0 = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_energy_dependent_2flavor_L0_example.json"
    pack_L = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_energy_dependent_2flavor_example.json"

    dm2_runner = 2.50e-3
    theta23_deg = 30.0

    df0 = _run_runner(
        tmp_path,
        pack_L0,
        [
            "--flavors",
            "2",
            "--dm2_runner_eV2",
            str(dm2_runner),
            "--theta23_deg",
            str(theta23_deg),
        ],
    )
    dfl = _run_runner(
        tmp_path,
        pack_L,
        [
            "--flavors",
            "2",
            "--dm2_runner_eV2",
            str(dm2_runner),
            "--theta23_deg",
            str(theta23_deg),
        ],
    )

    P0 = df0["P_sm"].to_numpy(float)
    P1 = dfl["P_sm"].to_numpy(float)

    assert abs(float(P0[0] - P0[1])) < 1e-6
    assert abs(float(P1[0] - P1[1])) > 1e-3
