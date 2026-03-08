#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH/Eberhard scorecard aggregator — DROP-IN v1

What it does
------------
Scans an output directory (default: .\\out\\nist_ch) for:
  run*.summary.json
and the corresponding:
  run*.counts.csv

Builds a single scorecard table (CSV + Markdown) with:
- run id (e.g., 03_43, 01_11, 02_54)
- slots window, bitmask
- total trials scanned, valid trials (sum over counts.csv), dropped invalid settings trials
- CH terms and J
- J per 1M valid trials
- basic labels (training stub / tiny run)

Usage (PowerShell)
------------------
py -3 .\CODE\nist_ch_scorecard_v1_DROPIN.py `
  --in_dir ".\out\nist_ch" `
  --out_csv ".\out\nist_ch\CH_SCORECARD.csv" `
  --out_md  ".\out\nist_ch\CH_SCORECARD.md"

Notes
-----
- Robust to minor schema drift between summary versions.
- Uses counts.csv for N_valid (more meaningful than scanned count if invalid settings were dropped).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def _safe_get(d: Dict[str, Any], keys: List[str], default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default

def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _read_counts_csv(path: Path) -> Dict[str, Any]:
    """
    Returns:
      - total_valid_trials
      - per-setting trials_valid
      - per-setting detect rates (raw counts)
    """
    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    # Accept either trials_valid or trials fields
    total = 0
    per = {}
    for row in rows:
        a = int(row.get("a_set", row.get("a", 0)))
        b = int(row.get("b_set", row.get("b", 0)))
        tv = row.get("trials_valid", row.get("trials", row.get("n", "0")))
        tvi = int(float(tv)) if tv is not None else 0
        total += tvi
        per[(a,b)] = tvi
    return {"total_valid_trials": total, "per_setting_trials": per, "rows": rows}

def _extract_run_id(summary: Dict[str, Any], summary_path: Path) -> str:
    # Prefer run id from h5 file basename
    h5 = _safe_get(summary, ["h5_path", "io_h5_path", "hdf5_path"], "")
    base = os.path.basename(str(h5))
    m = re.search(r"(\d{2}_\d{2})", base)
    if m:
        return m.group(1)
    # fallback: from filename like run03_43_slot6.summary.json
    m = re.search(r"run(\d{2}_\d{2})", summary_path.name)
    if m:
        return m.group(1)
    # last resort
    return summary_path.stem

def _slots_spec(slots: List[int]) -> str:
    if not slots:
        return ""
    slots = sorted(slots)
    if len(slots) == 1:
        return f"{slots[0]}"
    # consecutive range?
    if slots == list(range(slots[0], slots[-1] + 1)):
        return f"{slots[0]}-{slots[-1]}"
    return ",".join(str(s) for s in slots)

def _window_label(slots: List[int]) -> str:
    if not slots:
        return "unknown"
    if len(slots) == 1:
        return f"slot{slots[0]}"
    return f"slots{_slots_spec(slots).replace(',','_')}"

def _is_training_stub(summary: Dict[str, Any]) -> bool:
    h5 = str(_safe_get(summary, ["h5_path"], ""))
    if "training" in h5.lower():
        return True
    n_scanned = int(_safe_get(summary, ["processed_trials_total_scanned", "processed_trials_scanned", "processed_trials"], 0) or 0)
    return n_scanned < 100000  # tiny => stub

def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    # basic markdown table (no external deps)
    def esc(s: str) -> str:
        return str(s).replace("\n", " ").replace("|", "\\|")
    widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(esc(c)))
    line_h = "| " + " | ".join(esc(headers[i]).ljust(widths[i]) for i in range(len(headers))) + " |"
    line_sep = "| " + " | ".join(("-" * widths[i]) for i in range(len(headers))) + " |"
    lines = [line_h, line_sep]
    for r in rows:
        lines.append("| " + " | ".join(esc(r[i]).ljust(widths[i]) for i in range(len(headers))) + " |")
    return "\n".join(lines)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch", help="Directory containing run*.summary.json and run*.counts.csv")
    ap.add_argument("--glob", default="run*.summary.json")
    ap.add_argument("--out_csv", default=r".\out\nist_ch\CH_SCORECARD.csv")
    ap.add_argument("--out_md", default=r".\out\nist_ch\CH_SCORECARD.md")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    if not in_dir.exists():
        raise SystemExit(f"in_dir not found: {in_dir}")

    summary_paths = sorted(in_dir.glob(args.glob))
    if not summary_paths:
        raise SystemExit(f"No summaries found matching {args.glob} in {in_dir}")

    records: List[Dict[str, Any]] = []
    warnings: List[str] = []

    for sp in summary_paths:
        summary = _read_json(sp)

        # find matching counts.csv by prefix: replace .summary.json with .counts.csv
        counts_path = sp.with_name(sp.name.replace(".summary.json", ".counts.csv"))
        if not counts_path.exists():
            warnings.append(f"missing counts.csv for {sp.name}")
            counts_info = {"total_valid_trials": 0, "per_setting_trials": {}}
        else:
            counts_info = _read_counts_csv(counts_path)

        run_id = _extract_run_id(summary, sp)
        slots = _safe_get(summary, ["slots"], [])
        bitmask_hex = _safe_get(summary, ["bitmask_hex"], "")
        n_scanned = int(_safe_get(summary, ["processed_trials_total_scanned", "processed_trials_scanned", "processed_trials"], 0) or 0)
        dropped = int(_safe_get(summary, ["dropped_invalid_settings_trials"], 0) or 0)
        ch = _safe_get(summary, ["CH_terms", "ch_terms"], {}) or {}
        N_pp_ab   = int(_safe_get(ch, ["N_pp_ab"], 0) or 0)
        N_p0_abp  = int(_safe_get(ch, ["N_p0_abp"], 0) or 0)
        N_0p_apb  = int(_safe_get(ch, ["N_0p_apb"], 0) or 0)
        N_pp_apbp = int(_safe_get(ch, ["N_pp_apbp"], 0) or 0)
        J = int(_safe_get(summary, ["J"], 0) or 0)

        n_valid = int(counts_info["total_valid_trials"])
        j_per_1m = (float(J) * 1e6 / n_valid) if n_valid > 0 else 0.0

        is_train = _is_training_stub(summary)

        records.append({
            "run_id": run_id,
            "window": _window_label(slots),
            "slots": _slots_spec(slots),
            "bitmask_hex": bitmask_hex,
            "trials_scanned": n_scanned,
            "trials_valid": n_valid,
            "dropped_invalid_settings": dropped,
            "N_pp_ab": N_pp_ab,
            "N_p0_abp": N_p0_abp,
            "N_0p_apb": N_0p_apb,
            "N_pp_apbp": N_pp_apbp,
            "J": J,
            "J_per_1M": f"{j_per_1m:.6g}",
            "violation": "YES" if J > 0 else "NO",
            "label": "training_stub" if is_train else "real_run",
            "summary_file": str(sp),
            "counts_file": str(counts_path) if counts_path.exists() else "",
        })

    # Sort: run_id then window size (slot6 < slots5-7 < slots4-8)
    def win_key(w: str) -> int:
        # slot6 => 1, slots5-7 => 3, slots4-8 => 5 (fallback 99)
        m = re.match(r"slot(\d+)$", w)
        if m:
            return 1
        m = re.match(r"slots(\d+)-(\d+)$", w.replace("_", "-"))
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            return hi - lo + 1
        # other patterns
        return 99

    records.sort(key=lambda r: (r["run_id"], win_key(r["window"]), r["window"]))

    out_csv = Path(args.out_csv)
    out_md = Path(args.out_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    fieldnames = list(records[0].keys())
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in records:
            w.writerow(r)

    # Write MD
    headers = [
        "run_id","label","window","slots","bitmask_hex","trials_valid","J","J_per_1M",
        "N_pp_ab","N_p0_abp","N_0p_apb","N_pp_apbp","dropped_invalid_settings"
    ]
    md_rows = [[str(rec[h]) for h in headers] for rec in records]
    md = []
    md.append("# NIST CH/Eberhard scorecard")
    md.append("")
    md.append(_md_table(headers, md_rows))
    md.append("")
    md.append("## Notes")
    md.append("- `J = N(++|ab) - N(+0|ab') - N(0+|a'b) - N(++|a'b')`; local realism bound is `J <= 0` (violation if `J > 0`).")
    md.append("- `trials_valid` is the sum of per-setting valid trials from `*.counts.csv` (preferred over scanned count).")
    if warnings:
        md.append("")
        md.append("## Warnings")
        for wmsg in warnings:
            md.append(f"- {wmsg}")
    out_md.write_text("\n".join(md), encoding="utf-8")

    print("[OK] wrote:", str(out_csv))
    print("[OK] wrote:", str(out_md))
    print("rows:", len(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
