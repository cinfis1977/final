#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Init PARAMMODEL v4.1 params — DROP-IN v4.1

Provider uses anchored rule:
  eff_w = 1 + alpha*(w-1)

Infer alpha from slot6 (w=1) and slots5-7 (w=3):
  pw = 1 - (1 - p1)^(1 + alpha*(w-1))
=> alpha = (R - 1)/(w-1), where R = log(1-pw)/log(1-p1)

Outputs:
- out/nist_ch/model_params_parammodel.json
- out/nist_ch/parammodel_v4_1_alpha_report.json
"""
from __future__ import annotations
import argparse, csv, json, re, math, statistics
from pathlib import Path
from typing import Dict, Any, List

def _safe_rate(num: int, den: int) -> float:
    return (num / den) if den > 0 else 0.0

def _clip01(x: float) -> float:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return float(x)

def _read_counts(path: Path) -> Dict[str, Any]:
    N = {}
    A = {}
    B = {}
    AB = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            a = int(row["a_set"]); b = int(row["b_set"])
            k = f"{a}{b}"
            n = int(float(row.get("trials_valid", row.get("trials", "0"))))
            N[k] = n
            A[k] = int(float(row.get("alice_detect", "0")))
            B[k] = int(float(row.get("bob_detect", "0")))
            AB[k] = int(float(row.get("both_detect", "0")))
    return {"N": N, "A": A, "B": B, "AB": AB}

def _read_summary(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def _infer_alpha(p1: float, pw: float, w: int) -> float | None:
    p1 = float(p1); pw = float(pw)
    if not (0.0 < p1 < 1.0):
        return None
    if not (0.0 < pw < 1.0):
        return None
    if w <= 1:
        return None
    try:
        num = math.log(1.0 - pw)
        den = math.log(1.0 - p1)
        if den == 0:
            return None
        R = num / den
        a = (R - 1.0) / (w - 1.0)
        if not math.isfinite(a):
            return None
        return max(0.0, min(10.0, float(a)))
    except Exception:
        return None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--out_json", default=r".\out\nist_ch\model_params_parammodel.json")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    slot6_counts = sorted(in_dir.glob("run*_slot6.counts.csv"))
    if not slot6_counts:
        raise SystemExit("No run*_slot6.counts.csv found in in_dir.")

    runs: Dict[str, Dict[str, Any]] = {}
    report: Dict[str, Any] = {"alpha_pair_by_run": {}}

    for c6 in slot6_counts:
        m = re.search(r"run(\d{2}_\d{2})_slot6\.counts\.csv$", c6.name)
        if not m:
            continue
        run_id = m.group(1)

        s6 = in_dir / f"run{run_id}_slot6.summary.json"
        c3 = in_dir / f"run{run_id}_slots5_7.counts.csv"
        if not s6.exists():
            raise SystemExit(f"Missing summary: {s6}")
        if not c3.exists():
            raise SystemExit(f"Missing counts (slots5-7) for alpha fit: {c3}")

        d6 = _read_counts(c6)
        d3 = _read_counts(c3)
        summ = _read_summary(s6)
        ch = summ.get("CH_terms", {})

        N6, A6, B6, AB6 = d6["N"], d6["A"], d6["B"], d6["AB"]
        N3, AB3 = d3["N"], d3["AB"]

        def pA(k): return _safe_rate(A6.get(k, 0), N6.get(k, 0))
        def pB(k): return _safe_rate(B6.get(k, 0), N6.get(k, 0))
        def pPP6(k): return _safe_rate(AB6.get(k, 0), N6.get(k, 0))
        def pPP3(k): return _safe_rate(AB3.get(k, 0), N3.get(k, 0))

        pair6 = {k: _clip01(pPP6(k)) for k in ["00","01","10","11"]}
        pair3 = {k: _clip01(pPP3(k)) for k in ["00","01","10","11"]}

        alphas: List[float] = []
        per_setting: Dict[str, float] = {}
        for k in ["00","01","10","11"]:
            a = _infer_alpha(pair6[k], pair3[k], w=3)
            if a is not None:
                alphas.append(a)
                per_setting[k] = a

        alpha_pair = statistics.median(alphas) if alphas else 1.0
        report["alpha_pair_by_run"][run_id] = {"median": alpha_pair, "per_setting": per_setting}

        # CH-only terms provide +0 at 01 and 0+ at 10 (slot6)
        rate_p0_01 = _clip01(_safe_rate(int(ch.get("N_p0_abp", 0)), N6.get("01", 0)))
        rate_0p_10 = _clip01(_safe_rate(int(ch.get("N_0p_apb", 0)), N6.get("10", 0)))

        a1_u = 0.5 * (max(0.0, pA("10") - pair6["10"]) + max(0.0, pA("11") - pair6["11"]))
        b1_u = 0.5 * (max(0.0, pB("01") - pair6["01"]) + max(0.0, pB("11") - pair6["11"]))

        runs[run_id] = {
            "window_union_mode": "union",
            "gamma_window": 0.0,
            "alpha_pair": float(alpha_pair),
            "p_pair_1slot_by_setting": pair6,
            "pA0_u_1slot": rate_p0_01,
            "pA1_u_1slot": _clip01(a1_u),
            "pB0_u_1slot": rate_0p_10,
            "pB1_u_1slot": _clip01(b1_u),
        }

    out_json.write_text(json.dumps({"defaults": {}, "runs": runs}, indent=2), encoding="utf-8")
    rep_path = out_json.parent / "parammodel_v4_1_alpha_report.json"
    rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[OK] wrote:", str(out_json))
    print("[OK] wrote:", str(rep_path))
    print("runs:", sorted(runs.keys()))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
