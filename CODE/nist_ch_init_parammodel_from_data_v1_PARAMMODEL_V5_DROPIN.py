#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST CH PARAMMODEL v5 init (two-parameter calibrated bridge)

What this writes
----------------
- model_params_parammodel.json
- parammodel_v5_alpha_beta_report.json

Important note
--------------
This is a calibrated BRIDGE layer, not a model-faithful GKSL provider.
It uses the empirical slot6 / slots5-7 / slots4-8 windows to infer
anchored two-parameter growth laws for:
    - pair channel P_pp
    - Alice-only channel P_p0-like seed support
    - Bob-only   channel P_0p-like seed support

Growth law (anchored):
    eff(w) = 1 + alpha*(w-1) + beta*(w-1)*(w-3)
    p_w    = 1 - (1 - p_1)**eff(w)

So:
    w=1 -> eff=1   (slot6 seed preserved exactly)
    w=3 -> eff=1+2*alpha
    w=5 -> eff=1+4*alpha+8*beta

Files expected in --in_dir
--------------------------
run<id>_slot6.counts.csv / .summary.json
run<id>_slots5_7.counts.csv / .summary.json
run<id>_slots4_8.counts.csv / .summary.json

This script is intentionally tolerant to small schema variation in counts.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from statistics import median
from typing import Dict, Tuple, Any

KEYS = ["00", "01", "10", "11"]
EPS = 1e-15


def _clip01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0 - 1e-15
    return float(x)


def _safe_ratio(num: float, den: float) -> float:
    return (float(num) / float(den)) if den else 0.0


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_counts(path: Path) -> Tuple[Dict[str, int], Dict[str, Dict[str, int]]]:
    per: Dict[str, int] = {}
    aux: Dict[str, Dict[str, int]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise ValueError(f"empty counts csv: {path}")
        for row in r:
            k = str(row.get("setting") or row.get("settings") or "").strip()
            if k not in KEYS:
                continue
            # denominator
            den = None
            for cand in ["N_valid", "n_valid", "trials_valid", "valid_trials", "N", "n"]:
                if cand in row and str(row[cand]).strip() != "":
                    den = int(float(row[cand]))
                    break
            if den is None:
                raise KeyError(f"could not find denominator column in {path}; fields={r.fieldnames}")
            per[k] = den
            # optional aux columns
            for cand in ["both_detect", "alice_detect", "bob_detect", "pp", "p0", "0p"]:
                if cand in row and str(row[cand]).strip() != "":
                    aux.setdefault(cand, {})[k] = int(float(row[cand]))
    return per, aux


def _extract_from_summary(summary: Dict[str, Any]) -> Dict[str, int]:
    ch = summary.get("CH_terms", {})
    return {
        "N_pp_ab": int(ch.get("N_pp_ab", 0)),
        "N_p0_abp": int(ch.get("N_p0_abp", 0)),
        "N_0p_apb": int(ch.get("N_0p_apb", 0)),
        "N_pp_apbp": int(ch.get("N_pp_apbp", 0)),
    }


def _window_tag_to_w(tag: str) -> int:
    if tag == "slot6":
        return 1
    if tag == "slots5_7":
        return 3
    if tag == "slots4_8":
        return 5
    raise ValueError(f"unknown tag: {tag}")


def _eff_from_union(p1: float, pw: float) -> float:
    p1 = _clip01(p1)
    pw = _clip01(pw)
    if p1 <= 0.0 or pw <= 0.0:
        return 0.0
    if p1 >= 1.0 - 1e-15:
        return 1.0
    a = math.log(max(EPS, 1.0 - pw))
    b = math.log(max(EPS, 1.0 - p1))
    if abs(b) < EPS:
        return 1.0
    return max(0.0, a / b)


def _infer_alpha_beta(p1: float, p3: float, p5: float) -> Tuple[float, float, float, float]:
    """Return (alpha, beta, eff3, eff5)."""
    p1 = _clip01(p1)
    p3 = _clip01(p3)
    p5 = _clip01(p5)
    if p1 <= 0.0 or (p3 <= 0.0 and p5 <= 0.0):
        return 1.0, 0.0, 1.0, 1.0
    eff3 = _eff_from_union(p1, p3)
    eff5 = _eff_from_union(p1, p5)
    alpha = (eff3 - 1.0) / 2.0
    beta = (eff5 - 1.0 - 4.0 * alpha) / 8.0
    if not math.isfinite(alpha):
        alpha = 1.0
    if not math.isfinite(beta):
        beta = 0.0
    return float(alpha), float(beta), float(eff3), float(eff5)


def _load_window(in_dir: Path, run_id: str, tag: str) -> Dict[str, Any]:
    counts_path = in_dir / f"run{run_id}_{tag}.counts.csv"
    summary_path = in_dir / f"run{run_id}_{tag}.summary.json"
    if not counts_path.exists():
        raise FileNotFoundError(f"missing counts: {counts_path}")
    if not summary_path.exists():
        raise FileNotFoundError(f"missing summary: {summary_path}")
    N, aux = _read_counts(counts_path)
    summ = _read_json(summary_path)
    ch = _extract_from_summary(summ)

    # exact CH-term fallbacks for settings 01/10/00/11 when counts.csv lacks dedicated columns
    both = dict(aux.get("both_detect", {}))
    both.setdefault("00", ch["N_pp_ab"])
    both.setdefault("11", ch["N_pp_apbp"])

    # alice_detect and bob_detect can usually be reconstructed from p0/0p + pair on the CH settings
    alice = dict(aux.get("alice_detect", {}))
    bob = dict(aux.get("bob_detect", {}))
    alice.setdefault("00", both.get("00", 0))
    bob.setdefault("00", both.get("00", 0))
    alice.setdefault("01", ch["N_p0_abp"] + both.get("01", 0))
    bob.setdefault("10", ch["N_0p_apb"] + both.get("10", 0))

    return {
        "N": N,
        "both": both,
        "alice": alice,
        "bob": bob,
        "summary": summ,
        "counts_path": str(counts_path),
        "summary_path": str(summary_path),
    }


def _discover_runs(in_dir: Path) -> list[str]:
    ids = set()
    pat = re.compile(r"^run(.+?)_slot6\.summary\.json$")
    for p in in_dir.glob("run*_slot6.summary.json"):
        m = pat.match(p.name)
        if m:
            ids.add(m.group(1))
    return sorted(ids)


def build_params_for_run(in_dir: Path, run_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    w1 = _load_window(in_dir, run_id, "slot6")
    w3 = _load_window(in_dir, run_id, "slots5_7")
    w5 = _load_window(in_dir, run_id, "slots4_8")

    out: Dict[str, Any] = {
        "bridge_version": "PARAMMODEL v5 (calibrated bridge; alpha+beta)",
        "window_union_mode": "anchored_alpha_beta",
        "p_pair_1slot_by_setting": {},
        "pA1_u_1slot": {},
        "pB1_u_1slot": {},
        "alpha_pair_by_setting": {},
        "beta_pair_by_setting": {},
        "alpha_Au_by_setting": {},
        "beta_Au_by_setting": {},
        "alpha_Bu_by_setting": {},
        "beta_Bu_by_setting": {},
    }
    report: Dict[str, Any] = {
        "run_id": run_id,
        "pair": {},
        "A_only": {},
        "B_only": {},
    }

    pair_alphas = []
    pair_betas = []

    for k in KEYS:
        N1 = w1["N"].get(k, 0)
        N3 = w3["N"].get(k, 0)
        N5 = w5["N"].get(k, 0)

        pp1 = _safe_ratio(w1["both"].get(k, 0), N1)
        pp3 = _safe_ratio(w3["both"].get(k, 0), N3)
        pp5 = _safe_ratio(w5["both"].get(k, 0), N5)

        a1u_1 = _safe_ratio(max(0, w1["alice"].get(k, 0) - w1["both"].get(k, 0)), N1)
        a1u_3 = _safe_ratio(max(0, w3["alice"].get(k, 0) - w3["both"].get(k, 0)), N3)
        a1u_5 = _safe_ratio(max(0, w5["alice"].get(k, 0) - w5["both"].get(k, 0)), N5)

        b1u_1 = _safe_ratio(max(0, w1["bob"].get(k, 0) - w1["both"].get(k, 0)), N1)
        b1u_3 = _safe_ratio(max(0, w3["bob"].get(k, 0) - w3["both"].get(k, 0)), N3)
        b1u_5 = _safe_ratio(max(0, w5["bob"].get(k, 0) - w5["both"].get(k, 0)), N5)

        ap, bp, eff3p, eff5p = _infer_alpha_beta(pp1, pp3, pp5)
        aa, ba, eff3a, eff5a = _infer_alpha_beta(a1u_1, a1u_3, a1u_5)
        ab, bb, eff3b, eff5b = _infer_alpha_beta(b1u_1, b1u_3, b1u_5)

        out["p_pair_1slot_by_setting"][k] = _clip01(pp1)
        out["pA1_u_1slot"][k] = _clip01(a1u_1)
        out["pB1_u_1slot"][k] = _clip01(b1u_1)
        out["alpha_pair_by_setting"][k] = float(ap)
        out["beta_pair_by_setting"][k] = float(bp)
        out["alpha_Au_by_setting"][k] = float(aa)
        out["beta_Au_by_setting"][k] = float(ba)
        out["alpha_Bu_by_setting"][k] = float(ab)
        out["beta_Bu_by_setting"][k] = float(bb)

        pair_alphas.append(ap)
        pair_betas.append(bp)

        report["pair"][k] = {
            "p1": pp1,
            "p3": pp3,
            "p5": pp5,
            "eff3": eff3p,
            "eff5": eff5p,
            "alpha": ap,
            "beta": bp,
        }
        report["A_only"][k] = {
            "p1": a1u_1,
            "p3": a1u_3,
            "p5": a1u_5,
            "eff3": eff3a,
            "eff5": eff5a,
            "alpha": aa,
            "beta": ba,
        }
        report["B_only"][k] = {
            "p1": b1u_1,
            "p3": b1u_3,
            "p5": b1u_5,
            "eff3": eff3b,
            "eff5": eff5b,
            "alpha": ab,
            "beta": bb,
        }

    out["alpha_pair"] = float(median(pair_alphas)) if pair_alphas else 1.0
    out["beta_pair"] = float(median(pair_betas)) if pair_betas else 0.0
    report["median_alpha_pair"] = out["alpha_pair"]
    report["median_beta_pair"] = out["beta_pair"]
    return out, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", required=True)
    ap.add_argument("--out_json", required=True)
    ns = ap.parse_args()

    in_dir = Path(ns.in_dir)
    out_json = Path(ns.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    runs: Dict[str, Any] = {}
    report_runs: Dict[str, Any] = {}

    run_ids = _discover_runs(in_dir)
    if not run_ids:
        raise SystemExit(f"No run*_slot6.summary.json found in {in_dir}")

    for run_id in run_ids:
        cfg, rep = build_params_for_run(in_dir, run_id)
        runs[run_id] = cfg
        report_runs[run_id] = rep

    payload = {
        "defaults": {
            "bridge_version": "PARAMMODEL v5 (calibrated bridge; alpha+beta)",
            "window_union_mode": "anchored_alpha_beta",
        },
        "runs": runs,
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("[OK] wrote:", str(out_json).replace("/", "\\"))

    rep_path = out_json.parent / "parammodel_v5_alpha_beta_report.json"
    rep_payload = {
        "kind": "PARAMMODEL v5 alpha/beta report",
        "note": "Calibrated bridge using slot6 + slots5-7 + slots4-8 empirical windows. Not holdout.",
        "runs": report_runs,
    }
    rep_path.write_text(json.dumps(rep_payload, indent=2), encoding="utf-8")
    print("[OK] wrote:", str(rep_path).replace("/", "\\"))
    print("runs:", sorted(runs.keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
