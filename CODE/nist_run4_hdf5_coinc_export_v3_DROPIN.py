#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST Run4 HDF5 coincidence export — DROP-IN v3 (offset-join capable)

Purpose
-------
Build a coincidence table from NIST run4 *.build.hdf5 files that do NOT contain a precomputed
'coinc_idx' dataset. This avoids the "diagonal lock" symptom created by same-index exports.

HDF5 expected structure (example 03_43 run4):
  alice/settings  (N)
  alice/clicks    (N)
  bob/settings    (N)
  bob/clicks      (N)

Modes
-----
- both_clicked:
    coincidences are indices i where (alice_clicks[i] > 0) AND (bob_clicks[i] > 0)
    (often reproduces diagonal-lock if streams are effectively same-index paired)

- offset_join (recommended):
    build event index lists A={i|alice_clicks[i]>0}, B={j|bob_clicks[j]>0}
    estimate integer offset so that B ≈ A + offset, then match within ±window
    This is the minimal CHSH-ready pairing step when only click streams exist.

Output CSV columns
------------------
coinc_idx,a_set,b_set,a_out,b_out,a_clickmask,b_clickmask,a_slot,b_slot,a_i,b_i

Where:
- a_i, b_i are original time-slot indices in the HDF5 arrays (auditability).
- slot = least-significant set bit index of clickmask; -1 if clickmask==0
- out  = parity(slot): even -> +1, odd -> -1; slot<0 -> 0

Run (PowerShell recommended)
---------------------------
py -3 .\CODE\nist_run4_hdf5_coinc_export_v3_DROPIN.py `
  --h5_path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" `
  --out_csv ".\out\nist_run4_coincidences_offsetjoin.csv" `
  --coinc_mode offset_join `
  --window 2 `
  --offset_range 20000 `
  --sample_n 300000
"""
from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Tuple

import numpy as np

try:
    import h5py  # type: ignore
except Exception as e:
    raise SystemExit("h5py is required. Install: pip install h5py") from e

import pandas as pd


def _first_set_bit_slot(mask: np.ndarray) -> np.ndarray:
    """Least-significant set bit index. mask==0 -> -1."""
    mask = np.asarray(mask)
    out = np.full(mask.shape[0], -1, dtype=np.int32)
    if mask.dtype == object:
        for i, m in enumerate(mask):
            try:
                mv = int(m)
            except Exception:
                out[i] = -1
                continue
            if mv == 0:
                out[i] = -1
            else:
                out[i] = int((mv & -mv).bit_length() - 1)
        return out
    m = mask.astype(np.int64, copy=False)
    nz = m != 0
    lsb = (m[nz] & -m[nz]).astype(np.int64)
    out[nz] = np.floor(np.log2(lsb)).astype(np.int32)
    return out


def _outcome_from_slot(slot: np.ndarray) -> np.ndarray:
    """Parity mapping: odd -> -1, even -> +1; slot<0 -> 0."""
    slot = np.asarray(slot).astype(np.int32, copy=False)
    out = np.zeros(slot.shape[0], dtype=np.int8)
    m = slot >= 0
    out[m] = np.where((slot[m] % 2) == 1, -1, +1).astype(np.int8)
    return out


def _coerce_binary(x: np.ndarray, name: str) -> np.ndarray:
    x = np.asarray(x).astype(np.int32, copy=False)
    u = np.unique(x)
    if len(u) == 2 and set(u.tolist()) <= {0, 1}:
        return x
    if len(u) == 2:
        u_sorted = sorted(u.tolist())
        m = {u_sorted[0]: 0, u_sorted[1]: 1}
        return np.vectorize(lambda v: m[int(v)])(x).astype(np.int32)
    raise SystemExit(f"{name} not binary (need exactly 2 unique values). uniques={u[:10]} len={len(u)}")


def _audit(df: pd.DataFrame) -> Dict[str, Any]:
    g = df.groupby(["a_set", "b_set"])
    counts = g.size().sort_index().to_dict()
    eq_click = g.apply(lambda x: float((x.a_clickmask.values == x.b_clickmask.values).mean())).sort_index().to_dict()
    eq_slot = g.apply(lambda x: float((x.a_slot.values == x.b_slot.values).mean())).sort_index().to_dict()
    same_out = g.apply(lambda x: float((x.a_out.values == x.b_out.values).mean())).sort_index().to_dict()
    return {"counts": counts, "eq_clickmask_frac": eq_click, "eq_slot_frac": eq_slot, "same_outcome_frac": same_out}


def _event_indices_from_clicks(ds: "h5py.Dataset", chunk: int, N_scan: int) -> np.ndarray:
    """Return indices i where ds[i] > 0 using chunked scan."""
    idxs: List[np.ndarray] = []
    for start in range(0, N_scan, chunk):
        block = ds[start:start + chunk]
        loc = np.nonzero(np.asarray(block) > 0)[0]
        if loc.size:
            idxs.append(loc.astype(np.int64) + start)
    if not idxs:
        return np.zeros(0, dtype=np.int64)
    return np.concatenate(idxs)


def _estimate_offset(a_idx: np.ndarray, b_idx: np.ndarray, sample_n: int, offset_range: int, seed: int) -> int:
    """Estimate integer offset so that b ≈ a + offset using nearest-neighbor diffs histogram."""
    if a_idx.size == 0 or b_idx.size == 0:
        raise SystemExit("No events found on one side.")
    rng = np.random.default_rng(seed)
    if a_idx.size > sample_n:
        samp = rng.choice(a_idx, size=sample_n, replace=False)
        samp.sort()
    else:
        samp = a_idx

    pos = np.searchsorted(b_idx, samp)
    diffs: List[np.ndarray] = []
    m1 = pos < b_idx.size
    if m1.any():
        diffs.append((b_idx[pos[m1]] - samp[m1]).astype(np.int64))
    m0 = pos > 0
    if m0.any():
        diffs.append((b_idx[pos[m0] - 1] - samp[m0]).astype(np.int64))

    d = np.concatenate(diffs) if diffs else np.zeros(0, dtype=np.int64)
    d = d[(d >= -offset_range) & (d <= offset_range)]
    if d.size == 0:
        raise SystemExit("Offset estimation failed: no diffs within offset_range. Increase --offset_range.")
    bins = np.arange(-offset_range, offset_range + 2, 1, dtype=np.int64)
    hist, edges = np.histogram(d, bins=bins)
    k = int(np.argmax(hist))
    return int(edges[k])


def _match_with_offset(a_idx: np.ndarray, b_idx: np.ndarray, offset: int, window: int, max_pairs: int) -> Tuple[np.ndarray, np.ndarray]:
    """One-to-one two-pointer match: pairs where |(b - (a+offset))| <= window."""
    i = 0
    j = 0
    pa: List[int] = []
    pb: List[int] = []
    while i < a_idx.size and j < b_idx.size:
        target = int(a_idx[i]) + int(offset)
        d = int(b_idx[j]) - target
        if d < -window:
            j += 1
            continue
        if d > window:
            i += 1
            continue

        best_j = j
        best_abs = abs(d)
        jj = j + 1
        while jj < b_idx.size:
            dd = int(b_idx[jj]) - target
            if dd < -window:
                jj += 1
                continue
            if dd > window:
                break
            if abs(dd) < best_abs:
                best_abs = abs(dd)
                best_j = jj
            jj += 1

        pa.append(int(a_idx[i]))
        pb.append(int(b_idx[best_j]))
        i += 1
        j = best_j + 1

        if max_pairs > 0 and len(pa) >= max_pairs:
            break

    return np.asarray(pa, dtype=np.int64), np.asarray(pb, dtype=np.int64)


def _read_at_indices(ds: "h5py.Dataset", idx: np.ndarray) -> np.ndarray:
    """Read ds[idx] using sorted fancy indexing for better IO."""
    if idx.size == 0:
        return np.zeros(0, dtype=np.int64)
    order = np.argsort(idx)
    idxs = idx[order]
    vals = np.asarray(ds[idxs])
    inv = np.empty_like(order)
    inv[order] = np.arange(order.size)
    return vals[inv]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5_path", required=True)
    ap.add_argument("--out_csv", required=True)

    ap.add_argument("--a_set_path", default="alice/settings")
    ap.add_argument("--b_set_path", default="bob/settings")
    ap.add_argument("--a_clickmask_path", default="alice/clicks")
    ap.add_argument("--b_clickmask_path", default="bob/clicks")

    ap.add_argument("--coinc_mode", choices=["both_clicked", "offset_join"], default="offset_join")

    ap.add_argument("--chunk", type=int, default=2_000_000)
    ap.add_argument("--window", type=int, default=2)
    ap.add_argument("--offset", type=int, default=10**9)  # sentinel meaning "estimate"
    ap.add_argument("--offset_range", type=int, default=20000)
    ap.add_argument("--sample_n", type=int, default=300000)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--max_pairs", type=int, default=0)
    ap.add_argument("--max_slots_scan", type=int, default=0)

    args = ap.parse_args()

    with h5py.File(args.h5_path, "r") as h5:
        def get_ds(p: str):
            return h5[p] if p in h5 else h5["/" + p]

        a_set_ds = get_ds(args.a_set_path)
        b_set_ds = get_ds(args.b_set_path)
        a_clk_ds = get_ds(args.a_clickmask_path)
        b_clk_ds = get_ds(args.b_clickmask_path)

        N = int(a_set_ds.shape[0])
        if int(b_set_ds.shape[0]) != N or int(a_clk_ds.shape[0]) != N or int(b_clk_ds.shape[0]) != N:
            raise SystemExit("Dataset length mismatch between alice/bob arrays.")

        N_scan = int(args.max_slots_scan) if (args.max_slots_scan and args.max_slots_scan < N) else N

        if args.coinc_mode == "both_clicked":
            a_block = np.asarray(a_clk_ds[:N_scan]) > 0
            b_block = np.asarray(b_clk_ds[:N_scan]) > 0
            sel = np.nonzero(a_block & b_block)[0].astype(np.int64)
            a_i = sel
            b_i = sel
            print(f"[coinc_mode=both_clicked] {a_i.size} coincidences out of {N_scan} time slots ({(100.0*a_i.size/N_scan):.4f}%).")
        else:
            print("[scan] building event index lists from clicks (chunked)...")
            a_events = _event_indices_from_clicks(a_clk_ds, chunk=args.chunk, N_scan=N_scan)
            b_events = _event_indices_from_clicks(b_clk_ds, chunk=args.chunk, N_scan=N_scan)
            print(f"[events] alice={a_events.size}  bob={b_events.size}  (over {N_scan} slots)")

            if args.offset != 10**9:
                offset_used = int(args.offset)
                print(f"[offset] using user-provided offset={offset_used}")
            else:
                offset_used = _estimate_offset(a_events, b_events, sample_n=args.sample_n, offset_range=args.offset_range, seed=args.seed)
                print(f"[offset] estimated offset={offset_used} (slots) within ±{args.offset_range}")

            a_i, b_i = _match_with_offset(a_events, b_events, offset_used, window=args.window, max_pairs=args.max_pairs)
            print(f"[match] coincidences={a_i.size} (window=±{args.window})")

        # Read values at indices
        a_set = _read_at_indices(a_set_ds, a_i)
        b_set = _read_at_indices(b_set_ds, b_i)
        a_clickmask = _read_at_indices(a_clk_ds, a_i)
        b_clickmask = _read_at_indices(b_clk_ds, b_i)

    # Coerce + compute
    a_set = _coerce_binary(a_set, "a_set").astype(np.int8)
    b_set = _coerce_binary(b_set, "b_set").astype(np.int8)

    a_slot = _first_set_bit_slot(a_clickmask)
    b_slot = _first_set_bit_slot(b_clickmask)
    a_out = _outcome_from_slot(a_slot)
    b_out = _outcome_from_slot(b_slot)

    df = pd.DataFrame({
        "coinc_idx": np.arange(a_i.size, dtype=np.int64),
        "a_set": a_set,
        "b_set": b_set,
        "a_out": a_out.astype(np.int8),
        "b_out": b_out.astype(np.int8),
        "a_clickmask": a_clickmask,
        "b_clickmask": b_clickmask,
        "a_slot": a_slot,
        "b_slot": b_slot,
        "a_i": a_i,
        "b_i": b_i,
    })

    os.makedirs(os.path.dirname(os.path.abspath(args.out_csv)) or ".", exist_ok=True)
    df.to_csv(args.out_csv, index=False)

    aud = _audit(df)
    print("[OK] wrote:", args.out_csv)
    print("counts:", aud["counts"])
    print("eq_clickmask_frac:", aud["eq_clickmask_frac"])
    print("eq_slot_frac:", aud["eq_slot_frac"])
    print("same_outcome_frac:", aud["same_outcome_frac"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
