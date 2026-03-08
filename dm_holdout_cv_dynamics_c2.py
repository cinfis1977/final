#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DM-C2 holdout k-fold CV over galaxies using the DM-C1 dynamics core.

Scope
- Works on a DM-C2 pack built from real SPARC points (schema_version=dm_c2_pack_v1).
- Galaxy-holdout CV: folds are split by galaxy name, not by points.
- Train-only calibration: choose A_dm on TRAIN fold (grid search), then evaluate on TEST.

This is an IO/closure + leakage-safety + determinism artifact.
It is not an accuracy claim.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from typing import cast

from dm_dynamics_core_c1 import DMDynamicsC1Params, OrderMode, simulate_profile


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _make_galaxy_folds(galaxies: Iterable[str], *, kfold: int, seed: int) -> list[list[str]]:
    rng = np.random.default_rng(int(seed))
    gal = np.array(sorted(set([str(g) for g in galaxies])))
    rng.shuffle(gal)
    folds = np.array_split(gal, int(kfold))
    return [list(map(str, f.tolist())) for f in folds]


@dataclass(frozen=True)
class EvalConfig:
    dt: float
    n_steps: int
    seed: int
    order_mode: str
    sigma_floor: float


def _galaxy_chi2(gal: dict[str, Any], *, p: DMDynamicsC1Params, cfg: EvalConfig) -> tuple[float, int]:
    obs = gal.get("obs", {})
    r_obs = np.asarray(obs.get("r", []), dtype=float)
    v_obs = np.asarray(obs.get("v_obs", []), dtype=float)
    sigma_v = np.asarray(obs.get("sigma_v", []), dtype=float)
    a_bary = np.asarray(obs.get("a_bary", []), dtype=float)

    if not (r_obs.size and r_obs.size == v_obs.size == sigma_v.size == a_bary.size):
        raise RuntimeError(f"Galaxy {gal.get('name','gal')}: obs arrays must be same non-zero length")

    order = np.argsort(r_obs)
    r_obs = r_obs[order]
    v_obs = v_obs[order]
    sigma_v = sigma_v[order]
    a_bary = a_bary[order]

    def a_bary_fn(x: float) -> float:
        return float(np.interp(float(x), r_obs, a_bary, left=float(a_bary[0]), right=float(a_bary[-1])))

    def v_target_fn(x: float) -> float:
        return float(np.interp(float(x), r_obs, v_obs, left=float(v_obs[0]), right=float(v_obs[-1])))

    def sigma_v_fn(x: float) -> float:
        s = float(np.interp(float(x), r_obs, sigma_v, left=float(sigma_v[0]), right=float(sigma_v[-1])))
        return float(max(s, float(cfg.sigma_floor)))

    sim = simulate_profile(
        n_steps=int(cfg.n_steps),
        dt=float(cfg.dt),
        r0=float(gal.get("r0", float(r_obs[0]))),
        v0=float(gal.get("v0", float(v_obs[0]))),
        theta0=float(gal.get("theta0", 0.0)),
        omega0=float(gal.get("omega0", 0.0)),
        epsilon0=float(gal.get("epsilon0", 0.0)),
        g0=float(gal.get("g0", 0.5)),
        a_bary_fn=a_bary_fn,
        v_target_fn=v_target_fn,
        sigma_v_fn=sigma_v_fn,
        params=p,
        order_mode=cast(OrderMode, str(cfg.order_mode)),
        shuffle_seed=int(cfg.seed),
        enforce_circular_velocity=True,
    )

    r_pred = np.asarray(sim["r"], dtype=float)
    v_pred = np.asarray(sim["v_pred"], dtype=float)

    v_obs_at = np.array([v_target_fn(float(x)) for x in r_pred], dtype=float)
    sig_at = np.array([sigma_v_fn(float(x)) for x in r_pred], dtype=float)

    pull = (v_pred - v_obs_at) / np.maximum(sig_at, float(cfg.sigma_floor))
    chi2 = float(np.sum(pull**2))
    ndof = int(r_pred.size)
    if not np.isfinite(chi2):
        raise RuntimeError(f"Galaxy {gal.get('name','gal')}: non-finite chi2")

    return chi2, ndof


def _pack_galaxies(pack: dict[str, Any]) -> list[dict[str, Any]]:
    gal = pack.get("galaxies")
    if not isinstance(gal, list) or not gal:
        raise RuntimeError("Pack must contain non-empty 'galaxies' list")
    return [g for g in gal if isinstance(g, dict)]


def main() -> int:
    ap = argparse.ArgumentParser(description="DM-C2 dynamics holdout k-fold CV (train-only A_dm calibration)")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--kfold", type=int, default=5)
    ap.add_argument("--seed", type=int, default=2026)

    ap.add_argument("--dt", type=float, default=0.001)
    ap.add_argument("--n_steps", type=int, default=240)
    ap.add_argument("--order_mode", default="forward", choices=["forward", "reverse", "shuffle"])
    ap.add_argument("--sigma_floor", type=float, default=1e-6)

    ap.add_argument("--A_min", type=float, default=0.0)
    ap.add_argument("--A_max", type=float, default=0.2)
    ap.add_argument("--nA", type=int, default=21)

    ap.add_argument(
        "--sensitivity_check",
        action="store_true",
        help="Print a fit-free sensitivity diagnostic for A_dm (A=0 vs A_probe) before CV.",
    )
    ap.add_argument(
        "--A_probe",
        type=float,
        default=None,
        help="A value to probe for sensitivity_check (default: A_max; snapped to nearest grid value).",
    )

    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_json", required=True)

    args = ap.parse_args()

    pack_path = Path(args.pack).resolve()
    pack = _load_json(pack_path)

    schema = str(pack.get("schema_version"))
    if schema != "dm_c2_pack_v1":
        raise RuntimeError(f"Unexpected pack schema_version={schema}")

    galaxies = _pack_galaxies(pack)
    galaxy_names = [str(g.get("name", "gal")) for g in galaxies]

    if int(args.kfold) < 2:
        raise ValueError("kfold must be >= 2")

    folds = _make_galaxy_folds(galaxy_names, kfold=int(args.kfold), seed=int(args.seed))

    # Deterministic grid for A_dm.
    if int(args.nA) <= 1:
        A_grid = np.array([float(args.A_min)], dtype=float)
    else:
        A_grid = np.linspace(float(args.A_min), float(args.A_max), int(args.nA), dtype=float)

    base_params = DMDynamicsC1Params()  # defaults except A_dm updated per scan
    base_params_dict = dict(vars(base_params))
    eval_cfg = EvalConfig(
        dt=float(args.dt),
        n_steps=int(args.n_steps),
        seed=int(args.seed),
        order_mode=str(args.order_mode),
        sigma_floor=float(args.sigma_floor),
    )

    # Index galaxies by name.
    by_name = {str(g.get("name", "gal")): g for g in galaxies}

    # Precompute per-galaxy chi2 across the entire A_grid once.
    # This makes CV folds fast while preserving train-only selection semantics.
    chi2_grid_by_gal: dict[str, np.ndarray] = {}
    ndof_by_gal: dict[str, int] = {}

    for name in galaxy_names:
        chi2s = np.zeros(int(A_grid.size), dtype=float)
        ndof0: int | None = None
        for j, A in enumerate(A_grid.tolist()):
            p = DMDynamicsC1Params(**{**base_params_dict, "A_dm": float(A)})
            c2, nd = _galaxy_chi2(by_name[name], p=p, cfg=eval_cfg)
            chi2s[int(j)] = float(c2)
            if ndof0 is None:
                ndof0 = int(nd)
        assert ndof0 is not None
        chi2_grid_by_gal[str(name)] = chi2s
        ndof_by_gal[str(name)] = int(ndof0)

    # Find the index corresponding to A=0 baseline (must exist in the grid).
    j0 = int(np.argmin(np.abs(A_grid - 0.0)))
    if not np.isclose(float(A_grid[j0]), 0.0, rtol=0.0, atol=1e-15):
        raise RuntimeError("A_grid must include A=0 baseline (use A_min=0)")

    if bool(args.sensitivity_check):
        A_probe = float(args.A_max) if args.A_probe is None else float(args.A_probe)
        j_probe = int(np.argmin(np.abs(A_grid - A_probe)))
        A_probe_snap = float(A_grid[j_probe])

        deltas = []
        for name in galaxy_names:
            c0 = float(chi2_grid_by_gal[name][j0])
            c1 = float(chi2_grid_by_gal[name][j_probe])
            deltas.append(c0 - c1)

        d = np.asarray(deltas, dtype=float)
        tiny = float(np.sum(np.abs(d) < 1e-9))

        print("DM-C2 sensitivity_check (fit-free)")
        print(f"A_grid: min={float(A_grid.min()):.6g} max={float(A_grid.max()):.6g} n={int(A_grid.size)}")
        print(f"A_probe requested: {A_probe:.6g}  snapped: {A_probe_snap:.6g}")
        print("Per-galaxy delta_chi2 = chi2(A=0) - chi2(A=A_probe)")
        print(f"delta_chi2 stats: min={float(np.min(d)):.6g} median={float(np.median(d)):.6g} max={float(np.max(d)):.6g}")
        print(f"near-zero count (|delta|<1e-9): {int(tiny)} / {int(d.size)}")
        print("")

    rows: list[dict[str, Any]] = []
    fold_details: list[dict[str, Any]] = []

    for fold_idx, test_gals in enumerate(folds):
        test_set = set(map(str, test_gals))
        train_gals = [g for g in galaxy_names if str(g) not in test_set]

        # Leak guard (disjointness)
        if set(train_gals) & test_set:
            raise RuntimeError("Leakage detected: train/test galaxies overlap")

        # Baseline on TRAIN
        chi2_train_base = float(sum(float(chi2_grid_by_gal[name][j0]) for name in train_gals))
        ndof_train = int(sum(int(ndof_by_gal[name]) for name in train_gals))

        # Train-only grid search
        chi2_train_by_A = np.zeros(int(A_grid.size), dtype=float)
        for name in train_gals:
            chi2_train_by_A += chi2_grid_by_gal[name]
        j_best = int(np.argmin(chi2_train_by_A))
        best_A = float(A_grid[j_best])
        best_chi2_train = float(chi2_train_by_A[j_best])

        # Evaluate baseline + best on TEST
        chi2_test_base = float(sum(float(chi2_grid_by_gal[name][j0]) for name in test_gals))
        chi2_test_best = float(sum(float(chi2_grid_by_gal[name][j_best]) for name in test_gals))
        ndof_test = int(sum(int(ndof_by_gal[name]) for name in test_gals))

        row = {
            "fold": int(fold_idx),
            "n_train_galaxies": int(len(train_gals)),
            "n_test_galaxies": int(len(test_gals)),
            "A_best": float(best_A),
            "chi2_train_base": float(chi2_train_base),
            "chi2_train_best": float(best_chi2_train),
            "delta_chi2_train": float(chi2_train_base - best_chi2_train),
            "chi2_test_base": float(chi2_test_base),
            "chi2_test_best": float(chi2_test_best),
            "delta_chi2_test": float(chi2_test_base - chi2_test_best),
            "ndof_train": int(ndof_train),
            "ndof_test": int(ndof_test),
            "dt": float(eval_cfg.dt),
            "n_steps": int(eval_cfg.n_steps),
            "order_mode": str(eval_cfg.order_mode),
            "sigma_floor": float(eval_cfg.sigma_floor),
        }
        rows.append(row)

        fold_details.append(
            {
                "fold": int(fold_idx),
                "test_galaxies": list(map(str, test_gals)),
                "train_galaxies": list(map(str, train_gals)),
                "A_best": float(best_A),
            }
        )

    df = pd.DataFrame(rows).sort_values(["fold"]).reset_index(drop=True)
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    dchi2 = df["delta_chi2_test"].astype(float).to_numpy()
    summary: dict[str, Any] = {
        "runner": {"name": "dm_holdout_cv_dynamics_c2", "path": str(Path(__file__).resolve())},
        "pack": {"path": str(pack_path), "schema_version": schema},
        "io": {"data_loaded_from_paths": True, "out_csv": str(out_csv), "out_json": str(Path(args.out_json))},
        "params": {
            "kfold": int(args.kfold),
            "seed": int(args.seed),
            "dt": float(args.dt),
            "n_steps": int(args.n_steps),
            "order_mode": str(args.order_mode),
            "sigma_floor": float(args.sigma_floor),
            "A_min": float(args.A_min),
            "A_max": float(args.A_max),
            "nA": int(args.nA),
        },
        "telemetry": {
            "folds_are_galaxy_holdout": True,
            "leakage_guard_disjoint_train_test": True,
            "train_only_calibration": True,
            "diagonal_sigma_v_used": True,
            "poison": {"DM_POISON_PROXY_CALLS": os.environ.get("DM_POISON_PROXY_CALLS")},
            "delta_chi2_test": {
                "min": float(np.min(dchi2)) if dchi2.size else None,
                "max": float(np.max(dchi2)) if dchi2.size else None,
            },
        },
        "fold_details": fold_details,
        "framing": {"stability_not_accuracy": True},
    }

    out_json = Path(args.out_json)
    _write_json(out_json, summary)

    print("DM-C2 CV runner OK")
    print("out_csv:", str(out_csv))
    print("out_json:", str(out_json))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
