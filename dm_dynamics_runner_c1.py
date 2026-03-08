from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from typing import cast

import numpy as np
import pandas as pd

from dm_dynamics_core_c1 import DMDynamicsC1Params, dm_accel, simulate_profile
from dm_dynamics_core_c1 import OrderMode


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _interp_fn(xp: np.ndarray, fp: np.ndarray):
    xp = np.asarray(xp, dtype=float)
    fp = np.asarray(fp, dtype=float)
    if xp.ndim != 1 or fp.ndim != 1 or xp.size != fp.size:
        raise ValueError("xp/fp must be 1D arrays of same length")

    order = np.argsort(xp)
    xp = xp[order]
    fp = fp[order]

    def f(x: float) -> float:
        return float(np.interp(float(x), xp, fp, left=float(fp[0]), right=float(fp[-1])))

    return f


def main() -> int:
    ap = argparse.ArgumentParser(description="DM-C1 dynamics runner (pack -> pred -> chi2 closure)")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_json", required=True)

    ap.add_argument("--dt", type=float, default=0.2)
    ap.add_argument("--n_steps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=2026)

    ap.add_argument("--A_dm", type=float, default=0.05)
    ap.add_argument("--texture_C", type=float, default=0.25)
    ap.add_argument("--texture_wr", type=float, default=0.35)
    ap.add_argument("--env_r0", type=float, default=2.0)
    ap.add_argument("--env_p", type=float, default=2.0)
    ap.add_argument("--eps_decay", type=float, default=0.5)
    ap.add_argument("--k_circ", type=float, default=0.8)

    ap.add_argument("--k_omega", type=float, default=0.25)
    ap.add_argument("--drive_strength", type=float, default=0.4)

    ap.add_argument("--k_eps", type=float, default=0.15)
    ap.add_argument("--gamma_eps", type=float, default=0.2)

    ap.add_argument("--k_g", type=float, default=0.8)
    ap.add_argument("--S0", type=float, default=1.0)
    ap.add_argument("--eps_w", type=float, default=0.6)
    ap.add_argument("--m_w", type=float, default=0.8)

    ap.add_argument("--order_mode", default="forward", choices=["forward", "reverse", "shuffle"])

    args = ap.parse_args()

    pack_path = Path(args.pack).resolve()
    out_csv = Path(args.out_csv)
    out_json = Path(args.out_json)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    pack = _load_json(pack_path)

    schema_version = str(pack.get("schema_version"))
    if schema_version not in {"dm_c1_pack_v1", "dm_c2_pack_v1"}:
        raise RuntimeError(f"Unexpected pack schema_version={schema_version}")

    galaxies = pack.get("galaxies")
    if not isinstance(galaxies, list) or not galaxies:
        raise RuntimeError("Pack must contain non-empty 'galaxies' list")

    p = DMDynamicsC1Params(
        A_dm=float(args.A_dm),
        texture_C=float(args.texture_C),
        texture_wr=float(args.texture_wr),
        env_r0=float(args.env_r0),
        env_p=float(args.env_p),
        eps_decay=float(args.eps_decay),
        k_circ=float(args.k_circ),
        k_omega=float(args.k_omega),
        drive_strength=float(args.drive_strength),
        k_eps=float(args.k_eps),
        gamma_eps=float(args.gamma_eps),
        k_g=float(args.k_g),
        S0=float(args.S0),
        eps_w=float(args.eps_w),
        m_w=float(args.m_w),
    )

    rows: list[dict[str, Any]] = []
    chi2_by_gal: dict[str, float] = {}
    ndof_by_gal: dict[str, int] = {}

    finite_all = True
    g_in_0_1_all = True
    eps_nonneg_all = True

    for gal in galaxies:
        name = str(gal.get("name", "gal"))
        obs = gal.get("obs", {})
        r_obs = np.asarray(obs.get("r", []), dtype=float)
        v_obs = np.asarray(obs.get("v_obs", []), dtype=float)
        sigma_v = np.asarray(obs.get("sigma_v", []), dtype=float)
        a_bary = np.asarray(obs.get("a_bary", []), dtype=float)

        if not (r_obs.size and r_obs.size == v_obs.size == sigma_v.size == a_bary.size):
            raise RuntimeError(f"Galaxy {name}: obs arrays must be same non-zero length")

        a_bary_fn = _interp_fn(r_obs, a_bary)
        v_target_fn = _interp_fn(r_obs, v_obs)
        sigma_fn = _interp_fn(r_obs, sigma_v)

        sim = simulate_profile(
            n_steps=int(args.n_steps),
            dt=float(args.dt),
            r0=float(gal.get("r0", float(r_obs[0]))),
            v0=float(gal.get("v0", float(v_obs[0]))),
            theta0=float(gal.get("theta0", 0.0)),
            omega0=float(gal.get("omega0", 0.0)),
            epsilon0=float(gal.get("epsilon0", 0.0)),
            g0=float(gal.get("g0", 0.5)),
            a_bary_fn=a_bary_fn,
            v_target_fn=v_target_fn,
            sigma_v_fn=sigma_fn,
            params=p,
            order_mode=cast(OrderMode, args.order_mode),
            shuffle_seed=int(args.seed),
            enforce_circular_velocity=True,
        )

        r_pred = sim["r"]
        theta = sim["theta"]
        omega = sim["omega"]
        eps = sim["epsilon"]
        g = sim["g"]

        a_b = np.array([a_bary_fn(float(x)) for x in r_pred], dtype=float)
        a_d = np.array(
            [dm_accel(float(r_pred[i]), theta=float(theta[i]), g=float(g[i]), epsilon=float(eps[i]), p=p) for i in range(r_pred.size)],
            dtype=float,
        )
        a_t = a_b + a_d
        v_pred = np.sqrt(np.maximum(r_pred * a_t, 0.0))

        v_obs_at = np.array([v_target_fn(float(x)) for x in r_pred], dtype=float)
        sig_at = np.maximum(np.array([sigma_fn(float(x)) for x in r_pred], dtype=float), 1e-12)
        pull = (v_pred - v_obs_at) / sig_at

        chi2 = float(np.sum(pull**2))
        chi2_by_gal[name] = chi2
        ndof_by_gal[name] = int(r_pred.size)

        finite_all = finite_all and bool(
            np.all(np.isfinite(r_pred))
            and np.all(np.isfinite(v_pred))
            and np.all(np.isfinite(a_b))
            and np.all(np.isfinite(a_d))
            and np.all(np.isfinite(theta))
            and np.all(np.isfinite(omega))
            and np.all(np.isfinite(eps))
            and np.all(np.isfinite(g))
        )
        g_in_0_1_all = g_in_0_1_all and bool((np.min(g) >= -1e-12) and (np.max(g) <= 1.0 + 1e-12))
        eps_nonneg_all = eps_nonneg_all and bool(np.min(eps) >= -1e-12)

        for i in range(int(r_pred.size)):
            rows.append(
                {
                    "galaxy": name,
                    "i": int(i),
                    "r": float(r_pred[i]),
                    "v_obs": float(v_obs_at[i]),
                    "sigma_v": float(sig_at[i]),
                    "a_bary": float(a_b[i]),
                    "a_dm": float(a_d[i]),
                    "v_pred": float(v_pred[i]),
                    "pull": float(pull[i]),
                    "g": float(g[i]),
                    "epsilon": float(eps[i]),
                    "theta": float(theta[i]),
                    "omega": float(omega[i]),
                    "order_mode": str(args.order_mode),
                    "dt": float(args.dt),
                    "n_steps": int(args.n_steps),
                }
            )

    df = pd.DataFrame(rows)
    df = df.sort_values(["galaxy", "i"]).reset_index(drop=True)
    df.to_csv(out_csv, index=False)

    summary: dict[str, Any] = {
        "pack": {"path": str(pack_path), "schema_version": schema_version},
        "params": {
            "dt": float(args.dt),
            "n_steps": int(args.n_steps),
            "seed": int(args.seed),
            "order_mode": str(args.order_mode),
            "dyn": {
                "A_dm": float(p.A_dm),
                "texture_C": float(p.texture_C),
                "texture_wr": float(p.texture_wr),
                "env_r0": float(p.env_r0),
                "env_p": float(p.env_p),
                "eps_decay": float(p.eps_decay),
                "k_circ": float(p.k_circ),
                "k_omega": float(p.k_omega),
                "drive_strength": float(p.drive_strength),
                "k_eps": float(p.k_eps),
                "gamma_eps": float(p.gamma_eps),
                "k_g": float(p.k_g),
                "S0": float(p.S0),
                "eps_w": float(p.eps_w),
                "m_w": float(p.m_w),
            },
        },
        "io": {
            "data_loaded_from_paths": True,
            "pack_json": str(pack_path),
            "out_csv": str(out_csv),
            "out_json": str(out_json),
        },
        "chi2": {
            "total": float(sum(chi2_by_gal.values())),
            "ndof": int(sum(ndof_by_gal.values())),
            "by_galaxy": chi2_by_gal,
            "ndof_by_galaxy": ndof_by_gal,
        },
        "telemetry": {
            "dm_dynamics_core_used": True,
            "proxy_overlay_used": False,
            "stiffgate_in_evolution": True,
            "boundedness": {
                "g_in_0_1": bool(g_in_0_1_all),
                "epsilon_nonneg": bool(eps_nonneg_all),
                "finite_all": bool(finite_all),
            },
            "poison": {"DM_POISON_PROXY_CALLS": os.environ.get("DM_POISON_PROXY_CALLS")},
        },
        "framing": {"stability_not_accuracy": True},
    }

    _write_json(out_json, summary)

    # ASCII-safe minimal stdout
    print("DM-C1 runner OK")
    print("out_csv:", str(out_csv))
    print("out_json:", str(out_json))
    print("chi2_total:", summary["chi2"]["total"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
