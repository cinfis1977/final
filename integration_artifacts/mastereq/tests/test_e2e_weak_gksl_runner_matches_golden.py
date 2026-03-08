import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
GOLDEN_DIR = ROOT / "integration_artifacts" / "out" / "verdict_golden" / "out" / "WEAK"


def _run(cmd, cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Ensure stable ordering.
    if "channel" in df.columns and "i" in df.columns:
        df = df.sort_values(["channel", "i"]).reset_index(drop=True)
    return df


def _assert_close(df_new: pd.DataFrame, df_gold: pd.DataFrame) -> None:
    # The GKSL runner is numerically integrated; allow small tolerances.
    # We compare a subset of columns that define the WEAK contract.
    key_cols = ["channel", "i"]
    for c in key_cols:
        assert list(df_new[c]) == list(df_gold[c])

    compare_cols = [
        "E_lo",
        "E_hi",
        "E_ctr",
        "obs",
        "bkg",
        "pred_sm",
        "pred_geo",
        "P_sm",
        "P_geo",
        "dphi",
        "dphi_base",
        "dphi_breath",
        "dphi_thread",
        "thread_weight",
        "omega",
    ]

    for c in compare_cols:
        assert c in df_new.columns, f"missing new col {c}"
        assert c in df_gold.columns, f"missing golden col {c}"

    # Numeric comparisons.
    for c in compare_cols:
        if c in key_cols:
            continue
        a = df_new[c].astype(float).to_numpy()
        b = df_gold[c].astype(float).to_numpy()
        # Strict on inputs/phase bookkeeping; looser on integrated probabilities and predictions.
        if c in {"P_sm", "P_geo", "pred_sm", "pred_geo"}:
            tol = 2e-4
        else:
            tol = 5e-10
        diff = abs(a - b)
        assert (diff <= tol).all(), f"col={c} max_diff={diff.max()} tol={tol}"


def test_gksl_dynamics_runner_matches_golden_nova(tmp_path: Path):
    out = tmp_path / "out.csv"

    cmd = [
        sys.executable,
        str(ROOT / "nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py"),
        "--pack",
        str(ROOT / "nova_channels.json"),
        "--kernel",
        "rt",
        "--k_rt",
        "180",
        "--A",
        "-0.002",
        "--alpha",
        "0.7",
        "--n",
        "0.0",
        "--E0",
        "1.0",
        "--phi",
        "1.57079632679",
        "--omega0_geom",
        "fixed",
        "--L0_km",
        "810",
        "--zeta",
        "0.05",
        "--rho",
        "2.8",
        "--breath_B",
        "0.3",
        "--breath_w0",
        "0.0038785094488762877",
        "--breath_gamma",
        "0.2",
        "--thread_C",
        "1.0",
        "--thread_w0",
        "-1.0",
        "--thread_gamma",
        "0.2",
        "--thread_weight_app",
        "0.0",
        "--thread_weight_dis",
        "1.0",
        "--kappa_gate",
        "0.0",
        "--T0",
        "1.0",
        "--mu",
        "0.0",
        "--eta",
        "0.0",
        "--bin_shift_app",
        "2",
        "--bin_shift_dis",
        "0",
        "--out",
        str(out),
    ]

    _run(cmd, ROOT)

    df_new = _read_csv(out)
    df_gold = _read_csv(GOLDEN_DIR / "nova_BREATH_THREAD_test.csv")
    _assert_close(df_new, df_gold)


def test_gksl_dynamics_runner_matches_golden_t2k(tmp_path: Path):
    out = tmp_path / "out.csv"

    cmd = [
        sys.executable,
        str(ROOT / "nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py"),
        "--pack",
        str(ROOT / "t2k_channels_real_approx.json"),
        "--kernel",
        "rt",
        "--k_rt",
        "180",
        "--A",
        "-0.002",
        "--alpha",
        "0.7",
        "--n",
        "0.0",
        "--E0",
        "1.0",
        "--phi",
        "1.57079632679",
        "--omega0_geom",
        "fixed",
        "--L0_km",
        "295",
        "--zeta",
        "0.05",
        "--rho",
        "2.6",
        "--breath_B",
        "0.3",
        "--breath_w0",
        "0.00387850944887629",
        "--breath_gamma",
        "0.2",
        "--thread_C",
        "1.0",
        "--thread_w0",
        "0.00387850944887629",
        "--thread_gamma",
        "0.2",
        "--thread_weight_app",
        "0.0",
        "--thread_weight_dis",
        "1.0",
        "--kappa_gate",
        "0.0",
        "--T0",
        "1.0",
        "--mu",
        "0.0",
        "--eta",
        "0.0",
        "--bin_shift_app",
        "0",
        "--bin_shift_dis",
        "0",
        "--out",
        str(out),
    ]

    _run(cmd, ROOT)

    df_new = _read_csv(out)
    df_gold = _read_csv(GOLDEN_DIR / "t2k_BREATH_THREAD_validation_APPROXREAL.csv")
    _assert_close(df_new, df_gold)
