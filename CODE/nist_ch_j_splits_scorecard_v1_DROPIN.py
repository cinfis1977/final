\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH/Eberhard J time-splits scorecard — v1 DROP-IN (NO FIT)

Reads one or more `<out_prefix>.splits.csv` files produced by:
  - nist_ch_j_timesplits_v1_1_DROPIN.py  (recommended)
and summarizes:
  - overall J, trials_valid, dropped_invalid (from sibling .summary.json when available)
  - split sign counts and min/max ranges

Outputs:
  - --out_csv (required)
  - --out_md  (optional)

Usage (PowerShell):
py -3 .\CODE\nist_ch_j_splits_scorecard_v1_DROPIN.py `
  --in_glob ".\out\nist_ch_splits\*_v1_1.splits.csv" `
  --out_csv ".\out\nist_ch_splits\CH_J_SPLITS_SCORECARD.csv" `
  --out_md  ".\out\nist_ch_splits\CH_J_SPLITS_SCORECARD.md"
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _derive_run_id_from_name(name: str) -> str:
    # expected patterns: run03_43_slots4_8_v1_1.splits.csv, run01_11_slots4_8_v1_1.splits.csv
    # fallback: stem
    stem = Path(name).stem
    # remove trailing .splits if present
    stem = stem.replace(".splits", "")
    return stem


def summarize_one(splits_csv: Path) -> Dict[str, Any]:
    df = pd.read_csv(splits_csv)

    # Basic split stats
    n_splits = int(len(df))
    neg = int((df["J"] < 0).sum())
    pos = int((df["J"] > 0).sum())
    zero = int((df["J"] == 0).sum())
    j_min = int(df["J"].min())
    j_max = int(df["J"].max())
    j1_min = float(df["J_per_1M_valid"].min())
    j1_max = float(df["J_per_1M_valid"].max())

    # Optional: first-half vs second-half sums (diagnostic only)
    half = n_splits // 2
    j_first = int(df.loc[:half - 1, "J"].sum()) if half > 0 else int(df["J"].sum())
    j_second = int(df.loc[half:, "J"].sum()) if half > 0 else 0

    # Get overall from sibling summary.json if present
    summary_json = splits_csv.with_suffix(".summary.json")
    overall = None
    settings_mapping = None
    dropped_invalid = None
    trials_valid = None
    J_total = None
    J_per_1M = None
    h5_path = None
    slots = None
    bitmask_hex = None

    if summary_json.exists():
        js = _read_json(summary_json)
        overall = js.get("overall", {}) if isinstance(js, dict) else {}
        trials_valid = overall.get("trials_valid")
        dropped_invalid = overall.get("dropped_invalid")
        J_total = overall.get("J")
        J_per_1M = overall.get("J_per_1M_valid")
        settings_mapping = js.get("settings_mapping")
        h5_path = js.get("h5_path")
        slots = js.get("slots")
        bitmask_hex = js.get("bitmask_hex")
    else:
        # Fallback: reconstruct totals from splits.csv (counts)
        # This matches the J definition exactly.
        N_pp_ab = int(df["N_pp_ab"].sum())
        N_p0_abp = int(df["N_p0_abp"].sum())
        N_0p_apb = int(df["N_0p_apb"].sum())
        N_pp_apbp = int(df["N_pp_apbp"].sum())
        trials_valid = int(df["trials_valid"].sum())
        dropped_invalid = int(df["dropped_invalid"].sum())
        J_total = N_pp_ab - N_p0_abp - N_0p_apb - N_pp_apbp
        J_per_1M = (J_total / trials_valid * 1e6) if trials_valid else None

    return {
        "run": _derive_run_id_from_name(splits_csv.name),
        "splits_csv": str(splits_csv),
        "summary_json": str(summary_json) if summary_json.exists() else "",
        "h5_path": h5_path or "",
        "slots": ",".join(str(s) for s in slots) if isinstance(slots, list) else "",
        "bitmask_hex": bitmask_hex or "",
        "settings_mapping": json.dumps(settings_mapping, ensure_ascii=False) if settings_mapping else "",
        "trials_valid": int(trials_valid) if trials_valid is not None else "",
        "dropped_invalid": int(dropped_invalid) if dropped_invalid is not None else "",
        "J_overall": int(J_total) if J_total is not None else "",
        "J_per_1M_overall": _safe_float(J_per_1M),
        "n_splits": n_splits,
        "splits_pos": pos,
        "splits_neg": neg,
        "splits_zero": zero,
        "J_min_split": j_min,
        "J_max_split": j_max,
        "J_per_1M_min_split": j1_min,
        "J_per_1M_max_split": j1_max,
        "J_sum_first_half": j_first,
        "J_sum_second_half": j_second,
    }


def write_md(rows: List[Dict[str, Any]], out_md: Path) -> None:
    cols = [
        "run", "trials_valid", "dropped_invalid", "J_overall", "J_per_1M_overall",
        "n_splits", "splits_pos", "splits_neg", "splits_zero",
        "J_min_split", "J_max_split", "J_per_1M_min_split", "J_per_1M_max_split",
        "J_sum_first_half", "J_sum_second_half",
        "slots", "bitmask_hex",
    ]
    # Build markdown table
    lines = []
    lines.append("# NIST CH/Eberhard J — time-splits scorecard\n")
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for r in rows:
        def fmt(v):
            if v is None:
                return ""
            if isinstance(v, float):
                # compact
                return f"{v:.6g}"
            return str(v)
        lines.append("| " + " | ".join(fmt(r.get(c, "")) for c in cols) + " |")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize NIST CH/Eberhard J splits into one scorecard (NO FIT).")
    ap.add_argument("--in_glob", default="", help='Glob for splits.csv files, e.g. ".\\out\\nist_ch_splits\\*_v1_1.splits.csv"')
    ap.add_argument("--in_files", nargs="*", default=[], help="Explicit list of splits.csv files (overrides --in_glob if provided).")
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_md", default="")
    args = ap.parse_args()

    files: List[str] = []
    if args.in_files:
        files = list(args.in_files)
    else:
        if not args.in_glob:
            raise SystemExit("Provide --in_files or --in_glob")
        files = sorted(glob.glob(args.in_glob))

    if not files:
        raise SystemExit("No input files matched.")

    rows = [summarize_one(Path(p)) for p in files]

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("[OK] wrote:", out_csv)
    if args.out_md:
        out_md = Path(args.out_md)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        write_md(rows, out_md)
        print("[OK] wrote:", out_md)

    print("rows:", len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
