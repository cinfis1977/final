#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_rows(csv_path: Path) -> list[tuple[int, int, int, int]]:
    rows_raw: list[tuple[float, int, int, int, int]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows_raw.append((
                float(r["coinc_idx"]),
                int(r["a_set"]),
                int(r["b_set"]),
                int(r["a_out"]),
                int(r["b_out"]),
            ))
    rows_raw.sort(key=lambda x: x[0])
    return [(a, b, ao, bo) for _, a, b, ao, bo in rows_raw[1:]]


def _null_pvalue(rows: list[tuple[int, int, int, int]], trials: int, seed: int) -> dict[str, Any]:
    by: dict[tuple[int, int], list[tuple[int, int]]] = {(0, 0): [], (0, 1): [], (1, 0): [], (1, 1): []}
    for a, b, ao, bo in rows:
        by[(a, b)].append((ao, bo))

    rng = np.random.default_rng(seed)
    ao_by = {k: np.array([x[0] for x in v], dtype=int) for k, v in by.items()}
    bo_by = {k: np.array([x[1] for x in v], dtype=int) for k, v in by.items()}

    def _s_abs(bo_map: dict[tuple[int, int], np.ndarray]) -> float:
        Es: dict[tuple[int, int], float] = {}
        for k in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            ao = ao_by[k]
            bo = bo_map[k]
            npp = int(np.sum((ao == 1) & (bo == 1)))
            npm = int(np.sum((ao == 1) & (bo == -1)))
            nmp = int(np.sum((ao == -1) & (bo == 1)))
            nmm = int(np.sum((ao == -1) & (bo == -1)))
            n = npp + npm + nmp + nmm
            Es[k] = (npp + nmm - npm - nmp) / n if n > 0 else float("nan")
        s = Es[(0, 0)] + Es[(0, 1)] + Es[(1, 0)] - Es[(1, 1)]
        return float(abs(s))

    obs = _s_abs(bo_by)
    sims: list[float] = []
    for _ in range(int(trials)):
        shuf = {k: v.copy() for k, v in bo_by.items()}
        for v in shuf.values():
            rng.shuffle(v)
        sims.append(_s_abs(shuf))

    arr = np.array(sims, dtype=float)
    return {
        "null_trials": int(trials),
        "seed": int(seed),
        "observed_S_abs": float(obs),
        "null_mean_S_abs": float(np.mean(arr)),
        "null_p95_S_abs": float(np.quantile(arr, 0.95)),
        "null_pvalue_S_abs": float(np.mean(arr >= obs)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Paper-faithful NIST run4 CHSH audit runner")
    ap.add_argument("--in_csv", default=str(_repo_root() / "integration_artifacts" / "entanglement_photon_bridge" / "nist_run4_coincidences.csv"))
    ap.add_argument("--out_dir", default=str(_repo_root() / "out" / "entanglement_paper"))
    ap.add_argument("--prefix", default="nist_run4_chsh_audit_paper_v1")
    ap.add_argument("--null_trials", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20260307)
    args = ap.parse_args()

    repo = _repo_root()
    bridge = _load_module(
        "audit_nist_coinc_csv_bridgeE0_v1_DROPIN",
        repo / "integration_artifacts" / "entanglement_photon_bridge" / "audit_nist_coinc_csv_bridgeE0_v1_DROPIN.py",
    )

    in_csv = Path(args.in_csv).resolve()
    rows = _read_rows(in_csv)
    Es, combo_counts, combo_out_counts, s_signed, s_abs = bridge.chsh_from_rows(rows)
    null = _null_pvalue(rows, int(args.null_trials), int(args.seed))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / f"{args.prefix}_summary.json"
    report_path = out_dir / f"{args.prefix}_report.md"

    summary = {
        "runner": "run_entanglement_nist_run4_chsh_audit_paper_v1.py",
        "layer": "paper-faithful",
        "claim_boundary": {
            "does": "Runs the validated NIST run4 coincidence audit and reports E(a,b), CHSH S, and a no-fit null benchmark.",
            "does_not": "Does not claim a full first-principles dynamic derivation of Bell correlations from the unified model.",
        },
        "inputs": {
            "in_csv": str(in_csv),
            "sha256": _sha256(in_csv),
        },
        "counts": {f"{k[0]}{k[1]}": int(v) for k, v in combo_counts.items()},
        "outcomes": {f"{k[0]}{k[1]}": combo_out_counts[k] for k in combo_out_counts},
        "observables": {
            "E": {f"{k[0]}{k[1]}": float(Es[k]) for k in Es},
            "S_signed": float(s_signed),
            "S_abs": float(s_abs),
        },
        "null_benchmark": null,
        "no_fit_statement": "No parameter fit or tuning is performed in this runner.",
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Entanglement paper-faithful CHSH audit\n",
        f"- input CSV: {in_csv}\n",
        f"- sha256: `{summary['inputs']['sha256']}`\n",
        "\n## Observables\n",
        f"- S_signed = {s_signed:.12g}\n",
        f"- S_abs = {s_abs:.12g}\n",
        f"- null_pvalue_S_abs = {null['null_pvalue_S_abs']:.6g}\n",
        "\n## E(a,b)\n",
    ]
    for k in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        lines.append(f"- E{k} = {float(Es[k]):.12g}\n")
    lines.extend([
        "\n## Claim boundary\n",
        "- This is a validated Bell benchmark / coincidence audit path.\n",
        "- It does **not** claim a full dynamic derivation of Bell correlations.\n",
        "- No fitting or retuning was performed.\n",
    ])
    report_path.write_text("".join(lines), encoding="utf-8")

    print(f"[WROTE] {summary_path}")
    print(f"[WROTE] {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
