#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STRONG C5A.1 paper-run mode.

Single-command driver that runs the STRONG C4 pack-ingestion runner on the C5A
real-data packs and writes deterministic artifacts under out/.

This is a reproducibility/runbook deliverable (IO closure + anti-fallback), not
an accuracy/fit claim.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _run_c4(pack_path: Path, *, out_csv: Path, out_json: Path, poison: bool) -> dict[str, Any]:
    env = dict(os.environ)
    if poison:
        env["STRONG_C4_POISON_PDG_CALLS"] = "1"

    cmd = [
        sys.executable,
        str(_repo_root() / "strong_amplitude_pack_hepdata_c4.py"),
        "--pack",
        str(pack_path),
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
    ]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            "C5A.1 paper-run failed\n"
            f"pack={pack_path}\n"
            f"rc={r.returncode}\n"
            f"STDOUT:\n{r.stdout}\n"
            f"STDERR:\n{r.stderr}\n"
        )

    return json.loads(out_json.read_text(encoding="utf-8"))


def _format_summary_block(label: str, summary: dict[str, Any]) -> str:
    chi2 = summary.get("chi2", {})
    tel = chi2.get("telemetry", {}) if isinstance(chi2, dict) else {}
    io = summary.get("io", {})
    anti = summary.get("anti_fallback", {})

    # Backward/forward compatible chi2 view
    chi2_total = chi2.get("total") if isinstance(chi2, dict) else None
    chi2_sm = chi2.get("sm") if isinstance(chi2, dict) else None
    chi2_geo = chi2.get("geo") if isinstance(chi2, dict) else None
    chi2_delta = chi2.get("delta") if isinstance(chi2, dict) else None

    lines: list[str] = []
    lines.append(f"## {label}")
    lines.append("")
    lines.append(f"- pack: {summary.get('pack', {}).get('path')}")
    if chi2_total is not None:
        lines.append(f"- chi2.total: {chi2_total}")
    if chi2_sm is not None or chi2_geo is not None or chi2_delta is not None:
        lines.append(f"- chi2.sm: {chi2_sm}")
        lines.append(f"- chi2.geo: {chi2_geo}")
        lines.append(f"- chi2.delta: {chi2_delta}")
    lines.append(f"- chi2.ndof: {chi2.get('ndof') if isinstance(chi2, dict) else None}")
    lines.append(f"- chi2.kind.sigma_tot_mb: {tel.get('sigma_tot_mb', {}).get('kind') if isinstance(tel, dict) else None}")
    lines.append(f"- chi2.kind.rho: {tel.get('rho', {}).get('kind') if isinstance(tel, dict) else None}")
    lines.append(f"- poison_active: {anti.get('pdg_call_poison_active')}")
    lines.append(f"- amplitude_core_used: {summary.get('amplitude_core_used')}")
    lines.append(f"- pdg_baseline_used: {summary.get('pdg_baseline_used')}")
    lines.append(f"- data_loaded_from_paths: {io.get('data_loaded_from_paths')}")
    lines.append(f"- data_csv: {io.get('data_csv')}")
    lines.append(f"- cov_sigma_tot_csv: {io.get('cov_sigma_tot_csv')}")
    lines.append(f"- cov_rho_csv: {io.get('cov_rho_csv')}")
    lines.append(f"- stability_not_accuracy: {summary.get('framing', {}).get('stability_not_accuracy')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out_dir",
        default=str(_repo_root() / "out" / "strong_c5a"),
        help="Output directory (default: out/strong_c5a)",
    )
    ap.add_argument(
        "--packs_dir",
        default=str(_repo_root() / "integration_artifacts" / "mastereq" / "packs" / "strong_c5a"),
        help="Directory containing C5A packs",
    )
    ap.add_argument(
        "--no_poison",
        action="store_true",
        help="Disable call-poison (not recommended for evidence runs)",
    )
    ap.add_argument(
        "--A",
        type=float,
        default=0.0,
        help=(
            "Locked global GEO amplitude to test against SM. "
            "The runner evaluates SM with A=0.0 and GEO with this A (same packs/cov)."
        ),
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    packs_dir = Path(args.packs_dir)
    poison = not bool(args.no_poison)
    A_locked = float(args.A)

    pack_sigma = (packs_dir / "pdg_sigma_tot_pack.json").resolve()
    pack_rho = (packs_dir / "pdg_rho_pack.json").resolve()

    out_dir.mkdir(parents=True, exist_ok=True)

    sigma_csv = out_dir / "sigma_tot_pred.csv"
    sigma_json = out_dir / "sigma_tot_summary.json"
    rho_csv = out_dir / "rho_pred.csv"
    rho_json = out_dir / "rho_summary.json"
    report_md = out_dir / "paper_run_report.md"

    # Run each pack twice: SM (A=0) and GEO (A=A_locked)
    tmp_dir = (out_dir / "_tmp_packs")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    def _rewrite_pack_A(src_pack: Path, *, A: float, label: str) -> Path:
        pack = json.loads(src_pack.read_text(encoding="utf-8"))
        # Make pack relocatable: resolve any relative CSV paths against the original pack directory.
        paths = pack.get("paths")
        if isinstance(paths, dict):
            new_paths: dict[str, Any] = dict(paths)
            for k, v in list(paths.items()):
                if not isinstance(k, str) or not k.endswith("_csv"):
                    continue
                if not isinstance(v, str) or not v:
                    continue
                # If relative, resolve it against the *source* pack directory.
                p = Path(v)
                if not p.is_absolute():
                    new_paths[k] = str((src_pack.parent / p).resolve())
            pack["paths"] = new_paths

        geo = pack.get("geo")
        if not isinstance(geo, dict):
            geo = {}
        geo["A"] = float(A)
        pack["geo"] = geo
        outp = tmp_dir / f"{src_pack.stem}__{label}.json"
        outp.write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return outp

    def _merge_pred_csv(
        csv_sm: Path,
        csv_geo: Path,
        *,
        pred_col: str,
        out_csv: Path,
        suffix_sm: str,
        suffix_geo: str,
    ) -> None:
        df_sm = pd.read_csv(csv_sm)
        df_geo = pd.read_csv(csv_geo)
        if pred_col not in df_sm.columns or pred_col not in df_geo.columns:
            raise RuntimeError(f"Missing pred column '{pred_col}' in SM/GEO CSVs")

        base_cols = [c for c in df_sm.columns if c != pred_col]
        # Deterministic join: preserve SM row order.
        merged = df_sm[base_cols].copy()
        merged[pred_col + suffix_sm] = pd.to_numeric(df_sm[pred_col], errors="coerce")
        merged[pred_col + suffix_geo] = pd.to_numeric(df_geo[pred_col], errors="coerce")
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(out_csv, index=False)

    def _combined_summary(sm: dict[str, Any], geo: dict[str, Any]) -> dict[str, Any]:
        chi_sm = float(sm.get("chi2", {}).get("total")) if sm.get("chi2", {}).get("total") is not None else None
        chi_geo = float(geo.get("chi2", {}).get("total")) if geo.get("chi2", {}).get("total") is not None else None
        ndof = sm.get("chi2", {}).get("ndof")

        out: dict[str, Any] = {}
        out["pack"] = sm.get("pack") or geo.get("pack")
        out["amplitude_core_used"] = True
        out["pdg_baseline_used"] = False
        out["anti_fallback"] = sm.get("anti_fallback") or geo.get("anti_fallback")
        out["io"] = sm.get("io") or geo.get("io")
        out["pars"] = geo.get("pars") or sm.get("pars")
        out["geo"] = {"A_locked": A_locked, "sm_A": 0.0}
        out["chi2"] = {
            "sm": chi_sm,
            "geo": chi_geo,
            "delta": (chi_sm - chi_geo) if (chi_sm is not None and chi_geo is not None) else None,
            "ndof": ndof,
        }
        out["framing"] = {
            "stability_not_accuracy": True,
            "note": "This paper run evaluates SM vs GEO using the same packs/cov; it is an IO/closure + anti-fallback artifact, not a physical-accuracy claim.",
        }
        return out

    # Sigma_tot
    pack_sigma_sm = _rewrite_pack_A(pack_sigma, A=0.0, label="sm")
    pack_sigma_geo = _rewrite_pack_A(pack_sigma, A=A_locked, label="geo")

    sigma_sm_csv = out_dir / "_sigma_tot_sm.csv"
    sigma_sm_json = out_dir / "_sigma_tot_sm_summary.json"
    sigma_geo_csv = out_dir / "_sigma_tot_geo.csv"
    sigma_geo_json = out_dir / "_sigma_tot_geo_summary.json"

    s_sigma_sm = _run_c4(pack_sigma_sm, out_csv=sigma_sm_csv, out_json=sigma_sm_json, poison=poison)
    s_sigma_geo = _run_c4(pack_sigma_geo, out_csv=sigma_geo_csv, out_json=sigma_geo_json, poison=poison)
    _merge_pred_csv(sigma_sm_csv, sigma_geo_csv, pred_col="sigma_tot_pred_mb", out_csv=sigma_csv, suffix_sm="_sm", suffix_geo="_geo")
    sigma_json.write_text(json.dumps(_combined_summary(s_sigma_sm, s_sigma_geo), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Rho
    pack_rho_sm = _rewrite_pack_A(pack_rho, A=0.0, label="sm")
    pack_rho_geo = _rewrite_pack_A(pack_rho, A=A_locked, label="geo")

    rho_sm_csv = out_dir / "_rho_sm.csv"
    rho_sm_json = out_dir / "_rho_sm_summary.json"
    rho_geo_csv = out_dir / "_rho_geo.csv"
    rho_geo_json = out_dir / "_rho_geo_summary.json"

    s_rho_sm = _run_c4(pack_rho_sm, out_csv=rho_sm_csv, out_json=rho_sm_json, poison=poison)
    s_rho_geo = _run_c4(pack_rho_geo, out_csv=rho_geo_csv, out_json=rho_geo_json, poison=poison)
    _merge_pred_csv(rho_sm_csv, rho_geo_csv, pred_col="rho_pred", out_csv=rho_csv, suffix_sm="_sm", suffix_geo="_geo")
    rho_json.write_text(json.dumps(_combined_summary(s_rho_sm, s_rho_geo), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Load combined summaries for report
    s_sigma = json.loads(sigma_json.read_text(encoding="utf-8"))
    s_rho = json.loads(rho_json.read_text(encoding="utf-8"))

    report_lines: list[str] = []
    report_lines.append("# STRONG C5A.1 paper run report")
    report_lines.append("")
    report_lines.append("This report is produced by `run_strong_c5a_paper_run.py`.")
    report_lines.append("It is an IO/closure + anti-fallback evidence artifact, not a physical-accuracy claim.")
    report_lines.append("")
    report_lines.append(f"- A_locked: {A_locked}")
    report_lines.append("")
    report_lines.append(_format_summary_block("Sigma_tot pack", s_sigma))
    report_lines.append(_format_summary_block("Rho pack", s_rho))

    report_md.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
