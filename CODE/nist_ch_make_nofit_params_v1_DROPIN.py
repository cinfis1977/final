#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Write a NO-FIT params JSON for NOFIT_DETECTORHAZARD provider v1.

This is NOT a fit: values are fixed constants and can be treated as prereg knobs.
No run-specific values are derived from data.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_json", default=r".\out\nist_ch\model_params_nofit_detectorhazard_v1.json")
    ap.add_argument("--visibility", type=float, default=0.9)
    ap.add_argument("--k_single", type=float, default=0.002)
    ap.add_argument("--k_pair", type=float, default=0.02)
    ap.add_argument("--n_tdc_bins", type=int, default=16)
    args = ap.parse_args()

    out = Path(args.out_json)
    out.parent.mkdir(parents=True, exist_ok=True)

    params = {
        "defaults": {
            "visibility": float(args.visibility),
            "k_single": float(args.k_single),
            "k_pair": float(args.k_pair),
            "n_tdc_bins": int(args.n_tdc_bins),
            "a0_deg": 0.0,
            "a1_deg": 45.0,
            "b0_deg": 22.5,
            "b1_deg": -22.5
        },
        "runs": {}
    }
    out.write_text(json.dumps(params, indent=2), encoding="utf-8")
    print("[OK] wrote:", str(out))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
