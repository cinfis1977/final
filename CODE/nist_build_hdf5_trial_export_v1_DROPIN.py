#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST build.hdf5 -> small trial CSV export — DROP-IN v1

This is only for DEBUG / inspection.
Exporting all ~1e8 trials to CSV is enormous; this tool exports a window or a subsample.

Columns:
  trial_idx,a_set,b_set,a_clickmask,b_clickmask

Usage
-----
# export first 5 million trials (still big; use smaller for quick look)
py -3 .\CODE\nist_build_hdf5_trial_export_v1_DROPIN.py `
  --h5_path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  --out_csv ".\out\nist_ch\run03_43_trials_head1m.csv" `
  --start 0 --max_trials 1000000
"""
from __future__ import annotations
import argparse, csv, os
import numpy as np
try:
    import h5py  # type: ignore
except Exception as e:
    raise SystemExit("h5py is required. Install: pip install h5py") from e

def map_two_valued_to_01(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr)
    u = np.unique(arr)
    if len(u) == 2 and set(u.tolist()) == {0, 1}:
        return arr.astype(np.int8)
    if len(u) == 2:
        u_sorted = sorted(u.tolist())
        m = {u_sorted[0]: 0, u_sorted[1]: 1}
        return np.vectorize(lambda v: m[v])(arr).astype(np.int8)
    raise ValueError(f"Expected binary settings, got uniques={u[:10]} len={len(u)}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5_path", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--chunk", type=int, default=1_000_000)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max_trials", type=int, default=1_000_000)
    ap.add_argument("--a_set_path", default="alice/settings")
    ap.add_argument("--b_set_path", default="bob/settings")
    ap.add_argument("--a_clicks_path", default="alice/clicks")
    ap.add_argument("--b_clicks_path", default="bob/clicks")
    args = ap.parse_args()

    if args.max_trials <= 0:
        raise SystemExit("--max_trials must be >0 for this debug exporter.")

    os.makedirs(os.path.dirname(os.path.abspath(args.out_csv)) or ".", exist_ok=True)

    with h5py.File(args.h5_path, "r") as h5, open(args.out_csv, "w", encoding="utf-8", newline="") as f:
        Aset = h5[args.a_set_path if args.a_set_path in h5 else "/" + args.a_set_path]
        Bset = h5[args.b_set_path if args.b_set_path in h5 else "/" + args.b_set_path]
        Aclk = h5[args.a_clicks_path if args.a_clicks_path in h5 else "/" + args.a_clicks_path]
        Bclk = h5[args.b_clicks_path if args.b_clicks_path in h5 else "/" + args.b_clicks_path]
        N = min(int(Aset.shape[0]), int(Bset.shape[0]), int(Aclk.shape[0]), int(Bclk.shape[0]))

        start = int(args.start)
        end = min(N, start + int(args.max_trials))

        w = csv.writer(f)
        w.writerow(["trial_idx","a_set","b_set","a_clickmask","b_clickmask"])

        trial = start
        for s in range(start, end, int(args.chunk)):
            e = min(end, s + int(args.chunk))
            a_set = map_two_valued_to_01(np.asarray(Aset[s:e], dtype=np.int32))
            b_set = map_two_valued_to_01(np.asarray(Bset[s:e], dtype=np.int32))
            a_clk = np.asarray(Aclk[s:e], dtype=np.uint16)
            b_clk = np.asarray(Bclk[s:e], dtype=np.uint16)

            for i in range(e - s):
                w.writerow([trial, int(a_set[i]), int(b_set[i]), int(a_clk[i]), int(b_clk[i])])
                trial += 1

    print("[OK] wrote:", args.out_csv, "trials:", end-start)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
