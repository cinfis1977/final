#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Init PARAMMODEL v5.1 params from empirical CH window files — DROP-IN (bugfix)

Outputs
-------
- model_params_parammodel_v5_1.json
- parammodel_v5_1_channel_report.json

This is a calibrated bridge, not a model-faithful GKSL init. It seeds and fits the
three scorecard-visible CH channels directly, per setting:
  - P_pp  (++ )
  - P_p0  (+0 )
  - P_0p  (0+ )

Windows used:
- slot6      -> w=1  (seed)
- slots5_7   -> w=3
- slots4_8   -> w=5

The effective-trials law is anchored so the slot6 seed is preserved exactly:
    eff(w) = 1 + alpha*(w-1) + beta*(w-1)*(w-3)

with p_w = 1 - (1 - p_1)^eff(w)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, Tuple


KEYS = ("00", "01", "10", "11")
WINDOWS: Tuple[Tuple[str, int], ...] = (("slot6", 1), ("slots5_7", 3), ("slots4_8", 5))

TRIAL_COLS = ("trials_valid", "trials", "n_valid", "n_trials")
ALICE_COLS = ("alice_detect", "alice_plus", "alice_count", "A_detect", "A")
BOB_COLS = ("bob_detect", "bob_plus", "bob_count", "B_detect", "B")
BOTH_COLS = ("both_detect", "coinc", "coinc_detect", "coincidences", "AB_detect", "AB")


def _clip01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return float(x)


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        if v is None or v == "":
            return int(default)
        return int(float(v))
    except Exception:
        return int(default)


def _safe_rate(num: int, den: int) -> float:
    return float(num) / float(den) if den > 0 else 0.0


def _first_present(row: Dict[str, Any], candidates: Iterable[str], default: int = 0) -> int:
    for c in candidates:
        if c in row and row[c] not in (None, ""):
            return _safe_int(row[c], default)
    return int(default)


def _norm_key_from_row(row: Dict[str, Any]) -> str:
    if "setting" in row and row["setting"] not in (None, ""):
        raw = str(row["setting"]).strip()
        if raw in KEYS:
            return raw
        m = re.search(r"([01])\D*([01])", raw)
        if m:
            return f"{m.group(1)}{m.group(2)}"
    a_fields = ("a_set", "alice_setting", "a", "A_set")
    b_fields = ("b_set", "bob_setting", "b", "B_set")
    a_val = None
    b_val = None
    for name in a_fields:
        if name in row and row[name] not in (None, ""):
            a_val = _safe_int(row[name], 0)
            break
    for name in b_fields:
        if name in row and row[name] not in (None, ""):
            b_val = _safe_int(row[name], 0)
            break
    if a_val is None or b_val is None:
        raise ValueError(f"Could not infer setting key from row columns: {sorted(row.keys())}")
    return f"{int(a_val)}{int(b_val)}"


def _read_counts(path: Path) -> Dict[str, Dict[str, int]]:
    out = {
        "N": {k: 0 for k in KEYS},
        "A": {k: 0 for k in KEYS},
        "B": {k: 0 for k in KEYS},
        "AB": {k: 0 for k in KEYS},
    }
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        saw_any = False
        for row in reader:
            if not row:
                continue
            saw_any = True
            k = _norm_key_from_row(row)
            out["N"][k] = _first_present(row, TRIAL_COLS, 0)
            out["A"][k] = _first_present(row, ALICE_COLS, 0)
            out["B"][k] = _first_present(row, BOB_COLS, 0)
            out["AB"][k] = _first_present(row, BOTH_COLS, 0)
        if not saw_any:
            raise ValueError(f"empty counts csv: {path}")
    return out


def _read_summary(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_ch(summary: Dict[str, Any]) -> Dict[str, int]:
    ch = dict(summary.get("CH_terms", {}) or {})
    return {k: _safe_int(v, 0) for k, v in ch.items()}


def _window_payload(in_dir: Path, run_id: str, tag: str) -> Tuple[Dict[str, Dict[str, int]], Dict[str, int]]:
    counts_path = in_dir / f"run{run_id}_{tag}.counts.csv"
    summary_path = in_dir / f"run{run_id}_{tag}.summary.json"
    if not counts_path.exists():
        raise FileNotFoundError(f"Missing counts file: {counts_path}")
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary file: {summary_path}")
    return _read_counts(counts_path), _summary_ch(_read_summary(summary_path))


def _channel_counts(counts: Dict[str, Dict[str, int]], ch: Dict[str, int]) -> Dict[str, Dict[str, int]]:
    N = counts["N"]
    A = counts["A"]
    B = counts["B"]
    AB = counts["AB"]

    pp = {k: max(0, int(AB.get(k, 0))) for k in KEYS}
    p0 = {k: max(0, int(A.get(k, 0)) - int(AB.get(k, 0))) for k in KEYS}
    op = {k: max(0, int(B.get(k, 0)) - int(AB.get(k, 0))) for k in KEYS}

    # Exact CH fallbacks / overrides where those counts are explicitly present in summary.json.
    if "N_pp_ab" in ch:
        pp["00"] = max(0, int(ch["N_pp_ab"]))
    if "N_pp_apbp" in ch:
        pp["11"] = max(0, int(ch["N_pp_apbp"]))
    if "N_p0_abp" in ch:
        p0["01"] = max(0, int(ch["N_p0_abp"]))
    if "N_0p_apb" in ch:
        op["10"] = max(0, int(ch["N_0p_apb"]))

    # Keep counts physically bounded by trials.
    for k in KEYS:
        n = max(0, int(N.get(k, 0)))
        pp[k] = min(pp[k], n)
        p0[k] = min(p0[k], n)
        op[k] = min(op[k], n)

    return {"N": N, "pp": pp, "p0": p0, "0p": op}


def _rate_map(chan_counts: Dict[str, Dict[str, int]], chan_key: str) -> Dict[str, float]:
    N = chan_counts["N"]
    C = chan_counts[chan_key]
    return {k: _clip01(_safe_rate(int(C.get(k, 0)), int(N.get(k, 0)))) for k in KEYS}


def _infer_eff(p1: float, pw: float, default_eff: float) -> float:
    p1 = _clip01(p1)
    pw = _clip01(pw)
    if p1 <= 0.0:
        return float(default_eff) if pw <= 0.0 else float(default_eff)
    if p1 >= 1.0:
        return 1.0
    if pw <= 0.0:
        return 0.0
    if pw >= 1.0:
        return max(float(default_eff), 1.0)
    num = math.log(max(1e-300, 1.0 - pw))
    den = math.log(max(1e-300, 1.0 - p1))
    if den == 0.0:
        return float(default_eff)
    eff = num / den
    if not math.isfinite(eff):
        return float(default_eff)
    if eff < 0.0:
        eff = 0.0
    return float(eff)


def _infer_alpha_beta(p1: float, p3: float, p5: float) -> Tuple[float, float, float, float]:
    # Defaults reproduce independent-slot union growth.
    if p1 <= 0.0 and p3 <= 0.0 and p5 <= 0.0:
        return 1.0, 0.0, 3.0, 5.0
    eff3 = _infer_eff(p1, p3, 3.0)
    eff5 = _infer_eff(p1, p5, 5.0)
    alpha = 0.5 * (eff3 - 1.0)
    beta = (eff5 - 1.0 - 4.0 * alpha) / 8.0
    if not math.isfinite(alpha):
        alpha = 1.0
    if not math.isfinite(beta):
        beta = 0.0
    return float(alpha), float(beta), float(eff3), float(eff5)


def _active_channel(p1: float, p3: float, p5: float) -> bool:
    return any(x > 0.0 for x in (p1, p3, p5))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default=r".\out\nist_ch")
    ap.add_argument("--out_json", default=r".\out\nist_ch\model_params_parammodel_v5_1.json")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    run_ids = []
    for p in sorted(in_dir.glob("run*_slot6.summary.json")):
        m = re.search(r"run(\d{2}_\d{2})_slot6\.summary\.json$", p.name)
        if m:
            run_ids.append(m.group(1))
    if not run_ids:
        raise SystemExit(f"No run*_slot6.summary.json found in {in_dir}")

    top: Dict[str, Any] = {
        "defaults": {
            "bridge_version": "PARAMMODEL v5.1 (calibrated bridge; direct CH channels)",
            "window_union_mode": "anchored_alpha_beta",
        },
        "runs": {},
    }
    report: Dict[str, Any] = {
        "kind": "PARAMMODEL v5.1 channel report",
        "note": "Calibrated bridge using slot6 + slots5-7 + slots4-8 empirical CH channels. Not holdout.",
        "runs": {},
    }

    for run_id in run_ids:
        payloads = {}
        for tag, _w in WINDOWS:
            counts, ch = _window_payload(in_dir, run_id, tag)
            payloads[tag] = _channel_counts(counts, ch)

        per_window_rates = {
            tag: {
                "pp": _rate_map(payloads[tag], "pp"),
                "p0": _rate_map(payloads[tag], "p0"),
                "0p": _rate_map(payloads[tag], "0p"),
            }
            for tag, _w in WINDOWS
        }

        out = {
            "bridge_version": "PARAMMODEL v5.1 (calibrated bridge; direct CH channels)",
            "window_union_mode": "anchored_alpha_beta",
            "p_pp_1slot_by_setting": {},
            "p_p0_1slot_by_setting": {},
            "p_0p_1slot_by_setting": {},
            "alpha_pp_by_setting": {},
            "beta_pp_by_setting": {},
            "alpha_p0_by_setting": {},
            "beta_p0_by_setting": {},
            "alpha_0p_by_setting": {},
            "beta_0p_by_setting": {},
        }
        rep_run: Dict[str, Any] = {
            "run_id": run_id,
            "pp": {},
            "p0": {},
            "0p": {},
        }

        pair_alphas = []
        pair_betas = []

        for k in KEYS:
            pp1 = per_window_rates["slot6"]["pp"][k]
            pp3 = per_window_rates["slots5_7"]["pp"][k]
            pp5 = per_window_rates["slots4_8"]["pp"][k]
            apair, bpair, eff3, eff5 = _infer_alpha_beta(pp1, pp3, pp5)
            out["p_pp_1slot_by_setting"][k] = pp1
            out["alpha_pp_by_setting"][k] = apair
            out["beta_pp_by_setting"][k] = bpair
            rep_run["pp"][k] = {
                "p1": pp1,
                "p3": pp3,
                "p5": pp5,
                "eff3": eff3,
                "eff5": eff5,
                "alpha": apair,
                "beta": bpair,
            }
            if _active_channel(pp1, pp3, pp5):
                pair_alphas.append(apair)
                pair_betas.append(bpair)

            p01 = per_window_rates["slot6"]["p0"][k]
            p03 = per_window_rates["slots5_7"]["p0"][k]
            p05 = per_window_rates["slots4_8"]["p0"][k]
            a_p0, b_p0, eff3_p0, eff5_p0 = _infer_alpha_beta(p01, p03, p05)
            out["p_p0_1slot_by_setting"][k] = p01
            out["alpha_p0_by_setting"][k] = a_p0
            out["beta_p0_by_setting"][k] = b_p0
            rep_run["p0"][k] = {
                "p1": p01,
                "p3": p03,
                "p5": p05,
                "eff3": eff3_p0,
                "eff5": eff5_p0,
                "alpha": a_p0,
                "beta": b_p0,
            }

            op1 = per_window_rates["slot6"]["0p"][k]
            op3 = per_window_rates["slots5_7"]["0p"][k]
            op5 = per_window_rates["slots4_8"]["0p"][k]
            a_0p, b_0p, eff3_0p, eff5_0p = _infer_alpha_beta(op1, op3, op5)
            out["p_0p_1slot_by_setting"][k] = op1
            out["alpha_0p_by_setting"][k] = a_0p
            out["beta_0p_by_setting"][k] = b_0p
            rep_run["0p"][k] = {
                "p1": op1,
                "p3": op3,
                "p5": op5,
                "eff3": eff3_0p,
                "eff5": eff5_0p,
                "alpha": a_0p,
                "beta": b_0p,
            }

        out["alpha_pair"] = float(median(pair_alphas)) if pair_alphas else 1.0
        out["beta_pair"] = float(median(pair_betas)) if pair_betas else 0.0
        rep_run["median_alpha_pair"] = out["alpha_pair"]
        rep_run["median_beta_pair"] = out["beta_pair"]

        top["runs"][run_id] = out
        report["runs"][run_id] = rep_run

    out_json.write_text(json.dumps(top, indent=2), encoding="utf-8")
    rep_path = out_json.parent / "parammodel_v5_1_channel_report.json"
    rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[OK] wrote:", str(out_json))
    print("[OK] wrote:", str(rep_path))
    print("runs:", sorted(top["runs"].keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
