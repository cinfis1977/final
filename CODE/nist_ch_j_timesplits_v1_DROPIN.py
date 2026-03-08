#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
NIST CH/Eberhard (J) Bell-test helper - time splits, NO FIT

Computes the CH/Eberhard statistic:
  J = N(++|ab) - N(+0|ab') - N(0+|a'b) - N(++|a'b')
directly from NIST CH HDF5 build files, and also computes J over contiguous time-index splits.

This is a data-side computation (NO FIT). It is not a model-performance test and not a local-realism p-value proof.

Usage:
py -3 .\CODE\nist_ch_j_timesplits_v1_DROPIN.py ^
  --h5_path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" ^
  --slots "4-8" ^
  --n_splits 10 ^
  --out_prefix ".\out\nist_ch_splits\run03_43_slots4_8"
'''
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List
import numpy as np

try:
    import h5py  # type: ignore
except Exception as e:
    raise SystemExit("h5py is required for this script. Install with: pip install h5py") from e


def parse_slots(spec: str) -> List[int]:
    spec = spec.strip()
    if not spec:
        raise ValueError("Empty --slots spec")
    parts: List[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            a = int(a.strip()); b = int(b.strip())
            if a > b:
                a, b = b, a
            parts.extend(list(range(a, b + 1)))
        else:
            parts.append(int(chunk))
    slots = sorted(set(parts))
    for s in slots:
        if s < 1 or s > 16:
            raise ValueError(f"Slot out of range 1..16: {s}")
    return slots


def slots_to_bitmask(slots: List[int]) -> int:
    mask = 0
    for s in slots:
        mask |= (1 << (s - 1))
    return int(mask)


def map_two_valued_to_01(arr: np.ndarray) -> np.ndarray:
    u = np.unique(arr)
    if len(u) == 0:
        return arr
    if len(u) == 1:
        return np.zeros_like(arr, dtype=np.int8)
    if len(u) == 2:
        if set(u.tolist()) == {0, 1}:
            return arr.astype(np.int8, copy=False)
        lo, hi = sorted([int(u[0]), int(u[1])])
        out = np.empty_like(arr, dtype=np.int8)
        out[arr == lo] = 0
        out[arr == hi] = 1
        return out
    return arr


def compute_J_counts(a_set: np.ndarray, b_set: np.ndarray, a_plus: np.ndarray, b_plus: np.ndarray):
    a_set = a_set.astype(np.int8, copy=False)
    b_set = b_set.astype(np.int8, copy=False)
    valid = ((a_set == 0) | (a_set == 1)) & ((b_set == 0) | (b_set == 1))
    dropped = int(np.size(valid) - int(valid.sum()))
    if valid.any():
        a = a_set[valid]; b = b_set[valid]
        ap = a_plus[valid]; bp = b_plus[valid]
    else:
        a = b = ap = bp = a_set[:0]

    def sel(ai, bi):
        return (a == ai) & (b == bi)

    m_ab = sel(0, 0)
    n_pp_ab = int(np.sum(ap[m_ab] & bp[m_ab]))
    m_abp = sel(0, 1)
    n_p0_abp = int(np.sum(ap[m_abp] & (~bp[m_abp])))
    m_apb = sel(1, 0)
    n_0p_apb = int(np.sum((~ap[m_apb]) & bp[m_apb]))
    m_apbp = sel(1, 1)
    n_pp_apbp = int(np.sum(ap[m_apbp] & bp[m_apbp]))

    trials_valid = int(valid.sum())
    J = n_pp_ab - n_p0_abp - n_0p_apb - n_pp_apbp
    return J, trials_valid, dropped, {
        "N_pp_ab": n_pp_ab, "N_p0_abp": n_p0_abp, "N_0p_apb": n_0p_apb, "N_pp_apbp": n_pp_apbp
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="NIST CH/Eberhard J with time splits (NO FIT).")
    ap.add_argument("--h5_path", required=True)
    ap.add_argument("--slots", required=True)
    ap.add_argument("--n_splits", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=5_000_000)
    ap.add_argument("--out_prefix", required=True)
    args = ap.parse_args()

    slots = parse_slots(args.slots)
    bitmask = slots_to_bitmask(slots)
    n_splits = int(args.n_splits)
    if n_splits < 1:
        raise SystemExit("--n_splits must be >= 1")

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    h5_path = Path(args.h5_path)
    if not h5_path.exists():
        raise SystemExit(f"HDF5 not found: {h5_path}")

    split_counts = [
        {"N_pp_ab": 0, "N_p0_abp": 0, "N_0p_apb": 0, "N_pp_apbp": 0, "trials_valid": 0, "dropped_invalid": 0}
        for _ in range(n_splits)
    ]

    with h5py.File(str(h5_path), "r") as f:
        Aset = f["alice/settings"]; Bset = f["bob/settings"]
        Aclk = f["alice/clicks"];   Bclk = f["bob/clicks"]

        N = min(int(Aset.shape[0]), int(Bset.shape[0]), int(Aclk.shape[0]), int(Bclk.shape[0]))
        bounds = np.linspace(0, N, n_splits + 1, dtype=np.int64)

        CH = int(args.chunk)
        for s in range(0, N, CH):
            e = min(N, s + CH)
            a_set_raw = np.asarray(Aset[s:e], dtype=np.int32)
            b_set_raw = np.asarray(Bset[s:e], dtype=np.int32)
            a_clk = np.asarray(Aclk[s:e], dtype=np.uint16)
            b_clk = np.asarray(Bclk[s:e], dtype=np.uint16)

            a_set = map_two_valued_to_01(a_set_raw)
            b_set = map_two_valued_to_01(b_set_raw)
            a_plus = (a_clk & bitmask) != 0
            b_plus = (b_clk & bitmask) != 0

            idx = np.arange(s, e, dtype=np.int64)
            split_idx = np.searchsorted(bounds, idx, side="right") - 1
            split_idx = np.clip(split_idx, 0, n_splits - 1)

            for k in range(n_splits):
                m = (split_idx == k)
                if not m.any():
                    continue
                _, _, _, _ = 0,0,0,0
                J, tv, dropped, c = compute_J_counts(a_set[m], b_set[m], a_plus[m], b_plus[m])
                sc = split_counts[k]
                sc["N_pp_ab"] += c["N_pp_ab"]
                sc["N_p0_abp"] += c["N_p0_abp"]
                sc["N_0p_apb"] += c["N_0p_apb"]
                sc["N_pp_apbp"] += c["N_pp_apbp"]
                sc["trials_valid"] += tv
                sc["dropped_invalid"] += dropped

    rows = []
    bounds2 = np.linspace(0, N, n_splits + 1, dtype=np.int64)
    for k in range(n_splits):
        sc = split_counts[k]
        J = sc["N_pp_ab"] - sc["N_p0_abp"] - sc["N_0p_apb"] - sc["N_pp_apbp"]
        start_idx = int(bounds2[k]); end_idx = int(bounds2[k + 1])
        rows.append({
            "split": k, "start_idx": start_idx, "end_idx": end_idx,
            "trials_valid": sc["trials_valid"], "dropped_invalid": sc["dropped_invalid"],
            "N_pp_ab": sc["N_pp_ab"], "N_p0_abp": sc["N_p0_abp"],
            "N_0p_apb": sc["N_0p_apb"], "N_pp_apbp": sc["N_pp_apbp"],
            "J": J,
            "J_per_1M_valid": (J / sc["trials_valid"] * 1e6) if sc["trials_valid"] else float("nan"),
        })

    total = {k: sum(sc[k] for sc in split_counts) for k in split_counts[0].keys()}
    J_total = total["N_pp_ab"] - total["N_p0_abp"] - total["N_0p_apb"] - total["N_pp_apbp"]

    import csv
    csv_path = out_prefix.with_suffix(".splits.csv")
    with csv_path.open("w", newline="", encoding="utf-8") as fcsv:
        w = csv.DictWriter(fcsv, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    js_path = out_prefix.with_suffix(".summary.json")
    summary = {
        "h5_path": str(h5_path),
        "slots": slots,
        "bitmask_hex": hex(bitmask),
        "n_splits": n_splits,
        "overall": {
            "trials_valid": int(total["trials_valid"]),
            "dropped_invalid": int(total["dropped_invalid"]),
            "N_pp_ab": int(total["N_pp_ab"]),
            "N_p0_abp": int(total["N_p0_abp"]),
            "N_0p_apb": int(total["N_0p_apb"]),
            "N_pp_apbp": int(total["N_pp_apbp"]),
            "J": int(J_total),
            "J_per_1M_valid": (J_total / total["trials_valid"] * 1e6) if total["trials_valid"] else None,
        },
        "splits": rows,
        "notes": [
            "Data-side CH/Eberhard J computation (NO FIT).",
            "Not a model-performance test; not a local-realism p-value proof.",
            "Use splits to check sign stability over time index."
        ],
        "outputs": {"splits_csv": str(csv_path), "summary_json": str(js_path)}
    }
    js_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("[OK] wrote:", csv_path)
    print("[OK] wrote:", js_path)
    print("overall J:", int(J_total), "trials_valid:", int(total["trials_valid"]), "bitmask:", hex(bitmask))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
