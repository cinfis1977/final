#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST build.hdf5 -> Clauser-Horne / Eberhard (CH) inequality runner — DROP-IN v1.1

Fix:
- settings arrays may be one-hot encoded as {1,2,3}:
    1 -> setting 0 bit
    2 -> setting 1 bit
    3 -> invalid (both bits set)
  This script auto-decodes and drops invalid trials.

J = N(++|ab) - N(+0|ab') - N(0+|a'b) - N(++|a'b')
Local realism: J <= 0. Violation: J > 0.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from typing import Dict, List, Tuple

import numpy as np

try:
    import h5py  # type: ignore
except Exception as e:
    raise SystemExit("h5py is required. Install: pip install h5py") from e


def parse_slots(spec: str) -> List[int]:
    spec = spec.strip()
    if not spec:
        raise ValueError("Empty --slots spec.")
    out: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            lo = int(a.strip())
            hi = int(b.strip())
            if hi < lo:
                lo, hi = hi, lo
            out.extend(range(lo, hi + 1))
        else:
            out.append(int(part))
    out = sorted(set(out))
    for s in out:
        if s < 1 or s > 16:
            raise ValueError(f"Slot out of range [1,16]: {s}")
    return out


def slots_to_bitmask(slots: List[int]) -> int:
    mask = 0
    for s in slots:
        mask |= 1 << (s - 1)
    return mask


def map_settings_to_01_auto(arr: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict[str, int]]:
    """
    Returns (setting01, valid_mask, stats)
    - If arr is {0,1} -> use directly.
    - If arr is {1,2,3} or subset -> one-hot decode:
        1 -> 0, 2 -> 1, else invalid
    - Otherwise: if exactly 2 unique values -> map sorted uniques -> 0/1
      else mark invalid (conservative).
    """
    a = np.asarray(arr).astype(np.int32, copy=False)
    u = np.unique(a)
    stats = {"n": int(a.size), "n_valid": 0, "n_invalid": 0, "mode": 0}

    # Case 1: already binary
    if set(u.tolist()) <= {0, 1}:
        valid = np.ones(a.shape[0], dtype=bool)
        out = a.astype(np.int8, copy=False)
        stats["n_valid"] = int(valid.sum())
        stats["mode"] = 1  # binary
        return out, valid, stats

    # Case 2: one-hot bits (common for NIST settings encoding)
    if set(u.tolist()) <= {0, 1, 2, 3} and (2 in u or 3 in u or 1 in u):
        out = np.full(a.shape[0], -1, dtype=np.int8)
        out[a == 1] = 0
        out[a == 2] = 1
        valid = out >= 0
        stats["n_valid"] = int(valid.sum())
        stats["n_invalid"] = int((~valid).sum())
        stats["mode"] = 2  # onehot
        return out, valid, stats

    # Case 3: two-valued but not {0,1}
    if len(u) == 2:
        u_sorted = sorted(u.tolist())
        m = {u_sorted[0]: 0, u_sorted[1]: 1}
        out = np.vectorize(lambda v: m[int(v)])(a).astype(np.int8)
        valid = np.ones(a.shape[0], dtype=bool)
        stats["n_valid"] = int(valid.sum())
        stats["mode"] = 3  # remap 2-valued
        return out, valid, stats

    # Conservative fallback: invalid
    out = np.full(a.shape[0], -1, dtype=np.int8)
    valid = np.zeros(a.shape[0], dtype=bool)
    stats["n_invalid"] = int(a.size)
    stats["mode"] = 9
    return out, valid, stats


def write_counts_csv(path: str, rows: List[Dict[str, object]]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5_path", required=True)
    ap.add_argument("--out_prefix", required=True)
    ap.add_argument("--slots", required=True)
    ap.add_argument("--chunk", type=int, default=2_000_000)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max_trials", type=int, default=0)
    ap.add_argument("--a_set_path", default="alice/settings")
    ap.add_argument("--b_set_path", default="bob/settings")
    ap.add_argument("--a_clicks_path", default="alice/clicks")
    ap.add_argument("--b_clicks_path", default="bob/clicks")
    args = ap.parse_args()

    slots = parse_slots(args.slots)
    bitmask = np.uint16(slots_to_bitmask(slots))

    out_summary = args.out_prefix + ".summary.json"
    out_counts = args.out_prefix + ".counts.csv"

    # CH terms
    n_pp_ab = 0
    n_p0_abp = 0
    n_0p_apb = 0
    n_pp_apbp = 0

    # diagnostics
    totals = {(0,0):0, (0,1):0, (1,0):0, (1,1):0}
    detA = {(0,0):0, (0,1):0, (1,0):0, (1,1):0}
    detB = {(0,0):0, (0,1):0, (1,0):0, (1,1):0}
    detAB = {(0,0):0, (0,1):0, (1,0):0, (1,1):0}

    processed = 0
    dropped_invalid_settings = 0
    a_set_mode_counts: Dict[int,int] = {}
    b_set_mode_counts: Dict[int,int] = {}

    with h5py.File(args.h5_path, "r") as h5:
        Aset = h5[args.a_set_path if args.a_set_path in h5 else "/" + args.a_set_path]
        Bset = h5[args.b_set_path if args.b_set_path in h5 else "/" + args.b_set_path]
        Aclk = h5[args.a_clicks_path if args.a_clicks_path in h5 else "/" + args.a_clicks_path]
        Bclk = h5[args.b_clicks_path if args.b_clicks_path in h5 else "/" + args.b_clicks_path]

        N = min(int(Aset.shape[0]), int(Bset.shape[0]), int(Aclk.shape[0]), int(Bclk.shape[0]))
        start = int(args.start)
        if start < 0 or start >= N:
            raise SystemExit(f"--start out of range: {start} (N={N})")
        end = N if args.max_trials == 0 else min(N, start + int(args.max_trials))

        for s in range(start, end, int(args.chunk)):
            e = min(end, s + int(args.chunk))

            a_raw = np.asarray(Aset[s:e], dtype=np.int32)
            b_raw = np.asarray(Bset[s:e], dtype=np.int32)

            a_set, a_valid, a_stats = map_settings_to_01_auto(a_raw)
            b_set, b_valid, b_stats = map_settings_to_01_auto(b_raw)

            a_set_mode_counts[a_stats["mode"]] = a_set_mode_counts.get(a_stats["mode"], 0) + 1
            b_set_mode_counts[b_stats["mode"]] = b_set_mode_counts.get(b_stats["mode"], 0) + 1

            valid = a_valid & b_valid
            if not np.all(valid):
                dropped_invalid_settings += int((~valid).sum())

            if valid.sum() == 0:
                processed += (e - s)
                continue

            # apply valid mask
            a_set = a_set[valid]
            b_set = b_set[valid]

            a_click = (np.asarray(Aclk[s:e], dtype=np.uint16) & bitmask) != 0
            b_click = (np.asarray(Bclk[s:e], dtype=np.uint16) & bitmask) != 0
            a_click = a_click[valid]
            b_click = b_click[valid]

            # per-setting diagnostics
            for aa in (0,1):
                for bb in (0,1):
                    m = (a_set == aa) & (b_set == bb)
                    if not m.any():
                        continue
                    key = (aa, bb)
                    totals[key] += int(m.sum())
                    detA[key] += int((m & a_click).sum())
                    detB[key] += int((m & b_click).sum())
                    detAB[key] += int((m & a_click & b_click).sum())

            # CH terms
            m_ab = (a_set == 0) & (b_set == 0)
            n_pp_ab += int((m_ab & a_click & b_click).sum())

            m_abp = (a_set == 0) & (b_set == 1)
            n_p0_abp += int((m_abp & a_click & (~b_click)).sum())

            m_apb = (a_set == 1) & (b_set == 0)
            n_0p_apb += int((m_apb & (~a_click) & b_click).sum())

            m_apbp = (a_set == 1) & (b_set == 1)
            n_pp_apbp += int((m_apbp & a_click & b_click).sum())

            processed += (e - s)

    J = int(n_pp_ab) - int(n_p0_abp) - int(n_0p_apb) - int(n_pp_apbp)

    counts_rows = []
    for (aa, bb) in [(0,0),(0,1),(1,0),(1,1)]:
        t = totals[(aa,bb)]
        ra = (detA[(aa,bb)] / t) if t else 0.0
        rb = (detB[(aa,bb)] / t) if t else 0.0
        rab = (detAB[(aa,bb)] / t) if t else 0.0
        counts_rows.append({
            "a_set": aa,
            "b_set": bb,
            "trials_valid": t,
            "alice_detect": detA[(aa,bb)],
            "bob_detect": detB[(aa,bb)],
            "both_detect": detAB[(aa,bb)],
            "rate_alice_detect": f"{ra:.8g}",
            "rate_bob_detect": f"{rb:.8g}",
            "rate_both_detect": f"{rab:.8g}",
        })

    summary = {
        "h5_path": args.h5_path,
        "slots": slots,
        "bitmask_hex": hex(int(bitmask)),
        "processed_trials_total_scanned": processed,
        "dropped_invalid_settings_trials": int(dropped_invalid_settings),
        "settings_decode_mode_counts_by_chunk": {
            "alice": a_set_mode_counts,
            "bob": b_set_mode_counts,
            "mode_meaning": {
                "1": "already binary {0,1}",
                "2": "onehot bits {1,2,3} decoded (1->0,2->1, else invalid)",
                "3": "2-valued remap",
                "9": "unknown -> invalid",
            }
        },
        "CH_terms": {
            "N_pp_ab": int(n_pp_ab),
            "N_p0_abp": int(n_p0_abp),
            "N_0p_apb": int(n_0p_apb),
            "N_pp_apbp": int(n_pp_apbp),
        },
        "J": int(J),
        "local_realism_bound": "J <= 0",
        "violation": bool(J > 0),
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_summary)) or ".", exist_ok=True)
    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    write_counts_csv(out_counts, counts_rows)

    print("=== NIST CH / EBERHARD RUNNER v1.1 ===")
    print("h5_path:", args.h5_path)
    print("slots:", slots, "bitmask:", hex(int(bitmask)))
    print("processed_trials_scanned:", processed)
    print("dropped_invalid_settings_trials:", int(dropped_invalid_settings))
    print("CH terms:")
    print("  N(++|ab)   =", int(n_pp_ab))
    print("  N(+0|ab')  =", int(n_p0_abp))
    print("  N(0+|a'b)  =", int(n_0p_apb))
    print("  N(++|a'b') =", int(n_pp_apbp))
    print("J =", int(J), " (bound J<=0; violation if J>0)")
    print("[WROTE]", out_summary)
    print("[WROTE]", out_counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())