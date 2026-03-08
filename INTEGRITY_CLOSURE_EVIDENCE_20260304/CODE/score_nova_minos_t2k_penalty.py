#!/usr/bin/env python3
# score_nova_minos_t2k_penalty.py
#
# One-shot scorer:
#   total_score = (dchi2_NOvA + dchi2_MINOS) - (T2K dchi2 penalty)
#
# dchi2 pack is parsed from runner stdout (expects "Delta chi2 = ... = <float>").
# Penalty is parsed from t2k_penalty_cli stdout (expects "TOTAL dchi2 penalty = <float>").
#
# Works on Windows (default null device: NUL).

from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional


_FLOAT_RE = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"

def _parse_pack_dchi2(stdout: str) -> float:
    # Prefer the canonical line:
    #   Delta chi2 = chi2_SM - chi2_GEO = 12.588
    m = re.search(r"Delta\s+chi2\s*=.*?=\s*(%s)\s*$" % _FLOAT_RE, stdout, flags=re.MULTILINE)
    if m:
        return float(m.group(1))
    # Fallback patterns seen in older tools
    m = re.search(r"\bdchi2\s*=\s*(%s)\b" % _FLOAT_RE, stdout)
    if m:
        return float(m.group(1))
    m = re.search(r"\bDelta\s*chi2\b.*?(%s)\b" % _FLOAT_RE, stdout)
    if m:
        return float(m.group(1))
    raise RuntimeError("Could not parse pack dchi2 from runner stdout. Expected a 'Delta chi2 = ... = <number>' line.")

def _parse_penalty(stdout: str) -> float:
    """
    Parse penalty CLI output.

    Supported canonical lines (ASCII-only preferred):
      TOTAL_dchi2_penalty = <number>
      TOTAL dchi2 penalty = <number>

    Legacy (may appear if user kept old CLI):
      TOTAL dchi2 penalty = <number>
    """
    # 1) New canonical (preferred)
    m = re.search(r"TOTAL[_ ]dchi2[_ ]penalty\s*=\s*(%s)\s*$" % _FLOAT_RE, stdout, flags=re.MULTILINE | re.IGNORECASE)
    if m:
        return float(m.group(1))
    # 2) Older ASCII fallback
    m = re.search(r"TOTAL\s+dchi2\s+penalty\s*=\s*(%s)\s*$" % _FLOAT_RE, stdout, flags=re.MULTILINE | re.IGNORECASE)
    if m:
        return float(m.group(1))
    # 3) Legacy unicode
    m = re.search(r"TOTAL\s+dchi2\s+penalty\s*=\s*(%s)\s*$" % _FLOAT_RE, stdout, flags=re.MULTILINE)
    if m:
        return float(m.group(1))
    raise RuntimeError("Could not parse T2K penalty from stdout. Expected 'TOTAL_dchi2_penalty = <number>'.")

def _run(cmd: List[str], cwd: Optional[Path]=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)

def run_pack(runner: Path, pack: Path, null_device: str, runner_args: List[str]) -> float:
    cmd = [sys.executable, str(runner), "--pack", str(pack), "--out", null_device] + runner_args
    cp = _run(cmd)
    if cp.returncode != 0:
        tail = (cp.stdout or "")[-4000:] + "\n" + (cp.stderr or "")[-4000:]
        raise RuntimeError(f"Runner failed for {pack.name} (code {cp.returncode}). Output tail:\n{tail}")
    return _parse_pack_dchi2(cp.stdout)

def run_t2k_penalty(penalty_cli: Path, profiles: Path, hierarchy: str, rc: str,
                    s2th23: float, dm2: float, dcp: float) -> float:
    cmd = [
        sys.executable, str(penalty_cli),
        "--profiles", str(profiles),
        "--hierarchy", hierarchy,
        "--rc", rc,
        "--s2th23", str(s2th23),
        "--dm2", str(dm2),
        "--dcp", str(dcp),
    ]
    cp = _run(cmd)
    if cp.returncode != 0:
        tail = (cp.stdout or "")[-4000:] + "\n" + (cp.stderr or "")[-4000:]
        raise RuntimeError(f"t2k_penalty_cli failed (code {cp.returncode}). Output tail:\n{tail}")
    return _parse_penalty(cp.stdout)

def main() -> int:
    ap = argparse.ArgumentParser(description="Compute (dchi2_NOvA + dchi2_MINOS) - T2K_penalty in one shot.")
    ap.add_argument("--runner", required=True, help="Path to nova_mastereq_forward_kernel_BREATH_THREAD_v2.py (or compatible).")
    ap.add_argument("--pack_nova", required=True, help="Path to nova_channels.json")
    ap.add_argument("--pack_minos", required=True, help="Path to minos_channels.json")
    ap.add_argument("--null_device", default="NUL", help="Windows null device (default: NUL).")
    ap.add_argument("--runner_args", required=True, help="Runner args as ONE quoted string (everything after --out). Example: \"--kernel rt ... --thread_weight_dis 1\"")

    ap.add_argument("--t2k_penalty_cli", default="t2k_penalty_cli.py", help="Path to t2k_penalty_cli.py (default: ./t2k_penalty_cli.py).")
    ap.add_argument("--t2k_profiles", required=True, help="Path to t2k_frequentist_profiles.json produced by extractor.")
    ap.add_argument("--hierarchy", default="NH", choices=["NH","IH"])
    ap.add_argument("--rc", default="wRC", choices=["wRC","woRC"])
    ap.add_argument("--s2th23", type=float, required=True)
    ap.add_argument("--dm2", type=float, required=True)
    ap.add_argument("--dcp", type=float, required=True)

    args = ap.parse_args()

    runner = Path(args.runner)
    pack_nova = Path(args.pack_nova)
    pack_minos = Path(args.pack_minos)
    penalty_cli = Path(args.t2k_penalty_cli)
    profiles = Path(args.t2k_profiles)

    # Split runner_args like a shell would (simple quotes supported).
    # We avoid shlex on Windows edge-cases by implementing a small parser.
    def split_args(s: str) -> List[str]:
        out: List[str] = []
        cur = ""
        in_s = False
        in_d = False
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == "'" and not in_d:
                in_s = not in_s
                i += 1
                continue
            if ch == '"' and not in_s:
                in_d = not in_d
                i += 1
                continue
            if ch.isspace() and not in_s and not in_d:
                if cur:
                    out.append(cur)
                    cur = ""
                i += 1
                continue
            cur += ch
            i += 1
        if cur:
            out.append(cur)
        return out

    runner_args = split_args(args.runner_args)

    # Run packs
    dchi2_nova = run_pack(runner, pack_nova, args.null_device, runner_args)
    dchi2_minos = run_pack(runner, pack_minos, args.null_device, runner_args)

    # Penalty
    pen = run_t2k_penalty(penalty_cli, profiles, args.hierarchy, args.rc, args.s2th23, args.dm2, args.dcp)

    total = (dchi2_nova + dchi2_minos) - pen

    print("============================================================")
    print("TOTAL SCORE (NOvA + MINOS - T2K penalty)")
    print("============================================================")
    print(f"dchi2_NOvA   = {dchi2_nova:.6f}")
    print(f"dchi2_MINOS  = {dchi2_minos:.6f}")
    print(f"T2K penalty= {pen:.6f}")
    print("------------------------------------------------------------")
    print(f"TOTAL SCORE= {total:.6f}")
    print("============================================================")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
