import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def test_runner_3flavor_writes_density_matrix_telemetry(tmp_path: Path):
    """Dynamics e2e test (runner-level):

    Requirements per bin (SM and GEO evolutions):
    1) trace(rho) ≈ 1
    2) rho ⪰ 0 (min eigenvalue >= -eps)
    3) hermiticity error small
    4) Pe+Pmu+Ptau ≈ 1

    This is a dynamics test because it validates internal-state integrity at the runner output boundary.
    """

    out = tmp_path / "out.csv"
    pack = ROOT / "integration_artifacts" / "packs" / "examples" / "weak_rate_model_example.json"

    cmd = [
        sys.executable,
        str(ROOT / "nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py"),
        "--pack",
        str(pack),
        "--use_rate_model",
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
        "--steps",
        "220",
        "--out",
        str(out),
    ]

    subprocess.run(cmd, cwd=str(ROOT), check=True)

    df = pd.read_csv(out).sort_values(["channel", "i"]).reset_index(drop=True)

    required_cols = [
        "trace_rho_sm",
        "min_eig_rho_sm",
        "purity_rho_sm",
        "herm_err_rho_sm",
        "Pe_sm",
        "Pmu_sm",
        "Ptau_sm",
        "trace_rho_geo",
        "min_eig_rho_geo",
        "purity_rho_geo",
        "herm_err_rho_geo",
        "Pe_geo",
        "Pmu_geo",
        "Ptau_geo",
    ]
    for c in required_cols:
        assert c in df.columns, f"missing column {c}"

    # tolerances: RK4 + per-bin evolution
    eps_trace = 5e-6
    eps_eig = 5e-6
    eps_herm = 5e-6
    eps_simplex = 5e-5

    for prefix in ("sm", "geo"):
        tr = df[f"trace_rho_{prefix}"].to_numpy(dtype=float)
        mineig = df[f"min_eig_rho_{prefix}"].to_numpy(dtype=float)
        purity = df[f"purity_rho_{prefix}"].to_numpy(dtype=float)
        herm = df[f"herm_err_rho_{prefix}"].to_numpy(dtype=float)

        Pe = df[f"Pe_{prefix}"].to_numpy(dtype=float)
        Pmu = df[f"Pmu_{prefix}"].to_numpy(dtype=float)
        Ptau = df[f"Ptau_{prefix}"].to_numpy(dtype=float)

        assert np.all(np.isfinite(tr))
        assert np.all(np.isfinite(mineig))
        assert np.all(np.isfinite(purity))
        assert np.all(np.isfinite(herm))

        assert np.max(np.abs(tr - 1.0)) <= eps_trace
        assert np.min(mineig) >= -eps_eig
        assert np.max(herm) <= eps_herm

        simplex = Pe + Pmu + Ptau
        assert np.max(np.abs(simplex - 1.0)) <= eps_simplex

        assert np.min(Pe) >= -1e-6 and np.min(Pmu) >= -1e-6 and np.min(Ptau) >= -1e-6
        assert np.max(Pe) <= 1.0 + 1e-6 and np.max(Pmu) <= 1.0 + 1e-6 and np.max(Ptau) <= 1.0 + 1e-6

        # Purity bounds (PSD trace-1 implies 1/3 <= Tr(rho^2) <= 1)
        assert np.min(purity) >= (1.0 / 3.0) - 2e-3
        assert np.max(purity) <= 1.0 + 2e-3

    # For this example channel (mu->e appearance), runner's P_sm should match Pe_sm.
    assert np.max(np.abs(df["P_sm"].to_numpy(float) - df["Pe_sm"].to_numpy(float))) < 5e-6
    assert np.max(np.abs(df["P_geo"].to_numpy(float) - df["Pe_geo"].to_numpy(float))) < 5e-6
