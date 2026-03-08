import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def _run_kernel_pack(tmp_path: Path, pack: Path) -> np.ndarray:
    out = tmp_path / "out.csv"
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
        # force P(E)=1 exactly for mu->mu
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
    # compare signal only (pred_sm - bkg)
    return (df["pred_sm"] - df["bkg"]).to_numpy(float)


def test_tabular_constant_models_match_const_models(tmp_path: Path):
    """E2E: tabular-constant models reproduce old const model predictions."""

    pack_const = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_smearing_example.json"
    pack_tab = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_tabular_constant_example.json"

    sig_const = _run_kernel_pack(tmp_path, pack_const)
    sig_tab = _run_kernel_pack(tmp_path, pack_tab)
    assert np.allclose(sig_tab, sig_const, rtol=0, atol=2e-2)


def test_tabular_shaped_flux_deforms_spectrum(tmp_path: Path):
    """E2E: shaped tabular flux deforms the reconstructed spectrum as expected.

    With sigma=2 and eff=0.5 (so sigma*eff=1) and P=1, the per-bin signal becomes:
      N_true = exposure * flux_value * bin_width.

    Using flux histogram values [1,3] on true bins [0,1] and [1,3]:
      widths = [1,2] => expected = 10*[1*1, 3*2] = [10,60].
    """

    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_kernel_tabular_shaped_example.json"
    sig = _run_kernel_pack(tmp_path, pack)
    expected = np.array([10.0, 60.0])
    assert np.allclose(sig, expected, rtol=0, atol=2e-2)
