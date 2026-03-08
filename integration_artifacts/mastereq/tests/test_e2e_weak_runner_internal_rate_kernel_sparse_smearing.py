import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def _make_pack_sparse(tmp_path: Path, *, n: int = 25) -> Path:
    # True and reco bins are identical 1-GeV wide bins for deterministic rates.
    E_lo = [float(i) for i in range(n)]
    E_hi = [float(i + 1) for i in range(n)]
    E_ctr = [float(i) + 0.5 for i in range(n)]

    # Sparse migration S(rec,true) in COO:
    # each true bin sends 0.8 to same reco bin, 0.2 to neighbor.
    # last true bin sends 0.2 to previous to keep in-range.
    row_idx: list[int] = []
    col_idx: list[int] = []
    val: list[float] = []
    for j in range(n):
        row_idx.append(j)
        col_idx.append(j)
        val.append(0.8)
        if j < n - 1:
            row_idx.append(j + 1)
            col_idx.append(j)
            val.append(0.2)
        else:
            row_idx.append(j - 1)
            col_idx.append(j)
            val.append(0.2)

    pack = {
        "meta": {"baseline_km": 1.0, "note": "A3: sparse COO migration matrix example (25 bins)."},
        "channels": [
            {
                "name": "EXAMPLE_dis_sparse",
                "type": "disappearance",
                "baseline_km": 1.0,
                "nu_in": "mu",
                "nu_out": "mu",
                "rate_kernel": {
                    "exposure": 10.0,
                    "n_steps": 64,
                    "true_bins": {"E_lo": E_lo, "E_hi": E_hi},
                    "smear_sparse": {
                        "format": "coo",
                        "n_rec": n,
                        "n_true": n,
                        "row_idx": row_idx,
                        "col_idx": col_idx,
                        "val": val,
                    },
                    "flux_model": {"kind": "const", "value": 1.0},
                    "sigma_model": {"kind": "const", "value": 1.0},
                    "eff_model": {"kind": "const", "value": 1.0},
                },
                "bins": {
                    "E_lo": E_lo,
                    "E_hi": E_hi,
                    "E_ctr": E_ctr,
                    "N_obs": [0.0] * n,
                    "N_bkg_sm": [0.0] * n,
                },
            }
        ],
    }

    path = tmp_path / "pack_sparse.json"
    path.write_text(json.dumps(pack), encoding="utf-8")
    return path


def test_runner_internal_rate_kernel_sparse_smearing_deforms_spectrum(tmp_path: Path):
    """A3 e2e: sparse COO smearing works and is physically constrained.

    With flux=sigma=eff=1 and P(E)=1, each true bin has N_true=exposure*width=10.
    With the COO S defined in _make_pack_sparse, expected reconstructed signal is:
      N_rec[i] = 10 * sum_j S(i,j) (since N_true constant).
    """

    n = 25
    pack = _make_pack_sparse(tmp_path, n=n)
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
        # Enforce P(E)=1 (degenerate evolution)
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
        "30",
        "--out",
        str(out),
    ]

    subprocess.run(cmd, cwd=str(ROOT), check=True)
    df = pd.read_csv(out).sort_values(["channel", "i"]).reset_index(drop=True)

    # Recompute expected row sums from the definition in _make_pack_sparse.
    row_sums = np.zeros(n, dtype=float)
    for j in range(n):
        row_sums[j] += 0.8
        if j < n - 1:
            row_sums[j + 1] += 0.2
        else:
            row_sums[j - 1] += 0.2

    expected_signal = 10.0 * row_sums
    got_signal = (df["pred_sm"] - df["bkg"]).to_numpy(float)
    assert np.allclose(got_signal, expected_signal, rtol=0, atol=2e-2)
