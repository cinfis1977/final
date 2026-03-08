#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST Run4 trial builder from Alice/Bob ZIPs — DROP-IN v1

Why this exists
---------------
Your NIST *.build.hdf5 files contain settings + single-bit click timing bins, but do NOT contain
an explicit measurement outcome dataset (±1). Therefore CHSH "performance" is not well-defined
from those HDF5 exports.

The correct next step is to build a CHSH-ready trial table from the *raw* Alice/Bob ZIPs, which
typically include detector/outcome information (directly or via event records).

This script is designed to be robust to unknown ZIP internals:
- It can INSPECT zips and print candidate files/columns.
- If it finds parseable tables (CSV/TSV/TXT/NPY/NPZ/HDF5) with settings+outcome, it will build trials.
- If it cannot find outcome fields, it exits with an actionable report (no silent proxies).

Key output
----------
A CSV with (minimum):
  trial_idx, a_set, b_set, a_out, b_out
Optional:
  t_a, t_b, pulse, source file names, etc.

Usage (recommended)
-------------------
1) Inspect (no output trials yet):
   py -3 .\CODE\nist_run4_trial_builder_from_zip_v1_DROPIN.py ^
     --alice_zip ".\data\nist_raw_03_43\alice_03_43.zip" ^
     --bob_zip   ".\data\nist_raw_03_43\bob_03_43.zip" ^
     --inspect_only

2) Build trials (auto-detect):
   py -3 .\CODE\nist_run4_trial_builder_from_zip_v1_DROPIN.py ^
     --alice_zip ".\data\nist_raw_03_43\alice_03_43.zip" ^
     --bob_zip   ".\data\nist_raw_03_43\bob_03_43.zip" ^
     --out_csv   ".\out\nist_03_43_trials.csv"

If auto-detect is ambiguous, the script prints what it found and how to disambiguate using:
  --a_table, --b_table, --key_col, --a_set_col, --b_set_col, --a_out_col, --b_out_col, --t_a_col, --t_b_col

Design notes
------------
- NO proxy outcome assumptions are made. If outcome cannot be found, we STOP and report.
- "Settings" are expected to be binary (0/1) or 2-valued; we map deterministically to 0/1 if needed.
- Outcome is expected to be ±1 (or 0/1). If 0/1, we map 0->-1, 1->+1 by default.

Limitations
-----------
Some NIST raw zips may contain binary formats requiring a dedicated parser. If so, the inspect report
will show file names and sizes so we can write the correct parser next.

"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


TEXT_EXT = {".csv", ".tsv", ".txt"}
NP_EXT = {".npy", ".npz"}
H5_EXT = {".h5", ".hdf5"}
BIN_EXT = {".dat", ".bin", ".raw"}


def _ext(name: str) -> str:
    return os.path.splitext(name.lower())[1]


def _sniff_delim(sample: str) -> str:
    # crude delimiter sniff
    if sample.count(",") >= 2:
        return ","
    if sample.count("\t") >= 2:
        return "\t"
    if sample.count(";") >= 2:
        return ";"
    return ","


def _read_text_table(z: zipfile.ZipFile, member: str, nrows: int = 2000) -> Optional[pd.DataFrame]:
    with z.open(member, "r") as f:
        head = f.read(20000)
    try:
        s = head.decode("utf-8", errors="replace")
    except Exception:
        return None
    delim = _sniff_delim(s.splitlines()[0] if s.splitlines() else s)
    with z.open(member, "r") as f:
        try:
            df = pd.read_csv(f, sep=delim, engine="python", nrows=nrows)
            return df
        except Exception:
            return None


def _read_npy_npz(z: zipfile.ZipFile, member: str) -> Optional[Dict[str, np.ndarray]]:
    with z.open(member, "r") as f:
        data = f.read()
    bio = io.BytesIO(data)
    ext = _ext(member)
    try:
        if ext == ".npy":
            arr = np.load(bio, allow_pickle=False)
            return {"array": arr}
        if ext == ".npz":
            npz = np.load(bio, allow_pickle=False)
            return {k: npz[k] for k in npz.files}
    except Exception:
        return None
    return None


def _read_hdf5_member(z: zipfile.ZipFile, member: str, tmp_dir: str) -> Optional[str]:
    # h5py is happiest with a real path; extract single member to temp.
    try:
        import h5py  # type: ignore
    except Exception:
        return None
    os.makedirs(tmp_dir, exist_ok=True)
    out_path = os.path.join(tmp_dir, os.path.basename(member))
    with z.open(member, "r") as src, open(out_path, "wb") as dst:
        dst.write(src.read())
    # sanity open
    try:
        with h5py.File(out_path, "r"):
            pass
    except Exception:
        return None
    return out_path


def _score_columns(cols: List[str]) -> Dict[str, int]:
    score = {"key": 0, "set": 0, "out": 0, "time": 0}
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["trial", "pulse", "laser", "index", "event", "seq", "clock"]):
            score["key"] += 1
        if any(k in cl for k in ["setting", "basis", "set", "x", "s"]):
            score["set"] += 1
        if any(k in cl for k in ["outcome", "result", "meas", "out", "y", "det", "channel", "port"]):
            score["out"] += 1
        if any(k in cl for k in ["time", "timestamp", "ns", "ps", "t_"]):
            score["time"] += 1
    return score


@dataclass
class TableCandidate:
    member: str
    kind: str  # text/npy/npz/h5
    columns: List[str]
    score: Dict[str, int]


def _find_table_candidates(zip_path: str, side: str, preview_rows: int, tmp_dir: str) -> Tuple[List[TableCandidate], Dict[str, Dict]]:
    """
    Returns:
      - list of candidates (TableCandidate)
      - blobs: mapping member -> parsed lightweight preview payload
        for text: DataFrame head
        for npy/npz: dict of arrays shapes
        for h5: dict of dataset paths/shapes
    """
    cands: List[TableCandidate] = []
    blobs: Dict[str, Dict] = {}

    with zipfile.ZipFile(zip_path, "r") as z:
        members = [m for m in z.namelist() if not m.endswith("/")]

        for m in members:
            ext = _ext(m)
            if ext in TEXT_EXT:
                df = _read_text_table(z, m, nrows=preview_rows)
                if df is None or df.shape[1] < 2:
                    continue
                cols = [str(c) for c in df.columns]
                score = _score_columns(cols)
                cands.append(TableCandidate(m, "text", cols, score))
                blobs[m] = {"type": "text", "ncols": len(cols), "cols": cols[:50], "head": df.head(3).to_dict(orient="list")}
            elif ext in NP_EXT:
                dd = _read_npy_npz(z, m)
                if dd is None:
                    continue
                cols = list(dd.keys())
                score = _score_columns(cols)
                cands.append(TableCandidate(m, "np", cols, score))
                blobs[m] = {"type": "np", "arrays": {k: {"shape": list(np.asarray(v).shape), "dtype": str(np.asarray(v).dtype)} for k, v in dd.items()}}
            elif ext in H5_EXT:
                h5_path = _read_hdf5_member(z, m, tmp_dir=tmp_dir)
                if not h5_path:
                    continue
                try:
                    import h5py  # type: ignore
                    ds = []
                    with h5py.File(h5_path, "r") as f:
                        def visit(name, obj):
                            if hasattr(obj, "shape"):
                                ds.append((name, list(obj.shape), str(obj.dtype)))
                        f.visititems(visit)
                    # treat dataset names as "columns"
                    cols = [d[0] for d in ds]
                    score = _score_columns(cols)
                    cands.append(TableCandidate(m, "h5", cols, score))
                    blobs[m] = {"type": "h5", "extracted_path": h5_path, "datasets": ds[:200]}
                except Exception:
                    continue

    # sort by out+set+key presence
    cands.sort(key=lambda c: (c.score["out"], c.score["set"], c.score["key"], c.score["time"]), reverse=True)
    return cands, blobs


def _map_two_valued_to_01(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr)
    u = np.unique(arr)
    if len(u) == 2 and set(u.tolist()) == {0, 1}:
        return arr.astype(np.int8)
    if len(u) == 2:
        u_sorted = sorted(u.tolist())
        m = {u_sorted[0]: 0, u_sorted[1]: 1}
        return np.vectorize(lambda v: m[v])(arr).astype(np.int8)
    raise ValueError(f"Expected 2 unique values for setting, got {len(u)}: {u[:10]}")


def _map_outcome_to_pm1(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr)
    u = np.unique(arr)
    # already ±1
    if set(u.tolist()) <= {-1, 0, 1} and (-1 in u or 1 in u):
        # allow zeros, but treat as invalid later
        return arr.astype(np.int8)
    # binary 0/1
    if len(u) == 2 and set(u.tolist()) == {0, 1}:
        return (arr * 2 - 1).astype(np.int8)
    # binary 1/2
    if len(u) == 2 and set(u.tolist()) == {1, 2}:
        return ((arr - 1) * 2 - 1).astype(np.int8)
    raise ValueError(f"Outcome not recognizable as ±1 or 0/1 or 1/2. uniques={u[:10]} len={len(u)}")


def _load_full_text_table(zip_path: str, member: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path, "r") as z:
        with z.open(member, "r") as f:
            head = f.read(20000)
        s = head.decode("utf-8", errors="replace")
        delim = _sniff_delim(s.splitlines()[0] if s.splitlines() else s)
        with z.open(member, "r") as f:
            return pd.read_csv(f, sep=delim, engine="python")


def _choose_default_columns(cols: List[str], side: str) -> Dict[str, Optional[str]]:
    """
    Heuristic guesses for key/set/out/time column names.
    Returns dict with keys: key,set,out,time
    """
    cl = [c.lower() for c in cols]
    def pick(cands):
        for cand in cands:
            for i, name in enumerate(cl):
                if cand in name:
                    return cols[i]
        return None

    key = pick(["trial", "pulse", "laserpulse", "laser", "event", "index", "seq"])
    setc = pick(["setting", "basis", "set"])
    outc = pick(["outcome", "result", "meas", "out", "channel", "detector", "det", "port", "y"])
    timec = pick(["timestamp", "time", "t_"])
    return {"key": key, "set": setc, "out": outc, "time": timec}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alice_zip", required=True)
    ap.add_argument("--bob_zip", required=True)
    ap.add_argument("--out_csv", default="")
    ap.add_argument("--inspect_only", action="store_true")
    ap.add_argument("--preview_rows", type=int, default=2000)
    ap.add_argument("--tmp_dir", default=".\\out\\_zip_tmp")

    # overrides (if inspect shows ambiguity)
    ap.add_argument("--a_table", default="")
    ap.add_argument("--b_table", default="")
    ap.add_argument("--key_col", default="")
    ap.add_argument("--a_set_col", default="")
    ap.add_argument("--b_set_col", default="")
    ap.add_argument("--a_out_col", default="")
    ap.add_argument("--b_out_col", default="")
    ap.add_argument("--t_a_col", default="")
    ap.add_argument("--t_b_col", default="")
    args = ap.parse_args()

    a_cands, a_blobs = _find_table_candidates(args.alice_zip, "alice", args.preview_rows, tmp_dir=args.tmp_dir)
    b_cands, b_blobs = _find_table_candidates(args.bob_zip, "bob", args.preview_rows, tmp_dir=args.tmp_dir)

    def print_inspect():
        print("=== ZIP INSPECT ===")
        print("alice_zip:", args.alice_zip)
        for i, c in enumerate(a_cands[:10]):
            print(f"  [A{i}] {c.member}  kind={c.kind}  score={c.score}  ncols={len(c.columns)}")
        if not a_cands:
            print("  [A] No parseable tables found (csv/tsv/txt/npy/npz/h5).")
        print("bob_zip:", args.bob_zip)
        for i, c in enumerate(b_cands[:10]):
            print(f"  [B{i}] {c.member}  kind={c.kind}  score={c.score}  ncols={len(c.columns)}")
        if not b_cands:
            print("  [B] No parseable tables found (csv/tsv/txt/npy/npz/h5).")
        # show top candidate columns
        if a_cands:
            top = a_cands[0]
            print("\nTop Alice candidate columns (first 60):")
            print(top.columns[:60])
            print("Heuristic picks:", _choose_default_columns(top.columns, "alice"))
        if b_cands:
            top = b_cands[0]
            print("\nTop Bob candidate columns (first 60):")
            print(top.columns[:60])
            print("Heuristic picks:", _choose_default_columns(top.columns, "bob"))

    if args.inspect_only or not args.out_csv:
        print_inspect()
        if not args.out_csv:
            print("\nNOTE: --out_csv not provided, so not building trials.")
        return 0

    if not a_cands or not b_cands:
        print_inspect()
        raise SystemExit("No parseable tables found in one or both zips. Need a dedicated parser for the contained format.")

    a_member = args.a_table or a_cands[0].member
    b_member = args.b_table or b_cands[0].member

    # Load full tables (text only for v1)
    # If top candidate is not text, we stop and ask to extend parser.
    a_kind = next(c.kind for c in a_cands if c.member == a_member)
    b_kind = next(c.kind for c in b_cands if c.member == b_member)
    if a_kind != "text" or b_kind != "text":
        print_inspect()
        raise SystemExit("Top candidates are not text tables. v1 builder currently supports text tables only. We'll extend to np/h5 if needed.")

    A = _load_full_text_table(args.alice_zip, a_member)
    B = _load_full_text_table(args.bob_zip, b_member)

    # Choose columns
    a_guess = _choose_default_columns([str(c) for c in A.columns], "alice")
    b_guess = _choose_default_columns([str(c) for c in B.columns], "bob")

    key_col = args.key_col or a_guess["key"] or b_guess["key"]
    a_set_col = args.a_set_col or a_guess["set"]
    b_set_col = args.b_set_col or b_guess["set"]
    a_out_col = args.a_out_col or a_guess["out"]
    b_out_col = args.b_out_col or b_guess["out"]
    t_a_col = args.t_a_col or a_guess["time"]
    t_b_col = args.t_b_col or b_guess["time"]

    missing = [("key_col", key_col), ("a_set_col", a_set_col), ("b_set_col", b_set_col), ("a_out_col", a_out_col), ("b_out_col", b_out_col)]
    missing = [k for k, v in missing if not v]
    if missing:
        print_inspect()
        raise SystemExit(f"Could not auto-detect required columns: {missing}. Re-run with explicit --key_col/--*_col overrides.")

    if key_col not in A.columns or key_col not in B.columns:
        print_inspect()
        raise SystemExit(f"key_col '{key_col}' must exist in BOTH tables to join. Provide a common key column (trial/pulse/index).")

    # Build join
    A2 = A[[key_col, a_set_col, a_out_col] + ([t_a_col] if (t_a_col and t_a_col in A.columns) else [])].copy()
    B2 = B[[key_col, b_set_col, b_out_col] + ([t_b_col] if (t_b_col and t_b_col in B.columns) else [])].copy()

    A2 = A2.rename(columns={a_set_col: "a_set_raw", a_out_col: "a_out_raw"})
    B2 = B2.rename(columns={b_set_col: "b_set_raw", b_out_col: "b_out_raw"})

    M = A2.merge(B2, on=key_col, how="inner", suffixes=("_a", "_b"))
    if len(M) == 0:
        raise SystemExit("Join produced 0 rows. The chosen key_col does not align between Alice/Bob tables.")

    # Map settings/outcomes
    M["a_set"] = _map_two_valued_to_01(M["a_set_raw"].to_numpy())
    M["b_set"] = _map_two_valued_to_01(M["b_set_raw"].to_numpy())
    M["a_out"] = _map_outcome_to_pm1(M["a_out_raw"].to_numpy())
    M["b_out"] = _map_outcome_to_pm1(M["b_out_raw"].to_numpy())

    # Drop invalid outcomes (0)
    M = M[(M["a_out"] != 0) & (M["b_out"] != 0)].copy()
    M = M.sort_values(key_col)
    M["trial_idx"] = np.arange(len(M), dtype=np.int64)

    out_cols = ["trial_idx", key_col, "a_set", "b_set", "a_out", "b_out"]
    if t_a_col and t_a_col in A.columns and (t_a_col + "_a") in M.columns:
        out_cols.append(t_a_col + "_a")
    if t_b_col and t_b_col in B.columns and (t_b_col + "_b") in M.columns:
        out_cols.append(t_b_col + "_b")

    os.makedirs(os.path.dirname(os.path.abspath(args.out_csv)) or ".", exist_ok=True)
    M[out_cols].to_csv(args.out_csv, index=False)

    print("[OK] wrote:", args.out_csv)
    print("rows:", len(M))
    print("settings_counts:", M.groupby(["a_set", "b_set"]).size().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
