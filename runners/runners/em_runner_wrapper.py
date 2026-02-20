#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EM runner wrapper (protocol container).
Locks: shape_only=ON, freeze_betas=ON, fixed holdout bands, fixed centering mode.
Exposes: panel/cov/holdout/case + Aeff_target (NOT raw A).
Outputs: pred.csv + unit_summary.json with a stable schema.
"""

from __future__ import annotations
import argparse, json, os, sys, hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import numpy as np
import pandas as pd


# -------------------------
# Protocol locks (hard)
# -------------------------
CENTER_MODE_LOCK = "pivot_cos"   # or "center_cos" only via protocol v2 (not CLI)
HOLDOUT_BANDS_LOCK = {
    "forward": (0.72, 0.91),
    "mid": (0.45, 0.72),
}

PROTOCOL_VERSION = "EM_RUN_CARD_v1"
RUNNER_VERSION = "em_runner_wrapper_v1"  # overwrite with git hash in outer manifest if you want


@dataclass(frozen=True)
class RunSpec:
    panel: str           # "bhabha" | "mumu"
    cov: str             # "total" | "diag_total"
    holdout: str         # "forward" | "mid" | "none"
    case: str            # "null" | "plus" | "minus"
    pack: str
    baseline: str
    outdir: str
    Aeff_target: float   # 0 for null, +/- Aeff* for plus/minus


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mask_from_holdout(cos_vals: np.ndarray, holdout: str) -> Tuple[np.ndarray, np.ndarray]:
    """Return (mask_train, mask_test)."""
    if holdout == "none":
        m = np.ones_like(cos_vals, dtype=bool)
        return m, np.zeros_like(cos_vals, dtype=bool)

    lo, hi = HOLDOUT_BANDS_LOCK[holdout]
    mask_test = (cos_vals >= lo) & (cos_vals < hi)
    mask_train = ~mask_test
    return mask_train, mask_test


# -------------------------
# Backend hook (fill this)
# -------------------------
def run_backend(
    *,
    panel: str,
    pack: str,
    baseline: str,
    cov: str,
    holdout: str,
    raw_A: float,
    shape_only: bool,
    freeze_betas: bool,
    center_mode: str,
) -> Dict[str, Any]:
    """
    MUST return a dict with keys:
      cos, y_base, y_sm, y_geo, delta, chi2_sm_train, chi2_geo_train, chi2_sm_test, chi2_geo_test,
      flags: positivity_ok, mapping_ok, cov_ok
    """
    raise NotImplementedError(
        "Implement run_backend() by calling your existing working EM scripts "
        "(import or subprocess). Keep output schema identical."
    )


def compute_m_stats(spec: RunSpec) -> Dict[str, float]:
    """
    One deterministic probe at raw_A=+1 to get m_rms and m_max, where delta = A * m.
    No scanning.
    """
    out = run_backend(
        panel=spec.panel,
        pack=spec.pack,
        baseline=spec.baseline,
        cov=spec.cov,
        holdout=spec.holdout,
        raw_A=1.0,
        shape_only=True,
        freeze_betas=True,
        center_mode=CENTER_MODE_LOCK,
    )
    delta = np.asarray(out["delta"], dtype=float)
    m_rms = float(np.sqrt(np.mean(delta ** 2)))
    m_max = float(np.max(np.abs(delta)))
    return {"m_rms": m_rms, "m_max": m_max}


def write_pred_csv(outdir: str, out: Dict[str, Any], mask_train: np.ndarray, mask_test: np.ndarray) -> None:
    df = pd.DataFrame({
        "cos": out["cos"],
        "y_base": out["y_base"],
        "y_sm": out["y_sm"],
        "y_geo": out["y_geo"],
        "delta": out["delta"],
        "mask_train": mask_train.astype(int),
        "mask_test": mask_test.astype(int),
    })
    df.to_csv(Path(outdir) / "pred.csv", index=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True, choices=["bhabha", "mumu"])
    ap.add_argument("--cov", required=True, choices=["total", "diag_total"])
    ap.add_argument("--holdout", required=True, choices=["forward", "mid", "none"])
    ap.add_argument("--case", required=True, choices=["null", "plus", "minus"])
    ap.add_argument("--pack", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--Aeff_target", required=True, type=float)

    args = ap.parse_args()

    spec = RunSpec(
        panel=args.panel, cov=args.cov, holdout=args.holdout, case=args.case,
        pack=args.pack, baseline=args.baseline, outdir=args.outdir,
        Aeff_target=float(args.Aeff_target),
    )

    Path(spec.outdir).mkdir(parents=True, exist_ok=True)

    # lock-checks (anti-overfit)
    shape_only = True
    freeze_betas = True
    center_mode = CENTER_MODE_LOCK

    # probe m stats to map Aeff_target -> raw_A (deterministic)
    if spec.case == "null" or abs(spec.Aeff_target) == 0.0:
        raw_A = 0.0
        mstats = {"m_rms": 0.0, "m_max": 0.0}
    else:
        mstats = compute_m_stats(spec)
        if mstats["m_rms"] <= 0:
            raise SystemExit("m_rms <= 0 in probe. Backend likely broken or delta all-zero.")
        raw_A = float(spec.Aeff_target / mstats["m_rms"])

    out = run_backend(
        panel=spec.panel, pack=spec.pack, baseline=spec.baseline, cov=spec.cov,
        holdout=spec.holdout, raw_A=raw_A,
        shape_only=shape_only, freeze_betas=freeze_betas, center_mode=center_mode,
    )

    cos = np.asarray(out["cos"], dtype=float)
    mask_train, mask_test = mask_from_holdout(cos, spec.holdout)

    # Derived summary scalars
    delta = np.asarray(out["delta"], dtype=float)
    Aeff = float(np.sqrt(np.mean(delta ** 2)))
    deltamax = float(np.max(np.abs(delta)))

    # Chi2 and DeltaChi2 in our convention: DeltaChi2_TEST = chi2_SM(TEST) - chi2_GEO(TEST)
    chi2_sm_test = float(out["chi2_sm_test"])
    chi2_geo_test = float(out["chi2_geo_test"])
    chi2_sm_train = float(out["chi2_sm_train"])
    chi2_geo_train = float(out["chi2_geo_train"])

    DeltaChi2_TEST = chi2_sm_test - chi2_geo_test
    DeltaChi2_TRAIN = chi2_sm_train - chi2_geo_train

    positivity_ok = bool(out["flags"]["positivity_ok"])
    mapping_ok = bool(out["flags"]["mapping_ok"])
    cov_ok = bool(out["flags"]["cov_ok"])

    # Write outputs
    write_pred_csv(spec.outdir, out, mask_train, mask_test)

    unit_summary = {
        "protocol_version": PROTOCOL_VERSION,
        "runner_version": RUNNER_VERSION,

        "panel": spec.panel,
        "cov": spec.cov,
        "holdout": spec.holdout,
        "case": spec.case,

        "Aeff_target": spec.Aeff_target,
        "raw_A_used": raw_A,
        "m_rms_probe": mstats.get("m_rms", None),
        "m_max_probe": mstats.get("m_max", None),

        "Aeff": Aeff,
        "deltamax": deltamax,

        "chi2_sm_train": chi2_sm_train,
        "chi2_geo_train": chi2_geo_train,
        "chi2_sm_test": chi2_sm_test,
        "chi2_geo_test": chi2_geo_test,

        "DeltaChi2_TRAIN": DeltaChi2_TRAIN,
        "DeltaChi2_TEST": DeltaChi2_TEST,

        "flags": {
            "positivity_ok": positivity_ok,
            "mapping_ok": mapping_ok,
            "cov_ok": cov_ok,
        },

        "inputs_sha256": {
            "pack": sha256_file(spec.pack) if os.path.exists(spec.pack) else None,
            "baseline": sha256_file(spec.baseline) if os.path.exists(spec.baseline) else None,
        },
    }

    with open(Path(spec.outdir) / "unit_summary.json", "w", encoding="utf-8") as f:
        json.dump(unit_summary, f, indent=2, ensure_ascii=False)

    print(f"PANEL={spec.panel} COV={spec.cov} HOLDOUT={spec.holdout} CASE={spec.case}")
    print(f"Aeff={Aeff:.8g} deltamax={deltamax:.8g}")
    print(f"TEST Delta chi2 = {DeltaChi2_TEST:.8g}")

    # fail-fast signal for caller (but still outputs files)
    if not (positivity_ok and mapping_ok and cov_ok):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
