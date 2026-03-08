#!/usr/bin/env python

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from em_c1a_scattering_amplitude_core import evolve_A_over_scan


def _poison_if_baseline_calls_enabled() -> None:
    if os.environ.get("EM_C1A_POISON_BASELINE_CALLS", "0") == "1":
        raise RuntimeError("Baseline/overlay path is poison-enabled for EM-C1a")


def _baseline_overlay_sigma(*_args: Any, **_kwargs: Any) -> float:
    """Placeholder for legacy baseline/overlay path.

    EM-C1a must not use this. In tests we enable poison to guarantee anti-fallback.
    """

    _poison_if_baseline_calls_enabled()
    raise RuntimeError("Baseline/overlay sigma path is not implemented in EM-C1a")


@dataclass(frozen=True)
class ConstModel:
    value: float

    def __call__(self, _t: float) -> float:
        return float(self.value)


def _parse_scalar_model(model: dict[str, Any], *, name: str) -> Callable[[float], float]:
    kind = str(model.get("kind", "const")).lower()
    if kind == "const":
        return ConstModel(value=float(model.get("value", 0.0)))
    raise ValueError(f"Unsupported {name} model kind '{kind}'")


def _load_pack(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--dt_max", type=float, default=0.2)
    args = ap.parse_args()

    pack_path = Path(args.pack)
    pack = _load_pack(pack_path)

    scan = pack.get("scan")
    if not isinstance(scan, list) or len(scan) < 2:
        raise ValueError("pack.scan must be a list with at least 2 points")

    s_values: list[float] = []
    for pt in scan:
        if not isinstance(pt, dict):
            raise ValueError("pack.scan entries must be objects")
        if "s" in pt:
            s = float(pt["s"])
        elif "E_GeV" in pt:
            E = float(pt["E_GeV"])
            s = float(E * E)
        else:
            raise ValueError("pack.scan entries must contain 's' or 'E_GeV'")
        s_values.append(s)

    dyn = pack.get("dyn")
    if not isinstance(dyn, dict):
        raise ValueError("pack.dyn must be an object")

    s0 = float(dyn.get("s0", s_values[0]))
    A0_re = float(dyn.get("A0_re", 1.0))
    A0_im = float(dyn.get("A0_im", 0.0))
    A0 = complex(A0_re, A0_im)

    beta_model = dyn.get("beta")
    gamma_model = dyn.get("gamma")
    if not isinstance(beta_model, dict) or not isinstance(gamma_model, dict):
        raise ValueError("pack.dyn.beta and pack.dyn.gamma must be objects")

    beta_fn = _parse_scalar_model(beta_model, name="beta")
    gamma_fn = _parse_scalar_model(gamma_model, name="gamma")

    obs = pack.get("obs")
    if not isinstance(obs, dict):
        raise ValueError("pack.obs must be an object")
    sigma_norm = float(obs.get("sigma_norm", 1.0))

    data = pack.get("data")
    if not isinstance(data, list) or len(data) != len(s_values):
        raise ValueError("pack.data must be a list aligned with scan")

    sigma_data = np.array([float(d.get("sigma_data")) for d in data], dtype=float)
    sigma_err = np.array([float(d.get("sigma_err")) for d in data], dtype=float)
    if np.any(~np.isfinite(sigma_data)) or np.any(~np.isfinite(sigma_err)):
        raise ValueError("sigma_data/sigma_err must be finite")
    if np.any(sigma_err <= 0):
        raise ValueError("sigma_err must be positive")

    A_vals = evolve_A_over_scan(
        s_values,
        s0=s0,
        A0=A0,
        beta_fn=beta_fn,
        gamma_fn=gamma_fn,
        dt_max=float(args.dt_max),
    )

    sigma_pred = float(sigma_norm) * np.abs(A_vals) ** 2
    pull = (sigma_data - sigma_pred) / sigma_err

    if not np.all(np.isfinite(A_vals.real)) or not np.all(np.isfinite(A_vals.imag)):
        raise ValueError("Non-finite amplitude values")
    if not np.all(np.isfinite(sigma_pred)) or np.any(sigma_pred < -1e-12):
        raise ValueError("Non-finite or negative sigma_pred")
    if not np.all(np.isfinite(pull)):
        raise ValueError("Non-finite pulls")

    chi2 = float(np.sum(((sigma_data - sigma_pred) / sigma_err) ** 2))
    ndof = int(len(s_values))

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True) if out_csv.parent else None

    df = pd.DataFrame(
        {
            "s": np.asarray(s_values, dtype=float),
            "A_re": A_vals.real.astype(float),
            "A_im": A_vals.imag.astype(float),
            "sigma_pred": sigma_pred.astype(float),
            "sigma_data": sigma_data.astype(float),
            "sigma_err": sigma_err.astype(float),
            "pull": pull.astype(float),
        }
    )
    df.to_csv(out_csv, index=False)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True) if out_json.parent else None

    summary = {
        "runner": {"name": "em_scattering_pack_chi2_c1a", "path": str(Path(__file__).resolve())},
        "io": {"pack": str(pack_path.resolve()), "out_csv": str(out_csv.resolve()), "out_json": str(out_json.resolve())},
        "telemetry": {
            "amplitude_core_used": True,
            "baseline_used": False,
            "gw_coupling_used": False,
            "dt_max": float(args.dt_max),
            "n_points": int(len(s_values)),
        },
        "fit": {"chi2_total": float(chi2), "ndof": int(ndof)},
        "framing": {"stability_not_accuracy": True},
    }

    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    # Minimal, grep-friendly console line.
    print(f"[EM-C1a] chi2_total={chi2:.6g} ndof={ndof} out_csv={out_csv}")


if __name__ == "__main__":
    main()
