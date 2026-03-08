import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def test_e2e_tabular_flux_sigma_eff_product_lock(tmp_path: Path):
    """A2 e2e: shaped tabular flux×sigma×eff must bind multiplicatively.

    Pack uses histogram-constant values per true bin and identity smearing.
    With P(E)=1 enforced via degenerate 3-flavor mu->mu, the expected per-bin signal is:

      N_true[j] = exposure * width[j] * flux[j] * sigma[j] * eff[j]

    For the pack:
      widths = [1,2]
      flux   = [2,1]
      sigma  = [1,4]
      eff    = [0.5,0.2]
      product= [1.0,0.8]
      exposure=10
    => expected signal = [10, 16]
    """

    out = tmp_path / "out.csv"
    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_tabular_shaped_product_example.json"

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
        # enforce P(E)=1 exactly
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
    signal = (df["pred_sm"] - df["bkg"]).to_numpy(float)
    expected = np.array([10.0, 16.0])
    assert np.allclose(signal, expected, rtol=0, atol=2e-2)
