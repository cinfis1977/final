import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def test_runner_internal_rate_kernel_computes_pred_sm_without_reweight(tmp_path: Path):
    """E2E dynamics+rate-kernel test (no golden compare).

    Pack uses:
      exposure = 10
      flux(E)=1
      sigma(E)=2
      eff(E)=0.5
    => integrand=1

    For disappearance mu->mu with effectively trivial oscillation at L=1 km,
    P(E)≈1 so expected signal per true bin is exposure * bin_width.

    true bins: [0,1] width 1 => 10
               [1,3] width 2 => 20

    With identity smearing and zero background: pred_sm == [10,20].

    This advances closure because counts are produced internally from explicit
    flux/sigma/eff/exposure + state-derived P(E), not from pack N_sig_sm.
    """

    out = tmp_path / "out.csv"
    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_smearing_example.json"

    cmd = [
        sys.executable,
        str(ROOT / "nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py"),
        "--pack",
        str(pack),
        "--use_rate_kernel",
        "--flavors",
        "3",
        "--kernel",
        "none",
        "--A",
        "0.0",
        "--omega",
        "0.0",
        "--omega0_geom",
        "free",
        # make oscillations negligible: dm's ~0 and mixing ~0
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
        "--steps",
        "40",
        "--out",
        str(out),
    ]

    subprocess.run(cmd, cwd=str(ROOT), check=True)

    df = pd.read_csv(out).sort_values(["channel", "i"]).reset_index(drop=True)
    expected = np.array([10.0, 20.0])

    got = df["pred_sm"].to_numpy(dtype=float)
    assert np.allclose(got, expected, rtol=0, atol=2e-2)

    # With kernel none and A=0, GEO should match SM.
    got_geo = df["pred_geo"].to_numpy(dtype=float)
    assert np.allclose(got_geo, expected, rtol=0, atol=2e-2)

    # Telemetry should be present and sane in 3-flavor mode.
    assert np.max(np.abs(df["trace_rho_sm"].to_numpy(float) - 1.0)) < 1e-4
    assert np.min(df["min_eig_rho_sm"].to_numpy(float)) > -1e-4
