from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from dm_dynamics_core_c1 import DMDynamicsC1Params, simulate_profile


ROOT = Path(__file__).resolve().parents[3]


def _write_pack(path: Path, pack: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pack, indent=2, sort_keys=True), encoding="utf-8")


def _run_runner(tmp_path: Path, pack_path: Path, *, dt: float, n_steps: int, order_mode: str, extra_env: dict[str, str] | None = None):
    out_csv = tmp_path / f"out_dt{dt}_n{n_steps}_{order_mode}.csv"
    out_json = tmp_path / f"out_dt{dt}_n{n_steps}_{order_mode}.json"

    cmd = [
        sys.executable,
        str(ROOT / "dm_dynamics_runner_c1.py"),
        "--pack",
        str(pack_path),
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
        "--dt",
        str(dt),
        "--n_steps",
        str(int(n_steps)),
        "--seed",
        "2026",
        "--order_mode",
        str(order_mode),
        # fixed dyn params
        "--A_dm",
        "0.07",
        "--texture_C",
        "0.4",
        "--texture_wr",
        "0.6",
        "--env_r0",
        "2.5",
        "--env_p",
        "2.0",
        "--eps_decay",
        "0.7",
        "--k_circ",
        "0.9",
        "--k_omega",
        "0.25",
        "--drive_strength",
        "0.45",
        "--k_eps",
        "0.25",
        "--gamma_eps",
        "0.18",
        "--k_g",
        "0.9",
        "--S0",
        "1.0",
        "--eps_w",
        "0.6",
        "--m_w",
        "0.9",
    ]

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    print("[CMD]", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    print("[STDOUT]\n", cp.stdout)
    print("[STDERR]\n", cp.stderr)
    assert cp.returncode == 0

    df = pd.read_csv(out_csv)
    summary = json.loads(out_json.read_text(encoding="utf-8"))
    return df, summary


def test_dm_c1_integrity_closure_refinement_order_and_antifallback(tmp_path: Path):
    n0 = 240
    dt0 = 0.2

    # Synthetic pack generated from the same core (closure target).
    p = DMDynamicsC1Params(
        A_dm=0.07,
        texture_C=0.4,
        texture_wr=0.6,
        env_r0=2.5,
        env_p=2.0,
        eps_decay=0.7,
        k_circ=0.9,
        k_omega=0.25,
        drive_strength=0.45,
        k_eps=0.25,
        gamma_eps=0.18,
        k_g=0.9,
        S0=1.0,
        eps_w=0.6,
        m_w=0.9,
    )

    # Simple baryonic acceleration (toy) on a coarse reference grid.
    r_ref = np.linspace(0.2, 10.0, n0)
    a_bary_ref = 0.25 / (1.0 + (r_ref / 3.0) ** 2)

    a_bary_fn = lambda r: float(np.interp(float(r), r_ref, a_bary_ref, left=float(a_bary_ref[0]), right=float(a_bary_ref[-1])))

    # Build a self-consistent synthetic observation under mismatch feedback
    # using a short fixed-point iteration.
    sim = simulate_profile(
        n_steps=n0,
        dt=dt0,
        r0=float(r_ref[0]),
        v0=0.0,
        theta0=0.1,
        omega0=0.05,
        epsilon0=0.0,
        g0=0.5,
        a_bary_fn=a_bary_fn,
        v_target_fn=None,
        sigma_v_fn=None,
        params=p,
        order_mode="forward",
        shuffle_seed=0,
        enforce_circular_velocity=True,
    )

    for _ in range(3):
        r_prev = sim["r"].astype(float)
        v_prev = sim["v_pred"].astype(float)
        sig_prev = np.full_like(v_prev, 0.5, dtype=float)

        order = np.argsort(r_prev)
        r_sorted = r_prev[order]
        v_sorted = v_prev[order]
        s_sorted = sig_prev[order]

        v_target_fn = lambda r: float(np.interp(float(r), r_sorted, v_sorted, left=float(v_sorted[0]), right=float(v_sorted[-1])))
        sigma_fn = lambda r: float(np.interp(float(r), r_sorted, s_sorted, left=float(s_sorted[0]), right=float(s_sorted[-1])))

        sim = simulate_profile(
            n_steps=n0,
            dt=dt0,
            r0=float(r_prev[0]),
            v0=float(v_prev[0]),
            theta0=0.1,
            omega0=0.05,
            epsilon0=0.0,
            g0=0.5,
            a_bary_fn=a_bary_fn,
            v_target_fn=v_target_fn,
            sigma_v_fn=sigma_fn,
            params=p,
            order_mode="forward",
            shuffle_seed=0,
            enforce_circular_velocity=True,
        )

    r_obs = sim["r"].astype(float)
    v_obs = sim["v_pred"].astype(float)
    sigma_v = np.full_like(v_obs, 0.5, dtype=float)
    a_bary_obs = np.array([a_bary_fn(float(x)) for x in r_obs], dtype=float)

    pack = {
        "schema_version": "dm_c1_pack_v1",
        "galaxies": [
            {
                "name": "toy1",
                "r0": float(r_obs[0]),
                "v0": float(v_obs[0]),
                "theta0": 0.1,
                "omega0": 0.05,
                "epsilon0": 0.0,
                "g0": 0.5,
                "obs": {
                    "r": r_obs.tolist(),
                    "v_obs": v_obs.tolist(),
                    "sigma_v": sigma_v.tolist(),
                    "a_bary": a_bary_obs.tolist(),
                },
            }
        ],
    }

    pack_path = tmp_path / "pack.json"
    _write_pack(pack_path, pack)

    # Anti-fallback: poison proxy calls; DM-C1 runner must still pass.
    df1, summary1 = _run_runner(
        tmp_path / "run1",
        pack_path,
        dt=dt0,
        n_steps=n0,
        order_mode="forward",
        extra_env={"DM_POISON_PROXY_CALLS": "1"},
    )

    assert summary1["telemetry"]["dm_dynamics_core_used"] is True
    assert summary1["telemetry"]["proxy_overlay_used"] is False
    assert summary1["telemetry"]["stiffgate_in_evolution"] is True
    assert summary1["framing"]["stability_not_accuracy"] is True

    # Closure: data==pred => chi2 ~ 0.
    assert summary1["chi2"]["total"] <= 1e-8

    # Integrity / boundedness.
    for c in ["r", "v_pred", "a_bary", "a_dm", "g", "epsilon", "theta", "omega", "pull"]:
        assert c in df1.columns
        assert np.all(np.isfinite(df1[c].to_numpy(float)))

    gvals = df1["g"].to_numpy(float)
    eps = df1["epsilon"].to_numpy(float)
    assert gvals.min() >= -1e-12
    assert gvals.max() <= 1.0 + 1e-12
    assert eps.min() >= -1e-12

    # Refinement stability: dt halved, n doubled.
    df2, summary2 = _run_runner(
        tmp_path / "run2",
        pack_path,
        dt=dt0 / 2.0,
        n_steps=n0 * 2,
        order_mode="forward",
        extra_env={"DM_POISON_PROXY_CALLS": "1"},
    )

    # Interpolate fine solution onto coarse r points.
    r1 = df1["r"].to_numpy(float)
    v1 = df1["v_pred"].to_numpy(float)
    r2 = df2["r"].to_numpy(float)
    v2 = df2["v_pred"].to_numpy(float)

    order = np.argsort(r2)
    v2i = np.interp(r1, r2[order], v2[order], left=float(v2[order][0]), right=float(v2[order][-1]))

    denom = np.maximum(np.abs(v2i), 1e-12)
    rel = float(np.max(np.abs(v2i - v1) / denom))
    assert rel <= 0.05

    # Refined run uses different n_steps; closure-tight chi2 is not required here.
    assert np.isfinite(float(summary2["chi2"]["total"]))

    # Order sensitivity: forward vs reverse differs.
    df_fwd, _ = df1, summary1
    df_rev, _ = _run_runner(
        tmp_path / "run3",
        pack_path,
        dt=dt0,
        n_steps=n0,
        order_mode="reverse",
        extra_env={"DM_POISON_PROXY_CALLS": "1"},
    )

    v_fwd = df_fwd["v_pred"].to_numpy(float)
    v_rev = df_rev["v_pred"].to_numpy(float)
    max_abs = float(np.max(np.abs(v_fwd - v_rev)))
    assert max_abs >= 1e-3

    # Poison should actually trip legacy/proxy imports.
    cmd = [sys.executable, "-c", "import dm_thread_env_dropin"]
    env = os.environ.copy()
    env["DM_POISON_PROXY_CALLS"] = "1"
    cp = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    assert cp.returncode != 0
