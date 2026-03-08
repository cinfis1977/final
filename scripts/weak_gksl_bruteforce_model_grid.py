from __future__ import annotations

import argparse
import csv
import itertools
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Result:
    thread_weight_app: float
    thread_weight_dis: float
    chi2_geo_total: float
    delta_total: float
    pos_channels: int
    exit_code: int
    out_csv: Path
    stdout_path: Path
    cmd_path: Path


def parse_totals(stdout_text: str) -> tuple[float, float, int]:
    chi2_geo = None
    delta = None
    pos = 0
    for line in stdout_text.splitlines():
        if line.startswith("- T2K"):
            # last token is dchi2
            parts = [p for p in line.split() if p]
            try:
                d = float(parts[-1])
            except Exception:
                continue
            if d > 0:
                pos += 1
        if line.startswith("TOTAL chi2_GEO"):
            try:
                chi2_geo = float(line.split("=")[-1].strip())
            except Exception:
                pass
        if line.startswith("Delta chi2"):
            try:
                delta = float(line.split("=")[-1].strip())
            except Exception:
                pass
    if chi2_geo is None or delta is None:
        raise RuntimeError("Failed to parse totals from stdout")
    return float(chi2_geo), float(delta), int(pos)


def main() -> int:
    ap = argparse.ArgumentParser(description="Brute-force small WEAK GKSL model grid (NOTE: this is tuning)")
    ap.add_argument("--python", required=True, help="Path to venv python.exe")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--epsilon", type=float, default=0.5)
    ap.add_argument("--max_keep", type=int, default=5)
    ap.add_argument(
        "--grid_app",
        default="0,0.2,0.5,1.0",
        help="Comma-separated thread_weight_app grid values",
    )
    ap.add_argument(
        "--grid_dis",
        default="0.5,1.0,1.5",
        help="Comma-separated thread_weight_dis grid values",
    )
    args = ap.parse_args()

    py = Path(args.python)
    pack = Path(args.pack)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Fixed baseline params from run05.
    base = [
        "nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py",
        "--pack",
        str(pack),
        "--kernel",
        "rt",
        "--k_rt",
        "180",
        "--A",
        "-0.002",
        "--alpha",
        "0.7",
        "--n",
        "0",
        "--E0",
        "1",
        "--omega0_geom",
        "fixed",
        "--L0_km",
        "295",
        "--phi",
        "1.57079632679",
        "--zeta",
        "0.05",
        "--rho",
        "2.6",
        "--kappa_gate",
        "0",
        "--T0",
        "1",
        "--mu",
        "0",
        "--eta",
        "0",
        "--bin_shift_app",
        "0",
        "--bin_shift_dis",
        "0",
        "--breath_B",
        "0.3",
        "--breath_w0",
        "0.00387850944887629",
        "--breath_gamma",
        "0.2",
        "--thread_C",
        "1.0",
        "--thread_w0",
        "0.00387850944887629",
        "--thread_gamma",
        "0.2",
        "--flavors",
        "3",
        "--steps",
        "700",
        "--chi2_mode",
        "poisson_dev",
        "--poisson_shape",
        "none",
    ]

    def parse_grid(s: str) -> list[float]:
        out: list[float] = []
        for tok in (t.strip() for t in str(s).split(",")):
            if not tok:
                continue
            out.append(float(tok))
        if not out:
            raise ValueError("Empty grid")
        return out

    grid_app = parse_grid(args.grid_app)
    grid_dis = parse_grid(args.grid_dis)

    results: list[Result] = []

    for w_app, w_dis in itertools.product(grid_app, grid_dis):
        tag = f"wapp_{w_app:.3g}__wdis_{w_dis:.3g}".replace(".", "p")
        ev_dir = out_dir / tag
        art_dir = ev_dir / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)

        out_csv = art_dir / "out.csv"
        stdout_path = ev_dir / "terminal_output.txt"
        cmd_path = ev_dir / "command.txt"

        cmd = [str(py)] + base + [
            "--thread_weight_app",
            str(w_app),
            "--thread_weight_dis",
            str(w_dis),
            "--out",
            str(out_csv),
        ]

        cmd_path.write_text(" ".join(cmd) + "\n", encoding="utf-8")

        proc = subprocess.run(cmd, capture_output=True, text=True)
        stdout_text = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        stdout_path.write_text(stdout_text + f"\nEXIT_CODE: {proc.returncode}\n", encoding="utf-8")

        try:
            chi2_geo, delta, pos = parse_totals(stdout_text)
        except Exception:
            chi2_geo, delta, pos = float("nan"), float("nan"), 0

        results.append(
            Result(
                thread_weight_app=float(w_app),
                thread_weight_dis=float(w_dis),
                chi2_geo_total=float(chi2_geo),
                delta_total=float(delta),
                pos_channels=int(pos),
                exit_code=int(proc.returncode),
                out_csv=out_csv,
                stdout_path=stdout_path,
                cmd_path=cmd_path,
            )
        )

    # Sort by: require delta>=epsilon and pos>=3, then minimize chi2_geo
    eps = float(args.epsilon)

    def ok(r: Result) -> bool:
        return (r.exit_code == 0) and (r.delta_total >= eps) and (r.pos_channels >= 3)

    sorted_results = sorted(
        results,
        key=lambda r: (
            0 if ok(r) else 1,
            r.chi2_geo_total if r.chi2_geo_total == r.chi2_geo_total else 1e99,
            -r.delta_total,
        ),
    )

    # Write summary
    summary_path = out_dir / "summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "thread_weight_app",
            "thread_weight_dis",
            "chi2_geo_total",
            "delta_total",
            "pos_channels",
            "exit_code",
            "ok",
            "evidence_dir",
        ])
        for r in sorted_results:
            w.writerow([
                r.thread_weight_app,
                r.thread_weight_dis,
                r.chi2_geo_total,
                r.delta_total,
                r.pos_channels,
                r.exit_code,
                ok(r),
                str(r.stdout_path.parent),
            ])

    # Prune evidence: keep only best N + any failures
    keep = set()
    for r in sorted_results[: int(args.max_keep)]:
        keep.add(r.stdout_path.parent)
    for r in sorted_results:
        if r.exit_code != 0:
            keep.add(r.stdout_path.parent)

    for p in out_dir.iterdir():
        if p.is_dir() and p not in keep:
            # remove directories to keep repo light
            for child in p.rglob("*"):
                try:
                    if child.is_file():
                        child.unlink()
                except Exception:
                    pass
            try:
                for child in sorted(p.rglob("*"), reverse=True):
                    if child.is_dir():
                        child.rmdir()
                p.rmdir()
            except Exception:
                pass

    best = sorted_results[0]
    print(f"BEST: w_app={best.thread_weight_app} w_dis={best.thread_weight_dis} chi2_geo={best.chi2_geo_total} delta={best.delta_total} pos={best.pos_channels} rc={best.exit_code}")
    print(f"SUMMARY: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
