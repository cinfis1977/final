import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def _make_toy_points_csv(path: Path) -> None:
    """Create a tiny deterministic DM dataset with an exactly realizable model.

    We deliberately choose A/alpha values that lie exactly on a tiny grid, so the
    CV runner should recover them fold-by-fold.
    """

    g0 = 1.0e-10
    A_true = 0.1
    alpha_true = 0.5

    galaxies = ["G0", "G1", "G2", "G3"]

    rows = []
    for gi, gal in enumerate(galaxies):
        # 3 radii/points per galaxy
        for pj, r_kpc in enumerate([1.0, 5.0, 10.0]):
            # vary g_bar mildly by galaxy/point (positive, physical scale)
            g_bar = (10 ** (-11.5 + 0.15 * gi + 0.05 * pj))

            g_geo = A_true * g0 * (g0 / (g_bar + g0)) ** alpha_true
            g_obs = g_bar + g_geo

            rows.append(
                {
                    "galaxy": gal,
                    "r_kpc": float(r_kpc),
                    "g_bar": float(g_bar),
                    "g_obs": float(g_obs),
                    # provide finite errors so chi2 is well-defined but does not change the optimum
                    "sigma_log10g": 0.05,
                }
            )

    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _run_dm_holdout(tmp_path: Path, *, env_model: str, extra_args: list[str] | None = None) -> tuple[pd.DataFrame, dict]:
    points = tmp_path / "points.csv"
    out_csv = tmp_path / f"out_{env_model}.csv"
    out_json = tmp_path / f"out_{env_model}.json"

    _make_toy_points_csv(points)

    cmd = [
        sys.executable,
        str(ROOT / "dm_holdout_cv_thread.py"),
        "--points_csv",
        str(points),
        "--env_model",
        env_model,
        "--g0",
        "1e-10",
        # tiny exact grid: A in {0.01, 0.1, 1.0}, alpha in {0.0, 0.5, 1.0}
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
        # 4 galaxies => 4 folds is stable/deterministic
        "--kfold",
        "4",
        "--seed",
        "123",
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]

    if extra_args:
        cmd.extend(extra_args)

    subprocess.run(cmd, cwd=str(ROOT), check=True)

    df = pd.read_csv(out_csv)
    summary = json.loads(out_json.read_text(encoding="utf-8"))
    return df, summary


def test_dm_toy_model_recovers_params_env_none(tmp_path: Path):
    df, summary = _run_dm_holdout(tmp_path, env_model="none")

    # Expect exact recovery because the true values lie on the grid.
    assert np.allclose(df["A_best"].to_numpy(float), 0.1, rtol=0, atol=0)
    assert np.allclose(df["alpha_best"].to_numpy(float), 0.5, rtol=0, atol=0)

    # Since g_obs is exactly modeled, chi2_best should be ~0 and improvements positive.
    assert (df["delta_chi2_train"].to_numpy(float) > 0.0).all()
    assert (df["delta_chi2_test"].to_numpy(float) > 0.0).all()

    # JSON framing lock must be present.
    # (We keep this tolerant to minor schema evolution; it's the contract we care about.)
    framing = summary.get("framing", {})
    assert framing.get("stability_not_accuracy", None) is True


def test_dm_legacy_no_env_scale_matches_env_none(tmp_path: Path):
    df_none, _ = _run_dm_holdout(tmp_path / "run_none", env_model="none")

    # legacy + --no_env_scale should map to env_model=none internally.
    df_legacy, _ = _run_dm_holdout(tmp_path / "run_legacy", env_model="legacy", extra_args=["--no_env_scale"])

    cols = [
        "fold",
        "A_best",
        "alpha_best",
        "chi2_train_base",
        "chi2_train_best",
        "delta_chi2_train",
        "chi2_test_base",
        "chi2_test_best",
        "delta_chi2_test",
    ]

    df_none = df_none.sort_values("fold").reset_index(drop=True)
    df_legacy = df_legacy.sort_values("fold").reset_index(drop=True)

    for c in cols:
        assert c in df_none.columns
        assert c in df_legacy.columns

    a = df_none[cols].to_numpy(float)
    b = df_legacy[cols].to_numpy(float)
    assert np.allclose(a, b, rtol=0, atol=0)
