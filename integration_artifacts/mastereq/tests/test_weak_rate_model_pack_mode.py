import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def test_pack_rate_model_derives_sig_sm_via_integral(tmp_path: Path):
    """Sanity-check: --use_rate_model uses channel.rate_model to create sig_sm.

    We choose:
      flux(E)=1, sigma(E)=2, eff(E)=0.5, norm=10
    so integrand = 1*2*0.5 = 1, hence
      N_noosc(bin) = 10 * ∫ dE 1 = 10 * bin_width.

    With P_sm ~ 1 and P_geo ~ 1 (we set theta~0), pred_sm should equal sig_sm.
    """

    out = tmp_path / "out.csv"
    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_model_example.json"

    cmd = [
        sys.executable,
        str(ROOT / "nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py"),
        "--pack",
        str(pack),
        "--use_rate_model",
        "--kernel",
        "none",
        "--A",
        "0.0",
        "--omega",
        "0.0",
        "--omega0_geom",
        "free",
        "--dm2_runner_eV2",
        "0.0",
        "--theta23_deg",
        "0.0",
        "--theta13_deg",
        "0.0",
        "--steps",
        "24",
        "--out",
        str(out),
    ]

    subprocess.run(cmd, cwd=str(ROOT), check=True)

    df = pd.read_csv(out).sort_values(["channel", "i"]).reset_index(drop=True)
    assert list(df["channel"].unique()) == ["EXAMPLE_app"]

    # Expected: sig_sm = 10 * bin_widths = [10*(1-0), 10*(3-1)] = [10, 20]
    expected = np.array([10.0, 20.0])
    got = df.groupby("channel")["pred_sm"].apply(lambda s: s.to_numpy()).iloc[0]

    assert np.allclose(got, expected, rtol=0, atol=1e-2)
