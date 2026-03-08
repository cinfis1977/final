import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import dm_thread_env_dropin as dropin
import dm_thread_env_dropin_STIFFGATE as dropin_sg


ROOT = Path(__file__).resolve().parents[3]


def _make_points(tmp_path: Path) -> Path:
    """Small deterministic dataset with multiple galaxies.

    We deliberately make galaxies have different (r, g_bar) distributions so the
    TRAIN-set median of the thread env raw factor changes fold-to-fold. This lets
    us detect leakage (using full-data normalization) vs correct CV-safe behavior.
    """

    g0 = 1.0e-10
    rows = []
    # 4 galaxies, 3 points each.
    for gal_i, gal in enumerate(["G0", "G1", "G2", "G3"]):
        for pj, r_kpc in enumerate([1.0, 4.0, 12.0]):
            # Spread g_bar strongly by galaxy so thread env raw distribution shifts with holdout.
            g_bar = (10 ** (-12.3 + 0.25 * gal_i + 0.05 * pj))
            # Keep g_obs close but not identical (avoid perfect degeneracy); not used in this test.
            g_obs = g_bar + 0.02 * g0
            rows.append(
                {
                    "galaxy": gal,
                    "r_kpc": float(r_kpc),
                    "g_bar": float(g_bar),
                    "g_obs": float(g_obs),
                    "sigma_log10g": 0.08,
                }
            )

    df = pd.DataFrame(rows)
    path = tmp_path / "points.csv"
    df.to_csv(path, index=False)
    return path


def _make_folds(galaxies: np.ndarray, kfold: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(int(seed))
    gal = np.array(sorted(set(galaxies.tolist())))
    rng.shuffle(gal)
    return list(np.array_split(gal, int(kfold)))


def test_dm_thread_normscale_is_train_only_no_leakage(tmp_path: Path):
    points = _make_points(tmp_path)
    df_all = pd.read_csv(points)

    out_csv = tmp_path / "out.csv"
    out_json = tmp_path / "out.json"

    seed = 123
    kfold = 4

    cmd = [
        sys.executable,
        str(ROOT / "dm_holdout_cv_thread.py"),
        "--points_csv",
        str(points),
        "--env_model",
        "thread",
        "--g0",
        "1e-10",
        "--thread_norm",
        "median",
        "--A_min",
        "0.01",
        "--A_max",
        "1.0",
        "--nA",
        "3",
        "--alpha_min",
        "0.0",
        "--alpha_max",
        "1.0",
        "--nAlpha",
        "3",
        "--kfold",
        str(kfold),
        "--seed",
        str(seed),
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]

    subprocess.run(cmd, cwd=str(ROOT), check=True)

    out = pd.read_csv(out_csv)
    assert "thread_norm_scale_train" in out.columns

    s = json.loads(out_json.read_text(encoding="utf-8"))
    assert s["params"]["env_model"] == "thread"
    assert s["framing"]["stability_not_accuracy"] is True

    # Recompute expected norm_scale fold-by-fold from TRAIN only.
    gal_col = "galaxy"
    galaxies = df_all[gal_col].astype(str).to_numpy()
    folds = _make_folds(galaxies, kfold=kfold, seed=seed)

    for fold_idx, test_gals in enumerate(folds):
        df_train = df_all[~df_all[gal_col].astype(str).isin(set(test_gals.tolist()))].copy()

        r_m = df_train["r_kpc"].to_numpy(float) * float(dropin.KPC_TO_M)
        g_bar = df_train["g_bar"].to_numpy(float)
        e_raw = dropin.compute_env_thread_raw(
            r_m,
            g_bar,
            g0=1.0e-10,
            mode="down",
            q=0.6,
            xi=0.5,
            r_weight_power=1.0,
            thread_S0=None,
            thread_gate_p=4.0,
            thread_k2=1.0,
            thread_k4=0.0,
        )
        expected = float(np.median(e_raw))
        got = float(out.loc[out["fold"] == fold_idx, "thread_norm_scale_train"].iloc[0])
        assert np.isfinite(got)
        assert np.isclose(got, expected, rtol=0, atol=1e-12)


def test_dm_stiffgate_calibration_and_normscale_reported(tmp_path: Path):
    points = _make_points(tmp_path)
    df_all = pd.read_csv(points)

    out_csv = tmp_path / "out.csv"
    out_json = tmp_path / "out.json"

    seed = 123
    kfold = 4

    cmd = [
        sys.executable,
        str(ROOT / "dm_holdout_cv_thread_STIFFGATE.py"),
        "--points_csv",
        str(points),
        "--env_model",
        "thread",
        "--thread_calibrate_from_galaxy",
        "--g0",
        "1e-10",
        "--thread_norm",
        "median",
        "--A_min",
        "0.01",
        "--A_max",
        "1.0",
        "--nA",
        "3",
        "--alpha_min",
        "0.0",
        "--alpha_max",
        "1.0",
        "--nAlpha",
        "3",
        "--kfold",
        str(kfold),
        "--seed",
        str(seed),
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]

    subprocess.run(cmd, cwd=str(ROOT), check=True)

    out = pd.read_csv(out_csv)
    assert "thread_norm_scale_train" in out.columns

    s = json.loads(out_json.read_text(encoding="utf-8"))
    assert s["params"]["env_model"] == "thread"
    assert s["telemetry"]["thread_calibration_used"] is True
    assert s["framing"]["stability_not_accuracy"] is True
    assert isinstance(s.get("thread_calibration"), list)
    assert len(s["thread_calibration"]) == kfold

    # Validate calibration rows are finite.
    for row in s["thread_calibration"]:
        assert np.isfinite(float(row["S0"]))
        assert np.isfinite(float(row["k4"]))
        assert np.isfinite(float(row["S_hi"]))
        assert np.isfinite(float(row["Sc"]))

    # Recompute expected norm_scale using calibrated (S0,k4) on TRAIN only.
    gal_col = "galaxy"
    galaxies = df_all[gal_col].astype(str).to_numpy()
    folds = _make_folds(galaxies, kfold=kfold, seed=seed)

    calib_by_fold = {int(r["fold"]): r for r in s["thread_calibration"]}

    for fold_idx, test_gals in enumerate(folds):
        df_train = df_all[~df_all[gal_col].astype(str).isin(set(test_gals.tolist()))].copy()

        calib = calib_by_fold[int(fold_idx)]
        S0 = float(calib["S0"])
        k4 = float(calib["k4"])

        r_m = df_train["r_kpc"].to_numpy(float) * float(dropin_sg.KPC_TO_M)
        g_bar = df_train["g_bar"].to_numpy(float)
        e_raw = dropin_sg.compute_env_thread_raw(
            r_m,
            g_bar,
            g0=1.0e-10,
            mode="down",
            q=0.6,
            xi=0.5,
            r_weight_power=1.0,
            thread_S0=S0,
            thread_gate_p=4.0,
            thread_k2=1.0,
            thread_k4=k4,
        )
        expected = float(np.median(e_raw))
        got = float(out.loc[out["fold"] == fold_idx, "thread_norm_scale_train"].iloc[0])
        assert np.isfinite(got)
        assert np.isclose(got, expected, rtol=0, atol=1e-12)
