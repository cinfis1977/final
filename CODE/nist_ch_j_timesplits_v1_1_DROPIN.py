#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH/Eberhard J Bell-test helper — time splits (NO FIT) — v1.1

v1.1 uses a deterministic *global* 2-code mapping per side (Alice, Bob) for settings:
- scan full uint8 settings array, pick the two most frequent codes
- map smaller->0, larger->1 (deterministic)
- all other codes are invalid and dropped

Computes:
  J = N(++|ab) - N(+0|ab') - N(0+|a'b) - N(++|a'b')

"+" means: (clickmask & slot_bitmask) != 0 within selected slots.

Outputs:
- <out_prefix>.splits.csv
- <out_prefix>.summary.json (includes settings mapping + invalid-code counts)

NO FIT: no parameter tuning.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

try:
    import h5py  # type: ignore
except Exception as e:
    raise SystemExit("h5py is required. Install with: pip install h5py") from e


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


def _bincount_u8(arr: np.ndarray) -> np.ndarray:
    return np.bincount(arr.astype(np.uint8, copy=False), minlength=256).astype(np.int64)


def compute_global_2code_mapping(ds, N: int, chunk: int, label: str) -> Tuple[int, int, Dict[int, int]]:
    counts = np.zeros(256, dtype=np.int64)
    for s in range(0, N, chunk):
        e = min(N, s + chunk)
        a = np.asarray(ds[s:e], dtype=np.uint8)
        counts += _bincount_u8(a)

    nonzero = np.where(counts > 0)[0].astype(int).tolist()
    if not nonzero:
        raise SystemExit(f"[{label}] settings array appears empty.")
    top = sorted(nonzero, key=lambda v: (-int(counts[v]), v))
    code_a = int(top[0])
    code_b = int(top[1]) if len(top) >= 2 else int(top[0])
    code0, code1 = (code_a, code_b) if code_a <= code_b else (code_b, code_a)
    counts_dict = {int(v): int(counts[v]) for v in nonzero}
    return code0, code1, counts_dict


def map_codes_to_01(arr_u8: np.ndarray, code0: int, code1: int) -> np.ndarray:
    out = np.full(arr_u8.shape, -1, dtype=np.int8)
    out[arr_u8 == np.uint8(code0)] = 0
    out[arr_u8 == np.uint8(code1)] = 1
    return out


def compute_J_counts(a_set01: np.ndarray, b_set01: np.ndarray, a_plus: np.ndarray, b_plus: np.ndarray):
    valid = (a_set01 >= 0) & (b_set01 >= 0)
    dropped = int(np.size(valid) - int(valid.sum()))
    if valid.any():
        a = a_set01[valid]; b = b_set01[valid]
        ap = a_plus[valid]; bp = b_plus[valid]
    else:
        a = b = ap = bp = a_set01[:0]

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
    ap = argparse.ArgumentParser(description="NIST CH/Eberhard J with time splits (NO FIT) — v1.1 global settings mapping.")
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

    CH = int(args.chunk)

    with h5py.File(str(h5_path), "r") as f:
        Aset = f["alice/settings"]; Bset = f["bob/settings"]
        Aclk = f["alice/clicks"];   Bclk = f["bob/clicks"]
        N = min(int(Aset.shape[0]), int(Bset.shape[0]), int(Aclk.shape[0]), int(Bclk.shape[0]))
        bounds = np.linspace(0, N, n_splits + 1, dtype=np.int64)

        a_code0, a_code1, a_counts = compute_global_2code_mapping(Aset, N, CH, "alice")
        b_code0, b_code1, b_counts = compute_global_2code_mapping(Bset, N, CH, "bob")

        split_counts = [
            {"N_pp_ab": 0, "N_p0_abp": 0, "N_0p_apb": 0, "N_pp_apbp": 0, "trials_valid": 0, "dropped_invalid": 0}
            for _ in range(n_splits)
        ]
        invalid_a = np.zeros(256, dtype=np.int64)
        invalid_b = np.zeros(256, dtype=np.int64)

        for s in range(0, N, CH):
            e = min(N, s + CH)
            a_set_u8 = np.asarray(Aset[s:e], dtype=np.uint8)
            b_set_u8 = np.asarray(Bset[s:e], dtype=np.uint8)
            a_clk = np.asarray(Aclk[s:e], dtype=np.uint16)
            b_clk = np.asarray(Bclk[s:e], dtype=np.uint16)

            a_set01 = map_codes_to_01(a_set_u8, a_code0, a_code1)
            b_set01 = map_codes_to_01(b_set_u8, b_code0, b_code1)

            ma = (a_set01 < 0); mb = (b_set01 < 0)
            if ma.any():
                invalid_a += _bincount_u8(a_set_u8[ma])
            if mb.any():
                invalid_b += _bincount_u8(b_set_u8[mb])

            a_plus = (a_clk & bitmask) != 0
            b_plus = (b_clk & bitmask) != 0

            idx = np.arange(s, e, dtype=np.int64)
            split_idx = np.searchsorted(bounds, idx, side="right") - 1
            split_idx = np.clip(split_idx, 0, n_splits - 1)

            for k in range(n_splits):
                m = (split_idx == k)
                if not m.any():
                    continue
                J, tv, dropped, c = compute_J_counts(a_set01[m], b_set01[m], a_plus[m], b_plus[m])
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
        rows.append({
            "split": k,
            "start_idx": int(bounds2[k]),
            "end_idx": int(bounds2[k + 1]),
            "trials_valid": int(sc["trials_valid"]),
            "dropped_invalid": int(sc["dropped_invalid"]),
            "N_pp_ab": int(sc["N_pp_ab"]),
            "N_p0_abp": int(sc["N_p0_abp"]),
            "N_0p_apb": int(sc["N_0p_apb"]),
            "N_pp_apbp": int(sc["N_pp_apbp"]),
            "J": int(J),
            "J_per_1M_valid": (J / sc["trials_valid"] * 1e6) if sc["trials_valid"] else float("nan"),
        })

    total = {k: sum(sc[k] for sc in split_counts) for k in split_counts[0].keys()}
    J_total = total["N_pp_ab"] - total["N_p0_abp"] - total["N_0p_apb"] - total["N_pp_apbp"]

    invalid_a_dict = {i: int(invalid_a[i]) for i in range(256) if int(invalid_a[i])}
    invalid_b_dict = {i: int(invalid_b[i]) for i in range(256) if int(invalid_b[i])}

    # write CSV
    import csv
    csv_path = out_prefix.with_suffix(".splits.csv")
    with csv_path.open("w", newline="", encoding="utf-8") as fcsv:
        w = csv.DictWriter(fcsv, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # write JSON
    js_path = out_prefix.with_suffix(".summary.json")
    summary = {
        "h5_path": str(h5_path),
        "slots": slots,
        "bitmask_hex": hex(bitmask),
        "n_splits": n_splits,
        "settings_mapping": {
            "alice": {"code0->0": a_code0, "code1->1": a_code1},
            "bob": {"code0->0": b_code0, "code1->1": b_code1},
        },
        "settings_code_counts": {"alice_nonzero": a_counts, "bob_nonzero": b_counts},
        "invalid_settings_code_counts": {"alice_invalid_nonzero": invalid_a_dict, "bob_invalid_nonzero": invalid_b_dict},
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
            "v1.1 uses global 2-code settings mapping per side (top-2 most frequent uint8 codes).",
            "Not a model-performance test; not a local-realism p-value proof.",
            "Use splits to check sign stability over time index."
        ],
        "outputs": {"splits_csv": str(csv_path), "summary_json": str(js_path)},
    }
    js_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("[OK] wrote:", csv_path)
    print("[OK] wrote:", js_path)
    print("overall J:", int(J_total), "trials_valid:", int(total["trials_valid"]), "dropped_invalid:", int(total["dropped_invalid"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
