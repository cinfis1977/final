# ms_dynamics_integrity_aggregate_v1_DROPIN.py
# === DYNAMICS INTEGRITY AGGREGATOR v1 (DROP-IN) ===
# Aggregates Layer-A prereg verdicts + Layer-B audit outputs across 3 arms and ablations.
#
# Outputs:
#   out/MS/<run_id>/DYNAMICS_INTEGRITY_SUMMARY.json
#   out/MS/<run_id>/DYNAMICS_INTEGRITY_SUMMARY.md
#
# Safe: read-only, no mutation.

from __future__ import annotations

import argparse
import json
import os
import glob
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple


ACTIONS = {
    "audit": "ms_dynamic_state_audit.json",
    "telemetry": "ms_dynamic_telemetry.json",
    "verdict": "prereg_lock_and_final_verdict_goodppm3.json",
    "drift": "drift_common.csv",
    "resid": "residuals.csv",
}

# Prefer these ablation labels (but script is resilient)
KNOWN_ABLATIONS = ["internal_only", "thread_only", "full"]
# Folder names used by the 3-arm driver.
KNOWN_ARMS = ["A1_B2", "A1_B3_holdout", "A2_B3_thirdarm"]


def _norm(p: str) -> str:
    return p.replace("\\", "/")


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _exists(path: str) -> bool:
    return path is not None and os.path.isfile(path)


def _relpath(path: str, root: str) -> str:
    try:
        return os.path.relpath(path, root)
    except Exception:
        return path


def _glob_first(patterns: List[str]) -> Optional[str]:
    for pat in patterns:
        hits = glob.glob(pat, recursive=True)
        if hits:
            hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return hits[0]
    return None


def _guess_ablation(path: str) -> str:
    lp = path.lower()
    for a in KNOWN_ABLATIONS:
        if f"\\{a}\\" in lp or f"/{a}/" in lp or lp.endswith(f"\\{a}") or lp.endswith(f"/{a}"):
            return a
    return "unknown"


def _guess_arm(path: str) -> str:
    lp = path.lower()
    for arm in KNOWN_ARMS:
        a = arm.lower()
        if f"\\{a}\\" in lp or f"/{a}/" in lp or lp.endswith(f"\\{a}") or lp.endswith(f"/{a}"):
            return arm
    return "unknown"


def _list_subdirs(path: str) -> List[str]:
    try:
        kids = [os.path.join(path, x) for x in os.listdir(path)]
        return [k for k in kids if os.path.isdir(k)]
    except Exception:
        return []


@dataclass
class ArmRecord:
    ablation: str
    arm: str
    folder: str  # absolute folder
    verdict_path: Optional[str]
    audit_path: Optional[str]
    telemetry_path: Optional[str]
    drift_csv: Optional[str]
    residuals_csv: Optional[str]
    prereg: Dict[str, Any]
    audit: Dict[str, Any]
    telemetry: Dict[str, Any]


def _safe_pick(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    out = {}
    for k in keys:
        if k in d:
            out[k] = d[k]
    return out


def _get(d: Dict[str, Any], *keys: str) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def find_run_root(root: str, run_id: str) -> str:
    # Typical:
    # out/MS/<run_id>/...
    cand = os.path.join(root, "out", "MS", run_id)
    if os.path.isdir(cand):
        return cand

    # fallback: search for folders containing run_id
    hits = glob.glob(os.path.join(root, "out", "**", run_id), recursive=True)
    hits = [h for h in hits if os.path.isdir(h)]
    if hits:
        # choose the one with most expected files under it
        def score(p: str) -> int:
            s = 0
            for fn in ACTIONS.values():
                s += len(glob.glob(os.path.join(p, "**", fn), recursive=True))
            return s

        hits.sort(key=score, reverse=True)
        return hits[0]

    # last resort: just use out
    return os.path.join(root, "out")


def _find_ablation_dirs(run_root: str) -> List[str]:
    # Usually: out/MS/<run_id>/<ablation>/...
    ab_dirs = []
    for d in _list_subdirs(run_root):
        name = os.path.basename(d)
        if name in KNOWN_ABLATIONS or name.lower() in [a.lower() for a in KNOWN_ABLATIONS]:
            ab_dirs.append(d)
    if ab_dirs:
        return ab_dirs

    # fallback: recursive search
    hits = []
    for a in KNOWN_ABLATIONS:
        hits.extend(glob.glob(os.path.join(run_root, "**", a), recursive=True))
    hits = [h for h in hits if os.path.isdir(h)]
    # prefer shallowest
    hits.sort(key=lambda p: _norm(p).count("/"))
    return hits


def _find_verdict_for_ablation(ablation_dir: str) -> Optional[str]:
    # Typical: <ablation>/final/prereg_lock_and_final_verdict_goodppm3.json
    cand = os.path.join(ablation_dir, "final", ACTIONS["verdict"])
    if os.path.isfile(cand):
        return cand
    # fallback recursive
    hits = glob.glob(os.path.join(ablation_dir, "**", ACTIONS["verdict"]), recursive=True)
    hits = [h for h in hits if os.path.isfile(h)]
    if not hits:
        return None
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0]


def _find_arm_dirs(ablation_dir: str) -> List[str]:
    # Prefer the canonical names if present.
    out = []
    for arm in KNOWN_ARMS:
        cand = os.path.join(ablation_dir, arm)
        if os.path.isdir(cand):
            out.append(cand)
    if out:
        return out

    # Fallback: any folder under ablation_dir containing telemetry or audit.
    hits = []
    for fn in (ACTIONS["telemetry"], ACTIONS["audit"], "scan_state.csv"):
        hits.extend(glob.glob(os.path.join(ablation_dir, "**", fn), recursive=True))
    arm_dirs = sorted({os.path.dirname(h) for h in hits})
    # Keep only direct-ish children under ablation_dir (avoid final/)
    cleaned = []
    for d in arm_dirs:
        base = os.path.basename(d)
        if base == "final":
            continue
        cleaned.append(d)
    return cleaned


def collect_arm_records(run_root: str) -> List[ArmRecord]:
    """Collect per-(ablation, arm) records.

    IMPORTANT: In this repo the paper-facing prereg verdict lives in:
      out/MS/<run_id>/<ablation>/final/prereg_lock_and_final_verdict_goodppm3.json
    while the Layer-B dynamics artifacts live in:
      out/MS/<run_id>/<ablation>/<arm>/(ms_dynamic_state_audit.json, ms_dynamic_telemetry.json, ...)

    So we attach the single ablation-level verdict to each arm.
    """

    records: List[ArmRecord] = []
    ab_dirs = _find_ablation_dirs(run_root)
    if not ab_dirs:
        return records

    for ab_dir in ab_dirs:
        ablation = os.path.basename(ab_dir).lower()
        verdict_path = _find_verdict_for_ablation(ab_dir)
        prereg = {}
        if verdict_path and os.path.isfile(verdict_path):
            try:
                prereg = _read_json(verdict_path)
            except Exception:
                prereg = {"_read_error": True}

        arm_dirs = _find_arm_dirs(ab_dir)
        for arm_dir in arm_dirs:
            arm = os.path.basename(arm_dir)

            audit_p = os.path.join(arm_dir, ACTIONS["audit"])
            telem_p = os.path.join(arm_dir, ACTIONS["telemetry"])
            drift_p = os.path.join(arm_dir, ACTIONS["drift"])
            resid_p = os.path.join(arm_dir, ACTIONS["resid"])

            audit = {}
            telemetry = {}
            if os.path.isfile(audit_p):
                try:
                    audit = _read_json(audit_p)
                except Exception:
                    audit = {"_read_error": True}
            if os.path.isfile(telem_p):
                try:
                    telemetry = _read_json(telem_p)
                except Exception:
                    telemetry = {"_read_error": True}

            records.append(
                ArmRecord(
                    ablation=ablation,
                    arm=arm,
                    folder=arm_dir,
                    verdict_path=verdict_path,
                    audit_path=audit_p if os.path.isfile(audit_p) else None,
                    telemetry_path=telem_p if os.path.isfile(telem_p) else None,
                    drift_csv=drift_p if os.path.isfile(drift_p) else None,
                    residuals_csv=resid_p if os.path.isfile(resid_p) else None,
                    prereg=prereg,
                    audit=audit,
                    telemetry=telemetry,
                )
            )

    # Stable ordering for deterministic output.
    def _sort_key(r: ArmRecord) -> tuple:
        a_idx = KNOWN_ABLATIONS.index(r.ablation) if r.ablation in KNOWN_ABLATIONS else 999
        arm_idx = KNOWN_ARMS.index(r.arm) if r.arm in KNOWN_ARMS else 999
        return (a_idx, str(r.ablation), arm_idx, str(r.arm))

    records.sort(key=_sort_key)
    return records


def summarize(records: List[ArmRecord], run_root: str) -> Dict[str, Any]:
    # Build compact summary per (ablation, arm)
    per: Dict[str, Dict[str, Any]] = {}
    overall = {
        "run_root": run_root,
        "counts": {"arms": 0, "with_audit": 0, "with_telemetry": 0, "with_verdict": 0},
        "prereg_all_pass": None,
        "dynamics_stateful_all": None,
        "notes": [],
    }

    prereg_pass_flags = []
    stateful_ok_flags = []

    for r in records:
        key = f"{r.ablation}/{r.arm}"
        # prereg keys (locked gate) live under criteria/metrics
        prereg_pick = {
            "final_verdict": _get(r.prereg, "final_verdict"),
            "C1_psuccess": _get(r.prereg, "criteria", "C1_psuccess"),
            "C2_mad": _get(r.prereg, "criteria", "C2_mad"),
            "C3_thirdarm": _get(r.prereg, "criteria", "C3_thirdarm"),
            "rank_corr_abs": _get(r.prereg, "metrics", "A1_B2_vs_A1_B3", "rank_corr_abs"),
            "mad_rank_corr": _get(r.prereg, "metrics", "A1_B2_vs_A1_B3", "mad_rank_corr"),
            "third_rank_corr_b2_a23": _get(r.prereg, "metrics", "third_arm_A2_B3", "rank_corr_b2_a23"),
            "third_rank_corr_b3_a23": _get(r.prereg, "metrics", "third_arm_A2_B3", "rank_corr_b3_a23"),
            "third_top_all_match": _get(r.prereg, "metrics", "third_arm_A2_B3", "top_all_match"),
        }

        # audit keys (layer-b)
        audit_pick = {
            "stateful_steps_total": _get(r.audit, "stateful_steps_total"),
            "drift_fit_baseline": _get(r.audit, "drift_fit_baseline"),
            "residual_summary_by_setting": _get(r.audit, "residual_summary_by_setting"),
            "anti_cancel": _get(r.audit, "anti_cancel"),
        }

        # telemetry keys (integrity)
        telem_pick = {
            "ablation": _get(r.telemetry, "ablation"),
            "prereg_observable": _get(r.telemetry, "prereg_observable"),
            "drift_state_mode": _get(r.telemetry, "drift_state_mode"),
            "internal_dynamics_used": _get(r.telemetry, "dynamics", "internal_dynamics_used"),
            "thread_env_used": _get(r.telemetry, "dynamics", "thread_env_used"),
            "stateful_steps_total": _get(r.telemetry, "dynamics", "stateful_steps_total"),
            "scan_series_required": _get(r.telemetry, "integrity", "scan_series_required"),
        }

        # Determine booleans robustly
        fv = prereg_pick.get("final_verdict", None)
        prereg_pass = (str(fv).upper() == "PASS")
        if fv is not None:
            prereg_pass_flags.append(prereg_pass)

        steps = telem_pick.get("stateful_steps_total", None)
        # Expected: internal_only/full => steps>0; thread_only => steps==0
        expected_stateful = (r.ablation != "thread_only")
        if isinstance(steps, (int, float)):
            stateful_ok_flags.append((steps > 0) if expected_stateful else (steps == 0))

        per[key] = {
            "paths": {
                "folder": _relpath(r.folder, run_root),
                "verdict": _relpath(r.verdict_path, run_root) if r.verdict_path else None,
                "audit": _relpath(r.audit_path, run_root) if r.audit_path else None,
                "telemetry": _relpath(r.telemetry_path, run_root) if r.telemetry_path else None,
                "drift_common_csv": _relpath(r.drift_csv, run_root) if r.drift_csv else None,
                "residuals_csv": _relpath(r.residuals_csv, run_root) if r.residuals_csv else None,
            },
            "prereg": prereg_pick,
            "audit": audit_pick,
            "telemetry": telem_pick,
            "derived": {
                "prereg_pass": prereg_pass if fv is not None else None,
                "stateful_steps": steps,
                "stateful_expected": expected_stateful,
                "stateful_ok": (stateful_ok_flags[-1] if (isinstance(steps, (int, float))) else None),
            },
        }

    overall["counts"]["arms"] = len(per)
    overall["counts"]["with_audit"] = sum(1 for k, v in per.items() if v["paths"]["audit"])
    overall["counts"]["with_telemetry"] = sum(1 for k, v in per.items() if v["paths"]["telemetry"])
    overall["counts"]["with_verdict"] = sum(1 for k, v in per.items() if v["paths"]["verdict"])

    overall["prereg_all_pass"] = (all(prereg_pass_flags) if prereg_pass_flags else None)
    overall["dynamics_stateful_all"] = (all(stateful_ok_flags) if stateful_ok_flags else None)

    return {"overall": overall, "per_arm": per}


def render_markdown(summary: Dict[str, Any]) -> str:
    overall = summary["overall"]
    per_arm = summary["per_arm"]

    lines: List[str] = []
    lines.append("# Dynamics Integrity Summary")
    lines.append("")
    lines.append(f"- Run root: `{overall['run_root']}`")
    lines.append(f"- Arms found: **{overall['counts']['arms']}** (verdict: {overall['counts']['with_verdict']}, audit: {overall['counts']['with_audit']}, telemetry: {overall['counts']['with_telemetry']})")
    lines.append(f"- Prereg all PASS: **{overall['prereg_all_pass']}**")
    lines.append(f"- Dynamics stateful all: **{overall['dynamics_stateful_all']}**")
    lines.append("")

    # Group keys by ablation
    by_ablation: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
    for k, v in per_arm.items():
        ablation = k.split("/")[0] if "/" in k else "unknown"
        by_ablation.setdefault(ablation, []).append((k, v))

    for ablation in sorted(by_ablation.keys()):
        lines.append(f"## {ablation}")
        lines.append("")
        lines.append("| Arm | Prereg | C1 | C2 | C3 | rank_corr_abs | third b2 | third b3 | stateful_steps | stateful_ok | anti_cancel_rankcorr |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

        rows = by_ablation[ablation]
        # stable order: known arms first
        def arm_order(key: str) -> int:
            arm = key.split("/", 1)[1] if "/" in key else key
            return KNOWN_ARMS.index(arm) if arm in KNOWN_ARMS else 999

        rows.sort(key=lambda kv: arm_order(kv[0]))

        for key, v in rows:
            arm = key.split("/", 1)[1] if "/" in key else key
            p = v["prereg"]
            t = v["telemetry"]
            a = v["audit"]
            derived = v["derived"]

            def fmt(x):
                if x is None:
                    return ""
                if isinstance(x, bool):
                    return "True" if x else "False"
                if isinstance(x, (int, float)):
                    # avoid noisy long floats
                    return f"{x:.6g}"
                return str(x)

            anti = None
            if isinstance(a.get("anti_cancel"), dict):
                anti = a["anti_cancel"].get("rank_corr_raw_vs_corrected")
            lines.append(
                "| "
                + " | ".join(
                    [
                        arm,
                        fmt(p.get("final_verdict")),
                        fmt(p.get("C1_psuccess")),
                        fmt(p.get("C2_mad")),
                        fmt(p.get("C3_thirdarm")),
                        fmt(p.get("rank_corr_abs")),
                        fmt(p.get("third_rank_corr_b2_a23")),
                        fmt(p.get("third_rank_corr_b3_a23")),
                        fmt(derived.get("stateful_steps")),
                        fmt(derived.get("stateful_ok")),
                        fmt(anti),
                    ]
                )
                + " |"
            )

        lines.append("")
        # paths block
        lines.append("### Files")
        lines.append("")
        for key, v in rows:
            arm = key.split("/", 1)[1] if "/" in key else key
            paths = v["paths"]
            lines.append(f"- **{arm}**")
            lines.append(f"  - folder: `{paths['folder']}`")
            if paths["verdict"]:
                lines.append(f"  - prereg verdict: `{paths['verdict']}`")
            if paths["audit"]:
                lines.append(f"  - audit: `{paths['audit']}`")
            if paths["telemetry"]:
                lines.append(f"  - telemetry: `{paths['telemetry']}`")
            if paths["drift_common_csv"]:
                lines.append(f"  - drift_common.csv: `{paths['drift_common_csv']}`")
            if paths["residuals_csv"]:
                lines.append(f"  - residuals.csv: `{paths['residuals_csv']}`")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_id", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out_json", default="")
    ap.add_argument("--out_md", default="")
    args = ap.parse_args()

    run_root = find_run_root(args.root, args.run_id)
    records = collect_arm_records(run_root)

    if not records:
        print("No records found under:", run_root)
        return

    summary = summarize(records, run_root)
    md = render_markdown(summary)

    # Default output path: out/MS/<run_id> if exists, else run_root
    default_dir = os.path.join(args.root, "out", "MS", args.run_id)
    out_dir = default_dir if os.path.isdir(default_dir) else run_root
    os.makedirs(out_dir, exist_ok=True)

    out_json = args.out_json or os.path.join(out_dir, "DYNAMICS_INTEGRITY_SUMMARY.json")
    out_md = args.out_md or os.path.join(out_dir, "DYNAMICS_INTEGRITY_SUMMARY.md")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)

    print("=== DYNAMICS INTEGRITY AGGREGATOR v1 ===")
    print("run_id :", args.run_id)
    print("run_root:", run_root)
    print("wrote  :", out_json)
    print("wrote  :", out_md)


if __name__ == "__main__":
    main()