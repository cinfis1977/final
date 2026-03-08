#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST Run4 HDF5 coincidence export (CHSH-ready attempt) — DROP-IN v2

Goal
----
Export a coincidence/trial table from a NIST run4 *.build.hdf5 WITHOUT the Bridge-E0 "diagonal lock"
symptom (a_clickmask≈b_clickmask≈, a_slot≈b_slot≈), so we can run model-faithful entanglement dynamics
on something closer to a real CHSH trial table.

Key ideas
---------
- The existing Bridge-E0 helper (as seen in grep logs) writes:
    coinc_idx, a_set, b_set, a_out, b_out, a_clickmask, b_clickmask, a_slot, b_slot
  and derives slot from *first set bit* of clickmask, then outcome by parity (odd→-1, even→+1).
  That path is fine as an audit helper, but if the exported clickmasks are effectively identical across sides,
  you get E≈1 for most settings and CHSH gets artificially inflated.

- This script tries to read the "real" per-side clickmask arrays (or Nx2 combined arrays) from HDF5.
  It does NOT force equality; it just exports what is inside the file.

Usage
-----
  py -3 .\CODE\nist_run4_hdf5_coinc_export_v2_DROPIN.py --h5_path ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5" --out_csv ".\out\nist_run4_coincidences_full.csv"

If auto-detection cannot uniquely identify datasets, the script prints candidates and exits.
Then re-run with explicit --coinc_idx_path / --settings_path / --clickmask_path.

Outputs
-------
- out_csv with columns:
    coinc_idx,a_set,b_set,a_out,b_out,a_clickmask,b_clickmask,a_slot,b_slot
  (optional: a_t,b_t if time paths supplied)

- Prints quick audit stats: setting counts, eq_clickmask_frac, eq_slot_frac, same_outcome_frac
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import h5py  # type: ignore
except Exception as e:
    raise SystemExit("h5py is required. Install: pip install h5py") from e

import pandas as pd


# --------------------------
# HDF5 discovery utilities
# --------------------------
@dataclass
class DSInfo:
    path: str
    shape: Tuple[int, ...]
    dtype: str

def _walk_datasets(h5: h5py.File) -> List[DSInfo]:
    out: List[DSInfo] = []
    def visitor(name, obj):
        if isinstance(obj, h5py.Dataset):
            try:
                shape = tuple(obj.shape)
            except Exception:
                shape = ()
            try:
                dtype = str(obj.dtype)
            except Exception:
                dtype = "unknown"
            out.append(DSInfo(path="/" + name, shape=shape, dtype=dtype))
    h5.visititems(visitor)
    return out

def _score_path(p: str, keywords: List[str]) -> int:
    pl = p.lower()
    s = 0
    for k in keywords:
        if k in pl:
            s += 10
    # mild preference for shorter paths
    s -= max(0, len(pl) - 40) // 10
    return s

def _pick_candidate(infos: List[DSInfo], keywords: List[str], shape_pred=None, dtype_pred=None, top_k: int = 8) -> List[DSInfo]:
    cands = []
    for inf in infos:
        if shape_pred is not None and not shape_pred(inf.shape):
            continue
        if dtype_pred is not None and not dtype_pred(inf.dtype):
            continue
        cands.append(( _score_path(inf.path, keywords), inf))
    cands.sort(key=lambda x: x[0], reverse=True)
    return [inf for score, inf in cands[:top_k] if score > 0]

def _read_dataset(h5: h5py.File, path: str) -> np.ndarray:
    if path not in h5:
        # allow without leading slash
        p2 = path if path.startswith("/") else "/" + path
        if p2 in h5:
            path = p2
        else:
            raise SystemExit(f"HDF5 path not found: {path}")
    arr = h5[path][...]
    return np.asarray(arr)

# --------------------------
# Mapping helpers
# --------------------------
def _coerce_binary(x: np.ndarray, name: str) -> np.ndarray:
    x = np.asarray(x).astype(int)
    u = np.unique(x)
    if len(u) == 2 and set(u.tolist()) <= {0, 1}:
        return x
    if len(u) == 2:
        # map top2 unique values to 0/1 deterministically
        u_sorted = sorted(u.tolist())
        m = {u_sorted[0]: 0, u_sorted[1]: 1}
        return np.vectorize(lambda v: m[int(v)])(x).astype(int)
    raise SystemExit(f"{name} is not binary (2 unique values). uniques={u[:10]} (len={len(u)})")

def _as_nx2(arr: np.ndarray, name: str) -> Tuple[np.ndarray, np.ndarray]:
    arr = np.asarray(arr)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise SystemExit(f"{name} expected Nx2, got shape {arr.shape}")
    return arr[:, 0], arr[:, 1]

def _bool_matrix_to_bitmask(mat: np.ndarray) -> np.ndarray:
    # mat: (N, M) bool -> bitmask int64 using bits 0..M-1
    mat = np.asarray(mat)
    if mat.ndim != 2:
        raise SystemExit(f"bool_matrix_to_bitmask expects 2D bool matrix; got shape {mat.shape}")
    N, M = mat.shape
    if M > 63:
        # still pack into python int via object dtype (slower), but safe
        out = np.zeros(N, dtype=object)
        for j in range(M):
            out += (mat[:, j].astype(object) << j)
        return out
    out = np.zeros(N, dtype=np.int64)
    for j in range(M):
        out |= (mat[:, j].astype(np.int64) << j)
    return out

def _first_set_bit_slot(mask: np.ndarray) -> np.ndarray:
    # Returns slot index of least-significant set bit. If mask==0 -> -1
    mask = np.asarray(mask)
    out = np.full(mask.shape[0], -1, dtype=int)
    for i, m in enumerate(mask):
        if m is None:
            out[i] = -1
            continue
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

def _outcome_from_slot(slot: np.ndarray, mode: str) -> np.ndarray:
    slot = np.asarray(slot).astype(int)
    out = np.full(slot.shape[0], 0, dtype=int)
    if mode == "parity":
        # match the Bridge-E0 helper behavior: odd -> -1, even -> +1; slot<0 -> 0 (invalid)
        m = slot >= 0
        out[m] = np.where((slot[m] % 2) == 1, -1, +1)
        out[~m] = 0
        return out
    raise SystemExit(f"Unsupported outcome_mode: {mode}")

# --------------------------
# Audit helpers
# --------------------------
def _audit(df: pd.DataFrame) -> Dict[str, Any]:
    g = df.groupby(["a_set", "b_set"])
    counts = g.size().sort_index().to_dict()
    eq_click = g.apply(lambda x: float((x.a_clickmask.values == x.b_clickmask.values).mean())).sort_index().to_dict()
    eq_slot = g.apply(lambda x: float((x.a_slot.values == x.b_slot.values).mean())).sort_index().to_dict()
    same_out = g.apply(lambda x: float((x.a_out.values == x.b_out.values).mean())).sort_index().to_dict()
    return {"counts": counts, "eq_clickmask_frac": eq_click, "eq_slot_frac": eq_slot, "same_outcome_frac": same_out}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5_path", required=True, help="Path to NIST run4 *.build.hdf5")
    ap.add_argument("--out_csv", required=True)

    # Optional explicit dataset paths (HDF5 internal paths)
    ap.add_argument("--coinc_idx_path", default="")
    ap.add_argument("--settings_path", default="", help="Either Nx2 combined settings, or separate paths via --a_set_path/--b_set_path")
    ap.add_argument("--a_set_path", default="")
    ap.add_argument("--b_set_path", default="")

    ap.add_argument("--clickmask_path", default="", help="Either Nx2 combined clickmask, or separate paths via --a_clickmask_path/--b_clickmask_path")
    ap.add_argument("--a_clickmask_path", default="")
    ap.add_argument("--b_clickmask_path", default="")

    ap.add_argument("--a_t_path", default="", help="Optional time array for side A (same length as coincidences)")
    ap.add_argument("--b_t_path", default="", help="Optional time array for side B (same length as coincidences)")

    ap.add_argument("--outcome_mode", default="parity", choices=["parity"])
    ap.add_argument("--print_candidates", action="store_true", help="Print top candidates for each field and exit")
    ap.add_argument("--coinc_mode", default="auto",
                    choices=["auto", "all", "both_clicked"],
                    help=(
                        "How to define coincidences when no coinc_idx dataset exists. "
                        "'auto': require a coinc_idx dataset (old behavior). "
                        "'all': treat every time slot as a coincidence (use row index). "
                        "'both_clicked': only rows where both alice and bob clicks > 0."
                    ))
    args = ap.parse_args()

    with h5py.File(args.h5_path, "r") as h5:
        infos = _walk_datasets(h5)

        # Heuristic candidate suggestions
        coinc_cands = _pick_candidate(
            infos,
            keywords=["coinc", "idx", "index"],
            shape_pred=lambda sh: (len(sh) == 1 and sh[0] > 1000),
            dtype_pred=lambda dt: ("int" in dt) or ("uint" in dt),
        )
        set_cands = _pick_candidate(
            infos,
            keywords=["set", "setting", "basis"],
            shape_pred=lambda sh: (len(sh) in (1, 2) and sh[0] > 1000),
            dtype_pred=lambda dt: ("int" in dt) or ("uint" in dt) or ("bool" in dt),
        )
        mask_cands = _pick_candidate(
            infos,
            keywords=["mask", "click", "det"],
            shape_pred=lambda sh: (len(sh) in (1, 2) and sh[0] > 1000),
            dtype_pred=lambda dt: ("int" in dt) or ("uint" in dt) or ("bool" in dt),
        )
        t_cands = _pick_candidate(
            infos,
            keywords=["time", "t", "timestamp"],
            shape_pred=lambda sh: (len(sh) == 1 and sh[0] > 1000),
            dtype_pred=lambda dt: ("float" in dt) or ("int" in dt) or ("uint" in dt),
        )

        if args.print_candidates:
            def show(title, cands):
                print(f"\n== {title} candidates ==")
                for inf in cands[:12]:
                    print(f"{inf.path:60s} shape={inf.shape} dtype={inf.dtype}")
            show("coinc_idx", coinc_cands)
            show("settings", set_cands)
            show("clickmask", mask_cands)
            show("time", t_cands)
            print("\nRe-run with explicit --*_path arguments.")
            return 0

        # Resolve coincidences idx
        coinc_filter: Optional[np.ndarray] = None  # boolean mask if coinc_mode filters rows
        if args.coinc_idx_path:
            coinc_idx = _read_dataset(h5, args.coinc_idx_path).astype(int).reshape(-1)
        elif coinc_cands:
            coinc_idx = _read_dataset(h5, coinc_cands[0].path).astype(int).reshape(-1)
        else:
            if args.coinc_mode == "auto":
                raise SystemExit(
                    "Could not find a plausible coincidence index dataset.\n"
                    "Re-run with --print_candidates to inspect the file, then either:\n"
                    "  --coinc_idx_path <hdf5_path>   (explicit dataset)\n"
                    "  --coinc_mode all               (use every time slot)\n"
                    "  --coinc_mode both_clicked       (only slots where both sides have clicks > 0)"
                )
            # Determine total length from settings or clicks
            # We need at least one of the side arrays to know N_total
            # Peek at alice/settings or alice/clicks for total size
            _peek_paths = ["/alice/settings", "/alice/clicks", "/bob/settings", "/bob/clicks"]
            N_total = None
            for _pp in _peek_paths:
                if _pp in h5:
                    N_total = h5[_pp].shape[0]
                    break
            if N_total is None:
                raise SystemExit("Cannot determine total row count. Pass --coinc_idx_path explicitly.")

            if args.coinc_mode == "all":
                coinc_idx = np.arange(N_total, dtype=np.int64)
                print(f"[coinc_mode=all] using all {N_total} time slots as coincidences.")
            elif args.coinc_mode == "both_clicked":
                # Need to load clicks first to build filter
                _a_clicks_path = "/alice/clicks" if "/alice/clicks" in h5 else None
                _b_clicks_path = "/bob/clicks" if "/bob/clicks" in h5 else None
                # fall back to heuristic mask candidates
                if _a_clicks_path is None or _b_clicks_path is None:
                    a_mc = [inf for inf in mask_cands if "alice" in inf.path.lower() or "a_" in inf.path.lower() or "/a/" in inf.path.lower()]
                    b_mc = [inf for inf in mask_cands if "bob" in inf.path.lower() or "b_" in inf.path.lower() or "/b/" in inf.path.lower()]
                    if a_mc:
                        _a_clicks_path = a_mc[0].path
                    if b_mc:
                        _b_clicks_path = b_mc[0].path
                if _a_clicks_path is None or _b_clicks_path is None:
                    raise SystemExit("coinc_mode=both_clicked: could not locate click arrays for both sides. Pass --a_clickmask_path and --b_clickmask_path.")
                _ac = np.asarray(h5[_a_clicks_path][...])
                _bc = np.asarray(h5[_b_clicks_path][...])
                coinc_filter = (_ac > 0) & (_bc > 0)
                coinc_idx = np.where(coinc_filter)[0].astype(np.int64)
                print(f"[coinc_mode=both_clicked] {len(coinc_idx)} coincidences out of {N_total} time slots "
                      f"({100*len(coinc_idx)/N_total:.2f}%).")
            else:
                raise SystemExit(f"Unknown coinc_mode: {args.coinc_mode}")

        N = int(coinc_idx.shape[0])

        # Resolve settings
        if args.a_set_path and args.b_set_path:
            a_set = _read_dataset(h5, args.a_set_path).reshape(-1)
            b_set = _read_dataset(h5, args.b_set_path).reshape(-1)
        elif args.settings_path:
            s = _read_dataset(h5, args.settings_path)
            a_set, b_set = _as_nx2(s, "settings")
        else:
            # best effort: pick top candidate; if Nx2 use it, else look for separate
            if not set_cands:
                raise SystemExit("Could not find settings dataset. Re-run with --print_candidates.")
            s = _read_dataset(h5, set_cands[0].path)
            if s.ndim == 2 and s.shape[1] == 2:
                a_set, b_set = _as_nx2(s, "settings")
            else:
                # try find explicit a/b by name
                a_named = [inf for inf in set_cands if "a_" in inf.path.lower() or "alice" in inf.path.lower()]
                b_named = [inf for inf in set_cands if "b_" in inf.path.lower() or "bob" in inf.path.lower()]
                if a_named and b_named:
                    a_set = _read_dataset(h5, a_named[0].path).reshape(-1)
                    b_set = _read_dataset(h5, b_named[0].path).reshape(-1)
                else:
                    raise SystemExit("Settings ambiguous. Re-run with --print_candidates and pass explicit paths.")

        # Index by coinc_idx (may be a subset filter, not just [:N])
        a_set = _coerce_binary(a_set.reshape(-1)[coinc_idx], "a_set")
        b_set = _coerce_binary(b_set.reshape(-1)[coinc_idx], "b_set")

        # Resolve clickmasks
        if args.a_clickmask_path and args.b_clickmask_path:
            am = _read_dataset(h5, args.a_clickmask_path)
            bm = _read_dataset(h5, args.b_clickmask_path)
        elif args.clickmask_path:
            m = _read_dataset(h5, args.clickmask_path)
            am, bm = _as_nx2(m, "clickmask")
        else:
            if not mask_cands:
                raise SystemExit("Could not find clickmask dataset. Re-run with --print_candidates.")
            m = _read_dataset(h5, mask_cands[0].path)
            if m.ndim == 2 and m.shape[1] == 2:
                am, bm = _as_nx2(m, "clickmask")
            else:
                # try named a/b datasets
                a_named = [inf for inf in mask_cands if "a_" in inf.path.lower() or "alice" in inf.path.lower()]
                b_named = [inf for inf in mask_cands if "b_" in inf.path.lower() or "bob" in inf.path.lower()]
                if a_named and b_named:
                    am = _read_dataset(h5, a_named[0].path)
                    bm = _read_dataset(h5, b_named[0].path)
                else:
                    raise SystemExit("Clickmask ambiguous. Re-run with --print_candidates and pass explicit paths.")

        # Coerce clickmask to integer bitmask if needed
        def to_bitmask(x: np.ndarray, name: str) -> np.ndarray:
            x = np.asarray(x)
            if x.dtype == np.bool_ and x.ndim == 2:
                return _bool_matrix_to_bitmask(x)
            if x.dtype == np.bool_ and x.ndim == 1:
                return x.astype(int)
            # int-like
            return x.reshape(-1)

        a_clickmask = to_bitmask(am, "a_clickmask")[coinc_idx]
        b_clickmask = to_bitmask(bm, "b_clickmask")[coinc_idx]

        # Optional times
        a_t = None
        b_t = None
        if args.a_t_path and args.b_t_path:
            a_t = _read_dataset(h5, args.a_t_path).reshape(-1)[coinc_idx]
            b_t = _read_dataset(h5, args.b_t_path).reshape(-1)[coinc_idx]

        # Slot/outcome (same convention as bridge helper, but now applied to the data as-is)
        a_slot = _first_set_bit_slot(a_clickmask)
        b_slot = _first_set_bit_slot(b_clickmask)
        a_out = _outcome_from_slot(a_slot, args.outcome_mode)
        b_out = _outcome_from_slot(b_slot, args.outcome_mode)

        # Build DF
        df = pd.DataFrame({
            "coinc_idx": coinc_idx,
            "a_set": a_set,
            "b_set": b_set,
            "a_out": a_out,
            "b_out": b_out,
            "a_clickmask": a_clickmask,
            "b_clickmask": b_clickmask,
            "a_slot": a_slot,
            "b_slot": b_slot,
        })
        if a_t is not None and b_t is not None:
            df["a_t"] = a_t
            df["b_t"] = b_t

        df.to_csv(args.out_csv, index=False)

    # quick audit
    aud = _audit(df)
    print("[OK] wrote:", args.out_csv)
    print("counts:", aud["counts"])
    print("eq_clickmask_frac:", aud["eq_clickmask_frac"])
    print("eq_slot_frac:", aud["eq_slot_frac"])
    print("same_outcome_frac:", aud["same_outcome_frac"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
