#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATA_RECON provider (NOT A MODEL)

This provider reconstructs CH/Eberhard probabilities from empirical outputs:
  out/nist_ch/run{run_id}_{window}.summary.json
  out/nist_ch/run{run_id}_{window}.counts.csv

so that J_model == J_data (plumbing check only).

It is NOT model-faithful and must NOT be used as a performance evaluation.
"""
from __future__ import annotations
from typing import Dict, Any
import json, csv
from pathlib import Path

def _window_tag(slots):
    slots = sorted([int(x) for x in slots])
    if len(slots) == 1:
        return f"slot{slots[0]}"
    if slots == list(range(slots[0], slots[-1] + 1)):
        return f"slots{slots[0]}_{slots[-1]}"
    return "slots" + "_".join(str(s) for s in slots)

def _read_counts(counts_path: Path):
    per = {}
    aux = {}
    with counts_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            a = int(row["a_set"]); b = int(row["b_set"])
            k = f"{a}{b}"
            n = int(float(row.get("trials_valid", row.get("trials", "0"))))
            per[k] = n
            if "both_detect" in row:
                aux.setdefault("both_detect", {})[k] = int(float(row["both_detect"]))
            if "alice_detect" in row:
                aux.setdefault("alice_detect", {})[k] = int(float(row["alice_detect"]))
            if "bob_detect" in row:
                aux.setdefault("bob_detect", {})[k] = int(float(row["bob_detect"]))
    return per, aux

def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    run_id = run_ctx["run_id"]
    slots = run_ctx["slots"]
    tag = _window_tag(slots)

    base = Path(".") / "out" / "nist_ch"
    summary_path = base / f"run{run_id}_{tag}.summary.json"
    counts_path  = base / f"run{run_id}_{tag}.counts.csv"

    if not summary_path.exists():
        raise FileNotFoundError(f"missing summary: {summary_path}")
    if not counts_path.exists():
        raise FileNotFoundError(f"missing counts: {counts_path}")

    s = json.loads(summary_path.read_text(encoding="utf-8"))
    N, aux = _read_counts(counts_path)

    ch = s.get("CH_terms", {})
    N_pp_ab   = int(ch.get("N_pp_ab", 0))
    N_p0_abp  = int(ch.get("N_p0_abp", 0))
    N_0p_apb  = int(ch.get("N_0p_apb", 0))
    N_pp_apbp = int(ch.get("N_pp_apbp", 0))

    keys = ["00","01","10","11"]
    P_pp = {k: 0.0 for k in keys}
    P_p0 = {k: 0.0 for k in keys}
    P_0p = {k: 0.0 for k in keys}

    if "both_detect" in aux:
        for k in keys:
            den = N.get(k, 0)
            num = aux["both_detect"].get(k, 0)
            P_pp[k] = (num / den) if den > 0 else 0.0
    else:
        P_pp["00"] = (N_pp_ab / N["00"]) if N.get("00", 0) else 0.0
        P_pp["11"] = (N_pp_apbp / N["11"]) if N.get("11", 0) else 0.0

    P_p0["01"] = (N_p0_abp / N["01"]) if N.get("01", 0) else 0.0
    P_0p["10"] = (N_0p_apb / N["10"]) if N.get("10", 0) else 0.0

    return {
        "__provider_label__": "DATA_RECON (plumbing only, NOT model)",
        "P_pp": P_pp,
        "P_p0": P_p0,
        "P_0p": P_0p,
    }
