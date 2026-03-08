#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH/Eberhard MODEL scorecard — DROP-IN v1

What it does
------------
1) Reads empirical CH outputs from:
   - run*.summary.json
   - run*.counts.csv
   in a directory (default: .\\out\\nist_ch)

2) Calls a user-supplied model probability provider:
   - ch_model_prob_provider_v1_TEMPLATE.py : compute_probabilities(run_ctx)

3) Computes:
   - J_data (from summary.json)
   - J_model (from probabilities + valid trial counts)
   - per-window trend checks
   - absolute / per-1M differences

4) Writes:
   - MODEL_SCORECARD.csv
   - MODEL_SCORECARD.md

Usage
-----
(1) First generate empirical summaries with nist_build_hdf5_ch_eberhard_runner_v1_DROPIN.py (done).

(2) Implement model probabilities:
    Copy `CODE/ch_model_prob_provider_v1_TEMPLATE.py` to `CODE/ch_model_prob_provider_v1.py`
    and implement `compute_probabilities(run_ctx)`.

(3) Run:
py -3 .\CODE\nist_ch_model_scorecard_v1_DROPIN.py `
  --in_dir ".\out\nist_ch" `
  --provider ".\CODE\ch_model_prob_provider_v1.py" `
  --out_csv ".\out\nist_ch\MODEL_SCORECARD.csv" `
  --out_md  ".\out\nist_ch\MODEL_SCORECARD.md" `
  --params_json ".\out\nist_ch\model_params.json"

Params file (optional)
----------------------
JSON with keys:
- "defaults": {...}
- "runs": {"03_43": {...}, "01_11": {...}, ...}

The dict is passed verbatim as run_ctx["params"].

Toy mode
--------
If you want to sanity-run the pipeline before implementing your model, pass --toy_ok.
This will use a trivial probability provider (clearly labeled TOY) that is NOT model-faithful.

"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_counts_csv(path: Path) -> Dict[str, Any]:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    total = 0
    per = {}
    for row in rows:
        a = int(row.get("a_set", row.get("a", 0)))
        b = int(row.get("b_set", row.get("b", 0)))
        tv = row.get("trials_valid", row.get("trials", row.get("n", "0")))
        tvi = int(float(tv)) if tv is not None else 0
        total += tvi
        per[f"{a}{b}"] = tvi
    return {"total_valid_trials": total, "per_setting_trials": per, "rows": rows}


def _extract_run_id(summary: Dict[str, Any], summary_path: Path) -> str:
    h5 = str(summary.get("h5_path", ""))
    base = os.path.basename(h5)
    m = re.search(r"(\d{2}_\d{2})", base)
    if m:
        return m.group(1)
    m = re.search(r"run(\d{2}_\d{2})", summary_path.name)
    if m:
        return m.group(1)
    return summary_path.stem


def _slots_spec(slots: List[int]) -> str:
    if not slots:
        return ""
    slots = sorted(slots)
    if len(slots) == 1:
        return f"{slots[0]}"
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
    h5 = str(summary.get("h5_path", ""))
    if "training" in h5.lower():
        return True
    n_scanned = int(summary.get("processed_trials_total_scanned", summary.get("processed_trials_scanned", 0)) or 0)
    return n_scanned < 100000


def _load_provider(provider_path: Path):
    spec = importlib.util.spec_from_file_location("ch_model_prob_provider", str(provider_path))
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load provider: {provider_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    if not hasattr(mod, "compute_probabilities"):
        raise SystemExit("Provider must define compute_probabilities(run_ctx).")
    return mod.compute_probabilities


def _clip01(x: float) -> float:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return float(x)


def _toy_provider(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    # Clear label: this is NOT model-faithful.
    # Produces small window-dependent correlated detection.
    slots = run_ctx["slots"]
    w = len(slots)
    # base rates
    pA = min(0.002 * w, 0.02)
    pB = min(0.0021 * w, 0.02)
    # correlated joint
    ppp = min(0.00008 * w, 0.002)
    out = {"P_pp": {}, "P_A_plus": {}, "P_B_plus": {}}
    for k in ["00","01","10","11"]:
        out["P_pp"][k] = ppp
        out["P_A_plus"][k] = pA
        out["P_B_plus"][k] = pB
    out["__provider_label__"] = "TOY (not model-faithful)"
    return out


def _compute_J_from_probs(N: Dict[str,int], probs: Dict[str, Any]) -> Dict[str, Any]:
    # Required:
    P_pp = probs["P_pp"]
    # derive P_p0 and P_0p
    if "P_p0" in probs and "P_0p" in probs:
        P_p0 = probs["P_p0"]
        P_0p = probs["P_0p"]
    else:
        P_A = probs.get("P_A_plus")
        P_B = probs.get("P_B_plus")
        if P_A is None or P_B is None:
            raise ValueError("Provider must return either (P_p0,P_0p) or (P_A_plus,P_B_plus) along with P_pp.")
        P_p0, P_0p = {}, {}
        for k in ["00","01","10","11"]:
            P_p0[k] = _clip01(float(P_A[k]) - float(P_pp[k]))
            P_0p[k] = _clip01(float(P_B[k]) - float(P_pp[k]))

    # CH definition used in runner:
    # J = N(++|ab) - N(+0|ab') - N(0+|a'b) - N(++|a'b')
    # mappings:
    # ab   -> "00"
    # ab'  -> "01"
    # a'b  -> "10"
    # a'b' -> "11"
    J = (
        N["00"] * float(P_pp["00"])
        - N["01"] * float(P_p0["01"])
        - N["10"] * float(P_0p["10"])
        - N["11"] * float(P_pp["11"])
    )
    return {
        "J_model": float(J),
        "P_pp": {k: float(P_pp[k]) for k in ["00","01","10","11"]},
        "P_p0": {k: float(P_p0[k]) for k in ["00","01","10","11"]},
        "P_0p": {k: float(P_0p[k]) for k in ["00","01","10","11"]},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--glob", default="run*.summary.json")
    ap.add_argument("--provider", default="", help="Path to ch_model_prob_provider_v1.py (implements compute_probabilities)")
    ap.add_argument("--params_json", default="", help="Optional model params JSON passed to provider via run_ctx['params']")
    ap.add_argument("--toy_ok", action="store_true", help="Allow a TOY provider to run the pipeline (NOT model-faithful).")
    ap.add_argument("--out_csv", default=r".\out\nist_ch\MODEL_SCORECARD.csv")
    ap.add_argument("--out_md", default=r".\out\nist_ch\MODEL_SCORECARD.md")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    if not in_dir.exists():
        raise SystemExit(f"in_dir not found: {in_dir}")

    summary_paths = sorted(in_dir.glob(args.glob))
    if not summary_paths:
        raise SystemExit(f"No summaries found matching {args.glob} in {in_dir}")

    params = {}
    if args.params_json:
        params = _read_json(Path(args.params_json))

    if args.toy_ok:
        compute_probs = _toy_provider
        provider_label = "TOY (not model-faithful)"
    else:
        if not args.provider:
            raise SystemExit("Provide --provider to a real probability provider, or pass --toy_ok for a TOY run.")
        compute_probs = _load_provider(Path(args.provider))
        provider_label = str(Path(args.provider))

    records: List[Dict[str, Any]] = []

    for sp in summary_paths:
        summary = _read_json(sp)
        counts_path = sp.with_name(sp.name.replace(".summary.json", ".counts.csv"))
        if not counts_path.exists():
            raise SystemExit(f"Missing counts.csv for {sp.name}")

        counts = _read_counts_csv(counts_path)
        N = counts["per_setting_trials"]
        N_valid = int(counts["total_valid_trials"])

        run_id = _extract_run_id(summary, sp)
        slots = summary.get("slots", [])
        bitmask_hex = summary.get("bitmask_hex", "")
        h5_path = summary.get("h5_path", "")
        label = "training_stub" if _is_training_stub(summary) else "real_run"

        # empirical
        J_data = int(summary.get("J", 0))
        ch = summary.get("CH_terms", {})
        N_pp_ab = int(ch.get("N_pp_ab", 0))
        N_p0_abp = int(ch.get("N_p0_abp", 0))
        N_0p_apb = int(ch.get("N_0p_apb", 0))
        N_pp_apbp = int(ch.get("N_pp_apbp", 0))

        # params for this run
        run_params = {}
        if params:
            run_params.update(params.get("defaults", {}))
            run_params.update(params.get("runs", {}).get(run_id, {}))

        run_ctx = {
            "run_id": run_id,
            "slots": slots,
            "bitmask_hex": bitmask_hex,
            "N_valid_by_setting": N,
            "trials_valid": N_valid,
            "h5_path": h5_path,
            "params": run_params,
        }

        probs = compute_probs(run_ctx)
        model = _compute_J_from_probs(N, probs)
        J_model = model["J_model"]

        j_data_per_1m = float(J_data) * 1e6 / N_valid if N_valid else 0.0
        j_model_per_1m = float(J_model) * 1e6 / N_valid if N_valid else 0.0

        records.append({
            "run_id": run_id,
            "label": label,
            "window": _window_label(slots),
            "slots": _slots_spec(slots),
            "bitmask_hex": bitmask_hex,
            "trials_valid": N_valid,
            "J_data": J_data,
            "J_model": f"{J_model:.6g}",
            "j_data_per_1M": f"{j_data_per_1m:.6g}",
            "j_model_per_1M": f"{j_model_per_1m:.6g}",
            "delta_J": f"{(J_model - J_data):.6g}",
            "delta_j_per_1M": f"{(j_model_per_1m - j_data_per_1m):.6g}",
            "sign_ok": "YES" if (J_model > 0) == (J_data > 0) else "NO",
            "provider": probs.get("__provider_label__", provider_label),
            "emp_N_pp_ab": N_pp_ab,
            "emp_N_p0_abp": N_p0_abp,
            "emp_N_0p_apb": N_0p_apb,
            "emp_N_pp_apbp": N_pp_apbp,
        })

    # sort
    def win_size(slotspec: str) -> int:
        if not slotspec:
            return 999
        if "-" in slotspec:
            a,b = slotspec.split("-",1)
            return int(b)-int(a)+1
        if "," in slotspec:
            return len(slotspec.split(","))
        return 1

    records.sort(key=lambda r: (r["run_id"], win_size(r["slots"])))

    out_csv = Path(args.out_csv); out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md = Path(args.out_md); out_md.parent.mkdir(parents=True, exist_ok=True)

    # write csv
    fieldnames = list(records[0].keys())
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in records:
            w.writerow(r)

    # write md
    headers = ["run_id","label","window","slots","trials_valid","J_data","J_model","delta_J","j_data_per_1M","j_model_per_1M","delta_j_per_1M","sign_ok","provider"]
    lines = ["# NIST CH/Eberhard model scorecard", ""]
    # simple md table
    def esc(s): return str(s).replace("|","\\|")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"]*len(headers)) + " |")
    for r in records:
        lines.append("| " + " | ".join(esc(r[h]) for h in headers) + " |")
    lines.append("")
    lines.append("## Notes")
    lines.append("- This compares empirical `J_data` (from run*.summary.json) to `J_model` produced by the probability provider.")
    lines.append("- Without a real provider, use `--toy_ok` only to sanity-check plumbing; it is **NOT** model-faithful.")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("[OK] wrote:", str(out_csv))
    print("[OK] wrote:", str(out_md))
    print("rows:", len(records))
    print("provider:", provider_label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
