import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def test_runner_internal_rate_kernel_with_nontrivial_smearing(tmp_path: Path):
    """E2E test: nontrivial physical smearing deforms the reconstructed spectrum.

    With exposure=10 and integrand=1 (flux=1, sigma=2, eff=0.5), true-bin counts are:
      N_true = [10, 20]

    Smearing S (rec-by-true):
      [[0.8,0.2],
       [0.2,0.8]]

    => N_rec = S @ N_true = [12, 18]

    This is a dynamics+rate-kernel test (no golden compare).
    """

    out = tmp_path / "out.csv"
    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_smearing_physical_example.json"

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
        # Make P(E)≈1 by turning off masses+mixing.
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
    expected = np.array([12.0, 18.0])

    assert np.allclose(df["pred_sm"].to_numpy(float), expected, rtol=0, atol=2e-2)
    assert np.allclose(df["pred_geo"].to_numpy(float), expected, rtol=0, atol=2e-2)
