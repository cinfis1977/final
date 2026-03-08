#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preregistered pass/fail evaluator for NIST CH model scorecards — DROP-IN v1
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List


def _read_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scorecard_csv", required=True)
    ap.add_argument("--out_json", default=r".\out\nist_ch\PREREG_PASS_EVAL_V1.json")
    ap.add_argument("--out_md", default=r".\out\nist_ch\PREREG_PASS_EVAL_V1.md")
    ap.add_argument("--max_slot6_mae_per_1M", type=float, default=0.01)
    ap.add_argument("--max_wide_mae_per_1M", type=float, default=0.15)
    ap.add_argument("--max_wide_rmse_per_1M", type=float, default=0.20)
    ap.add_argument("--require_all_sign_ok", action='store_true')
    args = ap.parse_args()

    rows = _read_csv(Path(args.scorecard_csv))
    slot6 = [abs(float(r['delta_j_per_1M'])) for r in rows if r['window'] == 'slot6']
    wide = [abs(float(r['delta_j_per_1M'])) for r in rows if r['window'] != 'slot6']
    slot6_mae = mean(slot6) if slot6 else float('nan')
    wide_mae = mean(wide) if wide else float('nan')
    wide_rmse = math.sqrt(mean([float(r['delta_j_per_1M']) ** 2 for r in rows if r['window'] != 'slot6'])) if wide else float('nan')
    sign_ok_all = all(str(r.get('sign_ok', '')).upper() == 'YES' for r in rows)

    criteria = {
        'slot6_mae_ok': bool(slot6_mae <= float(args.max_slot6_mae_per_1M)),
        'wide_mae_ok': bool(wide_mae <= float(args.max_wide_mae_per_1M)),
        'wide_rmse_ok': bool(wide_rmse <= float(args.max_wide_rmse_per_1M)),
        'sign_ok_all': bool(sign_ok_all),
    }
    passed = criteria['slot6_mae_ok'] and criteria['wide_mae_ok'] and criteria['wide_rmse_ok'] and (criteria['sign_ok_all'] if args.require_all_sign_ok else True)
    out = {
        'scorecard_csv': str(args.scorecard_csv),
        'metrics': {
            'slot6_mae_per_1M': slot6_mae,
            'wide_mae_per_1M': wide_mae,
            'wide_rmse_per_1M': wide_rmse,
            'sign_ok_all': sign_ok_all,
        },
        'thresholds': {
            'max_slot6_mae_per_1M': float(args.max_slot6_mae_per_1M),
            'max_wide_mae_per_1M': float(args.max_wide_mae_per_1M),
            'max_wide_rmse_per_1M': float(args.max_wide_rmse_per_1M),
            'require_all_sign_ok': bool(args.require_all_sign_ok),
        },
        'criteria': criteria,
        'pass': bool(passed),
    }
    Path(args.out_json).write_text(json.dumps(out, indent=2), encoding='utf-8')
    md = [
        '# NIST CH preregistered pass evaluation',
        '',
        f"- pass: {'YES' if passed else 'NO'}",
        f"- slot6_mae_per_1M: {slot6_mae:.6g}",
        f"- wide_mae_per_1M: {wide_mae:.6g}",
        f"- wide_rmse_per_1M: {wide_rmse:.6g}",
        f"- sign_ok_all: {'YES' if sign_ok_all else 'NO'}",
    ]
    Path(args.out_md).write_text('\n'.join(md), encoding='utf-8')
    print('[OK] wrote:', str(args.out_json))
    print('[OK] wrote:', str(args.out_md))
    print('PASS' if passed else 'FAIL')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
