from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

_INTEGRATION_ROOT = Path(__file__).resolve().parents[2]
if str(_INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_ROOT))

from mastereq.photon_sector import skyfold_anisotropy_prereg_check


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_skyfold_runner_matches_helper(tmp_path: Path):
    runner = _repo_root() / "integration_artifacts" / "entanglement_photon_bridge" / "prereg_birefringence_skyfold_v1_DROPIN.py"
    in_csv = tmp_path / "skyfold_sample.csv"
    out_csv = tmp_path / "skyfold_out.csv"
    out_json = tmp_path / "skyfold_out.json"

    rows = [
        {"label": "s1", "dec_deg": "25.0", "beta_deg": "0.30", "sigma_deg": "0.20"},
        {"label": "s2", "dec_deg": "40.0", "beta_deg": "0.10", "sigma_deg": "0.25"},
        {"label": "s3", "dec_deg": "-20.0", "beta_deg": "-0.25", "sigma_deg": "0.22"},
        {"label": "s4", "dec_deg": "-35.0", "beta_deg": "-0.05", "sigma_deg": "0.18"},
        {"label": "s5", "dec_deg": "15.0", "beta_deg": "0.05", "sigma_deg": "0.30"},
        {"label": "s6", "dec_deg": "-10.0", "beta_deg": "-0.12", "sigma_deg": "0.28"},
    ]
    with in_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    cmd = [
        sys.executable,
        str(runner),
        "--in_csv",
        str(in_csv),
        "--coord_col",
        "dec_deg",
        "--beta_col",
        "beta_deg",
        "--sigma_col",
        "sigma_deg",
        "--n_perm",
        "5000",
        "--seed",
        "20260307",
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr

    ref = skyfold_anisotropy_prereg_check(
        [25.0, 40.0, -20.0, -35.0, 15.0, -10.0],
        [0.30, 0.10, -0.25, -0.05, 0.05, -0.12],
        [0.20, 0.25, 0.22, 0.18, 0.30, 0.28],
        n_perm=5000,
        seed=20260307,
        abs_metric=False,
    )

    with out_json.open("r", encoding="utf-8") as f:
        got = json.load(f)

    assert got["coord_col"] == "dec_deg"
    assert math.isclose(float(got["statistic"]), float(ref["statistic"]), rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(float(got["p_value_signed"]), float(ref["p_value_signed"]), rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(float(got["p_value_abs"]), float(ref["p_value_abs"]), rel_tol=0.0, abs_tol=1e-15)
    assert got["verdict"] == ref["verdict"]
