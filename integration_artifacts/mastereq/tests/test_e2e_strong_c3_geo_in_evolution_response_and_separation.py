import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from integration_artifacts.mastereq.strong_c1_eikonal_amplitude import (
    EikonalC1Params,
    EikonalC1State,
    forward_amplitude_from_state,
    t_from_sqrts,
)


ROOT = Path(__file__).resolve().parents[3]


def _predict_sigma_rho(sqrts: np.ndarray, pars: EikonalC1Params) -> tuple[np.ndarray, np.ndarray]:
    t_arr = t_from_sqrts(sqrts, s0_GeV2=pars.s0_GeV2)
    order = np.argsort(t_arr)
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))

    t_sorted = t_arr[order]
    state = EikonalC1State.initialize(pars)

    sigma = np.empty_like(t_sorted, dtype=float)
    rho = np.empty_like(t_sorted, dtype=float)

    for i, t in enumerate(t_sorted):
        state.advance_to(float(t), pars)
        F = forward_amplitude_from_state(state)
        im = float(np.imag(F))
        re = float(np.real(F))
        sigma[i] = float(pars.sigma_norm_mb) * im
        im_safe = im if abs(im) > 1e-30 else (1e-30 if im >= 0 else -1e-30)
        rho[i] = re / im_safe

    return sigma[inv], rho[inv]


def test_strong_c3_geo_in_evolution_response_and_separation(tmp_path: Path):
    runner = ROOT / "strong_amplitude_pack_chi2_c3.py"
    assert runner.exists(), f"Missing runner: {runner}"

    sqrts = np.asarray([7.0, 20.0, 200.0, 13000.0], dtype=float)
    pars0 = EikonalC1Params()  # geo_A defaults to 0

    sig0, rho0 = _predict_sigma_rho(sqrts, pars0)

    # Valid dense response: identity (column-stochastic).
    I = np.eye(len(sqrts), dtype=float)
    # Valid sparse response: identity COO.
    n = int(len(sqrts))
    coo_I = {"n": n, "i": list(range(n)), "j": list(range(n)), "v": [1.0] * n}

    sig_unc = np.full_like(sig0, 1.0)
    rho_unc = np.full_like(rho0, 0.05)

    pack0 = {
        "meta": {"name": "strong_c3_pack_geo0", "note": "GEO=0 baseline"},
        "scan": {"sqrts_GeV": sqrts.tolist(), "channel": "pp"},
        "model": {
            "s0_GeV2": pars0.s0_GeV2,
            "dt_max": pars0.dt_max,
            "nb": pars0.nb,
            "b_max": pars0.b_max,
            "sigma_norm_mb": pars0.sigma_norm_mb,
        },
        "geo": {"A": 0.0, "template": "cos", "phi0": 0.0, "omega": 1.0},
        "response": {
            "validate": True,
            "sigma_tot_mb": {"dense": I.tolist()},
            "rho": {"sparse_coo": coo_I},
        },
        "data": {
            "sigma_tot_mb": {"y": sig0.tolist(), "unc": sig_unc.tolist()},
            "rho": {"y": rho0.tolist(), "unc": rho_unc.tolist()},
        },
    }

    pack0_path = tmp_path / "pack0.json"
    pack0_path.write_text(json.dumps(pack0, indent=2), encoding="utf-8")

    out0_csv = tmp_path / "out0.csv"
    out0_json = tmp_path / "out0.json"

    env = dict(os.environ)
    env["STRONG_C1_POISON_PDG_CALLS"] = "1"

    cmd0 = [
        sys.executable,
        str(runner),
        "--pack",
        str(pack0_path),
        "--out_csv",
        str(out0_csv),
        "--out_json",
        str(out0_json),
    ]
    proc0 = subprocess.run(cmd0, cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert proc0.returncode == 0, f"GEO=0 run failed. stdout=\n{proc0.stdout}\n\nstderr=\n{proc0.stderr}\n"

    summ0 = json.loads(out0_json.read_text(encoding="utf-8"))
    assert summ0["amplitude_core_used"] is True
    assert summ0["pdg_baseline_used"] is False
    assert summ0["anti_fallback"]["pdg_call_poison_active"] is True
    assert summ0["geo"]["geo_applied_in_evolution"] is False
    assert float(summ0["chi2"]["total"]) <= 1e-10

    # GEO != 0: keep data fixed (from GEO=0), so chi2 must change.
    pack1 = dict(pack0)
    pack1["meta"] = {"name": "strong_c3_pack_geo1", "note": "GEO!=0 should separate"}
    pack1["geo"] = {"A": 0.25, "template": "cos", "phi0": 0.3, "omega": 1.0}

    pack1_path = tmp_path / "pack1.json"
    pack1_path.write_text(json.dumps(pack1, indent=2), encoding="utf-8")

    out1_csv = tmp_path / "out1.csv"
    out1_json = tmp_path / "out1.json"

    cmd1 = [
        sys.executable,
        str(runner),
        "--pack",
        str(pack1_path),
        "--out_csv",
        str(out1_csv),
        "--out_json",
        str(out1_json),
    ]
    proc1 = subprocess.run(cmd1, cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert proc1.returncode == 0, f"GEO!=0 run failed. stdout=\n{proc1.stdout}\n\nstderr=\n{proc1.stderr}\n"

    summ1 = json.loads(out1_json.read_text(encoding="utf-8"))
    assert summ1["geo"]["geo_applied_in_evolution"] is True
    chi2_0 = float(summ0["chi2"]["total"])
    chi2_1 = float(summ1["chi2"]["total"])
    assert abs(chi2_1 - chi2_0) > 0.5

    # Dense response lock: negative entries must fail.
    pack_bad_dense = dict(pack0)
    pack_bad_dense["meta"] = {"name": "strong_c3_pack_bad_dense"}
    bad = np.eye(n, dtype=float)
    bad[0, 0] = -0.1
    pack_bad_dense["response"] = {"validate": True, "sigma_tot_mb": {"dense": bad.tolist()}}

    pack_bad_dense_path = tmp_path / "pack_bad_dense.json"
    pack_bad_dense_path.write_text(json.dumps(pack_bad_dense, indent=2), encoding="utf-8")

    proc_bad_dense = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--pack",
            str(pack_bad_dense_path),
            "--out_csv",
            str(tmp_path / "bad_dense.csv"),
            "--out_json",
            str(tmp_path / "bad_dense.json"),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc_bad_dense.returncode != 0

    # Sparse response lock: negative entries must fail.
    pack_bad_sparse = dict(pack0)
    pack_bad_sparse["meta"] = {"name": "strong_c3_pack_bad_sparse"}
    bad_coo = {"n": n, "i": [0], "j": [0], "v": [-1.0]}
    pack_bad_sparse["response"] = {"validate": True, "rho": {"sparse_coo": bad_coo}}

    pack_bad_sparse_path = tmp_path / "pack_bad_sparse.json"
    pack_bad_sparse_path.write_text(json.dumps(pack_bad_sparse, indent=2), encoding="utf-8")

    proc_bad_sparse = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--pack",
            str(pack_bad_sparse_path),
            "--out_csv",
            str(tmp_path / "bad_sparse.csv"),
            "--out_json",
            str(tmp_path / "bad_sparse.json"),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc_bad_sparse.returncode != 0

    # Schema smoke
    df = pd.read_csv(out1_csv)
    for col in ["sqrts_GeV", "sigma_tot_pred_mb", "rho_pred", "F_re", "F_im", "S_abs_max"]:
        assert col in df.columns
    assert summ1["framing"]["stability_not_accuracy"] is True
    assert all(summ1["integrity"].values())
