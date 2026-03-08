#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Write fixed NO-FIT params JSON for NOFIT_DETECTORHAZARD v2.

No run-specific seeding. Values are prereg knobs.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_json", default=r".\out\nist_ch\model_params_nofit_detectorhazard_v2.json")
    ap.add_argument("--visibility", type=float, default=0.9)
    ap.add_argument("--p_emit_1slot", type=float, default=0.02)
    ap.add_argument("--k_eta", type=float, default=10.0)
    ap.add_argument("--sA", type=float, default=0.5)
    ap.add_argument("--sB", type=float, default=0.5)
    args = ap.parse_args()

    out = Path(args.out_json)
    out.parent.mkdir(parents=True, exist_ok=True)

    params = {
        "defaults": {
            "visibility": float(args.visibility),
            "p_emit_1slot": float(args.p_emit_1slot),
            "k_eta": float(args.k_eta),
            "sA0": float(args.sA),
            "sA1": float(args.sA),
            "sB0": float(args.sB),
            "sB1": float(args.sB),
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
