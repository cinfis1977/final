from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _golden_file(rel: str) -> Path:
    p = _repo_root() / rel
    if not p.exists():
        pytest.skip(f"Golden output not found: {p}")
    return p


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _assert_frames_match(got: pd.DataFrame, gold: pd.DataFrame, *, atol: float, rtol: float) -> None:
    assert list(got.columns) == list(gold.columns)
    assert len(got) == len(gold)

    for col in got.columns:
        a = got[col]
        b = gold[col]
        if a.dtype == object or b.dtype == object:
            assert a.astype(str).tolist() == b.astype(str).tolist(), f"Column {col!r} differs"
            continue

        a_num = pd.to_numeric(a, errors="coerce").to_numpy(dtype=float)
        b_num = pd.to_numeric(b, errors="coerce").to_numpy(dtype=float)
        assert np.allclose(a_num, b_num, atol=float(atol), rtol=float(rtol)), f"Column {col!r} differs"


@pytest.mark.parametrize(
    "pack_rel,runner_rel,args_rel,golden_rel",
    [
        (
            "nova_channels.json",
            "nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py",
            [
                "--kernel",
                "rt",
                "--k_rt",
                "180",
                "--A",
                "-0.002",
                "--alpha",
                "0.7",
                "--n",
                "0",
                "--E0",
                "1",
                "--omega0_geom",
                "fixed",
                "--L0_km",
                "810",
                "--phi",
                "1.57079632679",
                "--zeta",
                "0.05",
                "--rho",
                "2.8",
                "--kappa_gate",
                "0",
                "--T0",
                "1",
                "--mu",
                "0",
                "--eta",
                "0",
                "--bin_shift_app",
                "2",
                "--bin_shift_dis",
                "0",
                "--breath_B",
                "0.3",
                "--breath_w0",
                "0.0038785094488762877",
                "--breath_gamma",
                "0.2",
                "--thread_C",
                "1.0",
                "--thread_w0",
                "-1",
                "--thread_gamma",
                "0.2",
                "--thread_weight_app",
                "0",
                "--thread_weight_dis",
                "1",
            ],
            "integration_artifacts/out/verdict_golden/out/WEAK/nova_BREATH_THREAD_test.csv",
        ),
        (
            "t2k_channels_real_approx.json",
            "nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py",
            [
                "--kernel",
                "rt",
                "--k_rt",
                "180",
                "--A",
                "-0.002",
                "--alpha",
                "0.7",
                "--n",
                "0",
                "--E0",
                "1",
                "--omega0_geom",
                "fixed",
                "--L0_km",
                "295",
                "--phi",
                "1.57079632679",
                "--zeta",
                "0.05",
                "--rho",
                "2.6",
                "--kappa_gate",
                "0",
                "--T0",
                "1",
                "--mu",
                "0",
                "--eta",
                "0",
                "--bin_shift_app",
                "0",
                "--bin_shift_dis",
                "0",
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
                "0",
                "--thread_weight_dis",
                "1",
            ],
            "integration_artifacts/out/verdict_golden/out/WEAK/t2k_BREATH_THREAD_validation_APPROXREAL.csv",
        ),
    ],
)
def test_e2e_weak_runner_regenerates_golden_outputs(
    tmp_path: Path,
    pack_rel: str,
    runner_rel: str,
    args_rel: list[str],
    golden_rel: str,
):
    root = _repo_root()
    runner = root / runner_rel
    pack = root / pack_rel
    golden = _golden_file(golden_rel)

    if not runner.exists():
        pytest.skip(f"Runner not found: {runner}")
    if not pack.exists():
        pytest.skip(f"Pack not found: {pack}")

    out_csv = tmp_path / "out.csv"
    cmd = [
        sys.executable,
        str(runner),
        "--pack",
        str(pack),
        *args_rel,
        "--out",
        str(out_csv),
    ]

    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    assert proc.returncode == 0, f"Runner failed. stdout=\n{proc.stdout}\n\nstderr=\n{proc.stderr}\n"
    assert out_csv.exists(), "Runner did not create output CSV"

    got = _read_csv(out_csv)
    gold = _read_csv(golden)

    # Tight tolerances, but allow tiny float drift across numpy/pandas versions.
    _assert_frames_match(got, gold, atol=1e-10, rtol=0.0)
