#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


RUNS = [
    "A1_B2_ModeA",
    "A1_B2_ModeB",
    "A1_B2_direct_ModeB_holdout",
    "Combined_A1_B2_plus_holdout",
]


def _to_bool_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().eq("true")


def _median(vals: List[float]) -> float:
    if not vals:
        return float("nan")
    x = sorted(vals)
    n = len(x)
    if n % 2 == 1:
        return float(x[n // 2])
    return 0.5 * float(x[n // 2 - 1] + x[n // 2])


def _anchor(comp: pd.DataFrame, a: str, b: str) -> str:
    m = (
        ((comp["target_a"].astype(str) == a) & (comp["target_b"].astype(str) == b))
        | ((comp["target_a"].astype(str) == b) & (comp["target_b"].astype(str) == a))
    )
    sub = comp[m]
    if sub.empty:
        return "missing"
    r = sub.iloc[0]
    return (
        f"{r.get('classification_track8','')}->{r.get('classification_rebuilt','')};"
        f"{r.get('boundary_confidence_track8','')}->{r.get('boundary_confidence_rebuilt','')}"
    )


def _verdict_from_md(path: Path) -> str:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"\*\*(PASS|SPLIT|FAIL)-DIAGNOSTIC-REBUILD\*\*", txt)
    if not m:
        return "UNKNOWN"
    return f"{m.group(1)}-DIAGNOSTIC-REBUILD"


def _shell_distribution(rebuilt: pd.DataFrame, shell: str) -> str:
    sub = rebuilt[rebuilt["pair_shell"].astype(str) == shell].copy()
    stable = int((sub["classification"] == "STABLE-INTERMEDIATE-CANDIDATE").sum())
    rep = int((sub["classification"] == "REPULSIVE").sum())
    inc = int((sub["classification"] == "INCONCLUSIVE").sum())
    return f"S:{stable} R:{rep} I:{inc}"


def summarize_run(base: Path, run: str) -> Dict[str, object]:
    comp = pd.read_csv(base / f"rebuilt_vs_track8_comparison_{run}.csv")
    rebuilt = pd.read_csv(base / f"rebuilt_two_center_pair_metrics_{run}.csv")
    verdict_md = base / f"rebuilt_two_center_verdict_{run}.md"

    class_changes = int(_to_bool_series(comp["classification_changed"]).sum())
    conf_changes = int(_to_bool_series(comp["boundary_confidence_changed"]).sum())
    matched_pairs = int((comp["pair_presence"].astype(str) == "matched").sum())

    adj = rebuilt[rebuilt["pair_shell"].astype(str) == "adjacent"].copy()
    nn = rebuilt[rebuilt["pair_shell"].astype(str) == "next_nearest"].copy()
    adj_stable_frac = float((adj["classification"] == "STABLE-INTERMEDIATE-CANDIDATE").mean()) if len(adj) else float("nan")
    nn_stable_frac = float((nn["classification"] == "STABLE-INTERMEDIATE-CANDIDATE").mean()) if len(nn) else float("nan")
    adj_med_delta = _median([float(x) for x in adj["delta_mz"].tolist()]) if len(adj) else float("nan")
    nn_med_delta = _median([float(x) for x in nn["delta_mz"].tolist()]) if len(nn) else float("nan")
    mono_ok = bool((adj_stable_frac >= nn_stable_frac) and (adj_med_delta <= nn_med_delta))

    return {
        "run": run,
        "matched_pairs": matched_pairs,
        "classification_changes": class_changes,
        "confidence_changes": conf_changes,
        "shell_adj": _shell_distribution(rebuilt, "adjacent"),
        "shell_next": _shell_distribution(rebuilt, "next_nearest"),
        "shell_monotonicity": "OK" if mono_ok else "BROKEN",
        "anchor_t02_t03": _anchor(comp, "T02", "T03"),
        "anchor_t12_t07": _anchor(comp, "T12", "T07"),
        "verdict": _verdict_from_md(verdict_md),
    }


def build_rollup(base: Path) -> str:
    rows = [summarize_run(base, r) for r in RUNS]

    lines: List[str] = []
    lines.append("# Arm-by-Arm Frozen Rebuild Rollup")
    lines.append("")
    lines.append("| run | matched_pairs | class_changes | conf_changes | shell_monotonicity | anchor T02<->T03 | anchor T12<->T07 | verdict |")
    lines.append("|---|---:|---:|---:|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {r['run']} | {r['matched_pairs']} | {r['classification_changes']} | {r['confidence_changes']} | "
            f"{r['shell_monotonicity']} | {r['anchor_t02_t03']} | {r['anchor_t12_t07']} | {r['verdict']} |"
        )

    lines.append("")
    lines.append("## Shell Distribution")
    for r in rows:
        lines.append(f"- {r['run']}: adjacent({r['shell_adj']}), next_nearest({r['shell_next']})")

    lines.append("")
    lines.append("## Direct Answer")
    arm_rows = [x for x in rows if x["run"] != "Combined_A1_B2_plus_holdout"]
    arm_ok = all(
        (x["classification_changes"] == 0)
        and (x["shell_monotonicity"] == "OK")
        and (x["verdict"] == "PASS-DIAGNOSTIC-REBUILD")
        for x in arm_rows
    )
    if arm_ok:
        lines.append("- Not only a pooled-data effect: the same skeleton survives in each arm individually.")
    else:
        lines.append("- Evidence is mixed: pooled-data behavior is stronger than at least one individual arm.")

    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Build rollup markdown from 4 arm-by-arm frozen rebuild outputs.")
    ap.add_argument("--base_dir", required=True)
    ap.add_argument("--out_md", required=True)
    args = ap.parse_args()

    base = Path(args.base_dir).resolve()
    out_md = Path(args.out_md).resolve()
    out_md.parent.mkdir(parents=True, exist_ok=True)

    md = build_rollup(base)
    out_md.write_text(md, encoding="utf-8")
    print(f"WROTE {out_md}")


if __name__ == "__main__":
    main()
