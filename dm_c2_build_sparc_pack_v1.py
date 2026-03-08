#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a DM-C2 pack from repo-hosted SPARC points.

This produces a *real-data* pack for the DM-C1 dynamics runner.
It is a schema/IO deliverable and a smoke surface for the C2 stage.

Units
- r: kpc
- v_obs, sigma_v: km/s
- a_bary: (km/s)^2 / kpc

The runner computes v_pred = sqrt(r * (a_bary + a_dm)), therefore the above
unit convention keeps v_pred in km/s.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


_KPC_M = 3.085677581e19
_KM_M = 1000.0


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class BuildConfig:
    max_galaxies: int
    min_points: int
    seed: int


def _a_from_gbar_mps2_to_kms2_per_kpc(gbar_mps2: np.ndarray) -> np.ndarray:
    # Convert m/s^2 -> (km/s)^2/kpc
    # (km/s)^2/kpc = (m/s^2) * (kpc/m) / (km/m)^2
    return np.asarray(gbar_mps2, dtype=float) * (_KPC_M / (_KM_M**2))


def build_pack(points_csv: Path, *, cfg: BuildConfig) -> dict[str, Any]:
    df = pd.read_csv(points_csv)

    required = [
        "galaxy",
        "r_kpc",
        "v_obs_kms",
        "e_v_kms",
        "g_bar_mps2",
        "g_obs_mps2",
        "env_scale",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"SPARC points CSV missing columns: {missing}")

    df = df.copy()
    df["galaxy"] = df["galaxy"].astype(str)

    # Filter galaxies by point count (deterministic ordering by name).
    counts = df.groupby("galaxy").size().sort_index()
    keep = counts[counts >= int(cfg.min_points)].index.tolist()
    if not keep:
        raise RuntimeError("No galaxies meet min_points constraint")

    keep = keep[: int(cfg.max_galaxies)]
    df = df[df["galaxy"].isin(keep)].copy()

    galaxies: list[dict[str, Any]] = []

    for name in sorted(set(keep)):
        gdf = df[df["galaxy"] == name].copy()
        gdf = gdf.sort_values("r_kpc").reset_index(drop=True)

        r = gdf["r_kpc"].astype(float).to_numpy()
        v_obs = gdf["v_obs_kms"].astype(float).to_numpy()
        sigma_v = gdf["e_v_kms"].astype(float).to_numpy()

        g_bar = gdf["g_bar_mps2"].astype(float).to_numpy()
        g_obs = gdf["g_obs_mps2"].astype(float).to_numpy()
        a_bary = _a_from_gbar_mps2_to_kms2_per_kpc(g_bar)

        env_scale = float(gdf["env_scale"].astype(float).iloc[0])

        # Basic guards: finite and sigma positive.
        if not (np.all(np.isfinite(r)) and np.all(np.isfinite(v_obs)) and np.all(np.isfinite(sigma_v))):
            raise RuntimeError(f"Galaxy {name}: non-finite r/v/sigma in input")
        if not (np.all(np.isfinite(a_bary)) and np.all(np.isfinite(g_bar)) and np.all(np.isfinite(g_obs))):
            raise RuntimeError(f"Galaxy {name}: non-finite accelerations in input")

        sigma_v = np.maximum(sigma_v, 1e-6)

        galaxies.append(
            {
                "name": name,
                # Initial conditions used by the DM-C1 dynamics runner.
                "r0": float(r[0]),
                "v0": float(v_obs[0]),
                "theta0": 0.0,
                "omega0": 0.0,
                "epsilon0": 0.0,
                "g0": 0.5,
                "meta": {
                    "env_scale": env_scale,
                    "n_points": int(len(r)),
                },
                "obs": {
                    "r": [float(x) for x in r],
                    "v_obs": [float(x) for x in v_obs],
                    "sigma_v": [float(x) for x in sigma_v],
                    "a_bary": [float(x) for x in a_bary],
                    # extra fields for future C2+ work (not required by runner)
                    "g_obs_mps2": [float(x) for x in g_obs],
                    "g_bar_mps2": [float(x) for x in g_bar],
                },
            }
        )

    pack: dict[str, Any] = {
        "schema_version": "dm_c2_pack_v1",
        "source": {
            "dataset": "SPARC",
            "points_csv": str(points_csv),
            "generated_utc": _utc_now_iso(),
            "build": asdict(cfg),
            "units": {
                "r": "kpc",
                "v_obs": "km/s",
                "sigma_v": "km/s",
                "a_bary": "(km/s)^2/kpc",
                "g_obs_mps2": "m/s^2",
                "g_bar_mps2": "m/s^2",
            },
        },
        "galaxies": galaxies,
    }

    return pack


def main() -> int:
    ap = argparse.ArgumentParser(description="Build DM-C2 pack from SPARC points CSV")
    ap.add_argument(
        "--points_csv",
        default=str(_repo_root() / "data" / "sparc" / "sparc_points.csv"),
        help="Input points CSV (default: data/sparc/sparc_points.csv)",
    )
    ap.add_argument(
        "--out_json",
        default=str(_repo_root() / "integration_artifacts" / "mastereq" / "packs" / "dm_c2" / "dm_c2_sparc_pack_v1.json"),
        help="Output pack JSON path",
    )
    ap.add_argument("--max_galaxies", type=int, default=5)
    ap.add_argument("--min_points", type=int, default=8)
    ap.add_argument("--seed", type=int, default=2026)

    args = ap.parse_args()

    points_csv = Path(args.points_csv).resolve()
    out_json = Path(args.out_json)

    cfg = BuildConfig(max_galaxies=int(args.max_galaxies), min_points=int(args.min_points), seed=int(args.seed))

    pack = build_pack(points_csv, cfg=cfg)
    _write_json(out_json, pack)

    print("DM-C2 pack builder OK")
    print("points_csv:", str(points_csv))
    print("out_json:", str(out_json))
    print("n_galaxies:", len(pack.get("galaxies", [])))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
