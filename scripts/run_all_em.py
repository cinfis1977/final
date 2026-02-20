#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run the full prereg EM grid (24 runs) and produce EM_VERDICT_SHEET_v1.json.
No scans, no best-of.
"""

from __future__ import annotations
import json, os, subprocess, sys, platform, datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

OUTROOT = ROOT / "out" / "em_v1"
WRAPPER = ROOT / "runners" / "em_runner_wrapper.py"

PROTOCOL_VERSION = "EM_RUN_CARD_v1"

GRID = {
    "panel": ["bhabha", "mumu"],
    "cov": ["total", "diag_total"],
    "holdout": ["forward", "mid"],
    "case": ["null", "plus", "minus"],
}

def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT)).decode().strip()
    except Exception:
        return "unknown"

def pip_freeze() -> str:
    try:
        return subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode()
    except Exception:
        return ""

def run_one(args: List[str]) -> int:
    p = subprocess.run([sys.executable, str(WRAPPER)] + args, cwd=str(ROOT))
    return int(p.returncode)

def load_summary(run_dir: Path) -> Dict[str, Any]:
    with open(run_dir / "unit_summary.json", "r", encoding="utf-8") as f:
        return json.load(f)

def decide_em_verdict(units: Dict[Tuple[str,str,str], Dict[str, Any]], tol: Dict[str, float]) -> Dict[str, Any]:
    """
    units keyed by (panel,cov,holdout) with embedded d0,d+,d- and flags.
    tol: eps0, eps1, chi2_gate (optional).
    """
    eps0 = float(tol.get("eps0", 1e-3))
    eps1 = float(tol.get("eps1", 1e-3))
    chi2_gate = float(tol.get("chi2_gate", 0.0))

    def unit_status(panel: str, cov: str, holdout: str) -> Dict[str, Any]:
        u = units[(panel,cov,holdout)]
        flags_ok = u["flags_ok"]
        if not flags_ok:
            return {"status": "INCONCLUSIVE", **u}

        d0, dp, dm = u["d0"], u["dplus"], u["dminus"]
        null_ok = abs(d0) <= eps0
        sign_ok = (dp > eps1) and (dm < -eps1)
        both_improve = (dp > eps1) and (dm > eps1)
        both_worsen  = (dp < -eps1) and (dm < -eps1)
        tiny_effect = (abs(dp) < chi2_gate) and (abs(dm) < chi2_gate) if chi2_gate > 0 else False

        unit_pass = null_ok and sign_ok and (not tiny_effect)
        unit_fail = null_ok and ((dp < -eps1) or both_worsen or both_improve)
        unit_tension = null_ok and (not unit_pass) and (not unit_fail)

        st = "PASS" if unit_pass else ("FAIL" if unit_fail else ("TENSION" if unit_tension else "TENSION"))
        return {
            "status": st,
            "null_ok": null_ok,
            "sign_ok": sign_ok,
            "alarms": {
                "both_improve": both_improve,
                "both_worsen": both_worsen,
                "tiny_effect": tiny_effect,
            },
            **u,
        }

    def panel_agg(panel: str) -> str:
        # Primary judgement uses total cov forward+mid; diag_total is robustness
        u_tf = unit_status(panel,"total","forward")
        u_tm = unit_status(panel,"total","mid")
        u_df = unit_status(panel,"diag_total","forward")
        u_dm = unit_status(panel,"diag_total","mid")

        if "INCONCLUSIVE" in {u_tf["status"], u_tm["status"], u_df["status"], u_dm["status"]}:
            return "INCONCLUSIVE"
        if "FAIL" in {u_tf["status"], u_tm["status"]}:
            return "FAIL"
        # total pass requires both bands pass
        total_pass = (u_tf["status"] == "PASS") and (u_tm["status"] == "PASS")
        diag_sign_ok = (u_df.get("sign_ok", False) and u_dm.get("sign_ok", False))
        if total_pass and diag_sign_ok:
            return "PASS"
        if total_pass and (not diag_sign_ok):
            return "TENSION"
        # partial / asymmetric -> tension
        return "TENSION"

    bh = panel_agg("bhabha")
    mu = panel_agg("mumu")

    if "INCONCLUSIVE" in {bh, mu}:
        em = "INCONCLUSIVE"
    elif bh == "FAIL":
        em = "FAIL"
    elif bh == "PASS" and mu == "PASS":
        em = "SEAL"
    elif bh == "PASS" and mu != "FAIL":
        em = "PASS"
    else:
        em = "TENSION"

    return {"EM_verdict": em, "Bhabha_status": bh, "Mumu_status": mu}

def main() -> int:
    OUTROOT.mkdir(parents=True, exist_ok=True)

    # ---- Load config (packs, baselines, Aeff*, tolerances)
    cfg_path = ROOT / "protocol" / "em_config.json"
    tol_path = ROOT / "protocol" / "tolerances.json"

    if not cfg_path.exists():
        raise SystemExit(f"Missing {cfg_path}. Create it with pack/baseline paths + Aeff_star.")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    tol = json.loads(tol_path.read_text(encoding="utf-8")) if tol_path.exists() else {"eps0":1e-3,"eps1":1e-3,"chi2_gate":0.0}

    Aeff_star = float(cfg["Aeff_star"])
    packs = cfg["packs"]         # {"bhabha":"...json", "mumu":"...json"}
    baselines = cfg["baselines"] # {"bhabha":"...csv", "mumu":"...csv"}

    # ---- Run grid
    run_failfast = False
    for panel in GRID["panel"]:
        for cov in GRID["cov"]:
            for holdout in GRID["holdout"]:
                for case in GRID["case"]:
                    run_id = f"{panel}_{cov}_{holdout}_{case}"
                    outdir = OUTROOT / run_id
                    if case == "null":
                        Aeff_target = 0.0
                    elif case == "plus":
                        Aeff_target = +Aeff_star
                    else:
                        Aeff_target = -Aeff_star

                    args = [
                        "--panel", panel,
                        "--cov", cov,
                        "--holdout", holdout,
                        "--case", case,
                        "--pack", packs[panel],
                        "--baseline", baselines[panel],
                        "--outdir", str(outdir),
                        "--Aeff_target", str(Aeff_target),
                    ]
                    rc = run_one(args)
                    if rc != 0:
                        run_failfast = True

    # ---- Build unit table keyed by (panel,cov,holdout) containing d0,d+,d-
    units: Dict[Tuple[str,str,str], Dict[str,Any]] = {}
    for panel in GRID["panel"]:
        for cov in GRID["cov"]:
            for holdout in GRID["holdout"]:
                # load three cases
                base_id = f"{panel}_{cov}_{holdout}_"
                s_null  = load_summary(OUTROOT / (base_id + "null"))
                s_plus  = load_summary(OUTROOT / (base_id + "plus"))
                s_minus = load_summary(OUTROOT / (base_id + "minus"))

                flags_ok = (
                    s_null["flags"]["positivity_ok"] and s_null["flags"]["mapping_ok"] and s_null["flags"]["cov_ok"]
                    and s_plus["flags"]["positivity_ok"] and s_plus["flags"]["mapping_ok"] and s_plus["flags"]["cov_ok"]
                    and s_minus["flags"]["positivity_ok"] and s_minus["flags"]["mapping_ok"] and s_minus["flags"]["cov_ok"]
                )

                units[(panel,cov,holdout)] = {
                    "panel": panel, "cov": cov, "holdout": holdout,
                    "flags_ok": bool(flags_ok),
                    "d0": float(s_null["DeltaChi2_TEST"]),
                    "dplus": float(s_plus["DeltaChi2_TEST"]),
                    "dminus": float(s_minus["DeltaChi2_TEST"]),
                    "Aeff_star": Aeff_star,
                    "Aeff_plus": float(s_plus["Aeff"]),
                    "Aeff_minus": float(s_minus["Aeff"]),
                }

    verdict = decide_em_verdict(units, tol)

    # ---- Write verdict sheet + manifest
    sheet = {
        "protocol_version": PROTOCOL_VERSION,
        "git_commit": git_commit(),
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "platform": {
            "python": sys.version,
            "os": platform.platform(),
        },
        "tolerances": tol,
        "config": {
            "Aeff_star": Aeff_star,
            "packs": packs,
            "baselines": baselines,
        },
        "units": { f"{k[0]}|{k[1]}|{k[2]}": v for k,v in units.items() },
        "verdict": verdict,
        "notes": {
            "FAIL_phrase": "EM is rejected under the preregistered protocol at the tested Aeff (investigation ongoing)."
        }
    }

    (OUTROOT / "EM_VERDICT_SHEET_v1.json").write_text(json.dumps(sheet, indent=2), encoding="utf-8")
    (OUTROOT / "pip_freeze.txt").write_text(pip_freeze(), encoding="utf-8")
    (OUTROOT / "git_commit.txt").write_text(git_commit(), encoding="utf-8")

    print("\n=== EM VERDICT ===")
    print(json.dumps(verdict, indent=2))

    return 0 if not run_failfast else 2


if __name__ == "__main__":
    raise SystemExit(main())
