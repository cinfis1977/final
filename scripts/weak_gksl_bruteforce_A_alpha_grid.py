from __future__ import annotations

import argparse
import csv
import itertools
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Result:
    A: float
    weak_alpha_Etilt: float
    chi2_geo_total: float
    delta_total: float
    pos_channels: int
    exit_code: int
    stdout_path: Path
    cmd_path: Path
    out_csv: Path


def parse_totals(stdout_text: str) -> tuple[float, float, int]:
    chi2_geo = None
    delta = None
    pos = 0
    for line in stdout_text.splitlines():
        if line.startswith("- T2K"):
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


def parse_grid(s: str) -> list[float]:
    out: list[float] = []
    for tok in (t.strip() for t in str(s).split(",")):
        if not tok:
            continue
        out.append(float(tok))
    if not out:
        raise ValueError("Empty grid")
    return out


def parse_grid_file(path: Path) -> list[float]:
    txt = path.read_text(encoding="utf-8")
    # Allow comma/whitespace/newline separated floats, with optional # comments.
    vals: list[float] = []
    for raw_line in txt.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        for tok in line.replace(",", " ").split():
            vals.append(float(tok))
    if not vals:
        raise ValueError(f"Empty grid file: {path}")
    return vals


def safe_tag(label: str) -> str:
    return label.replace("-", "m").replace(".", "p")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Brute-force WEAK GKSL grid over A and weak_alpha_Etilt. "
            "Default intent is exploratory_tuning (NOT global calibration)."
        )
    )
    ap.add_argument("--python", required=True, help="Path to venv python.exe")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument(
        "--intent",
        default="exploratory_tuning",
        choices=["exploratory_tuning", "anchor_calibration"],
        help=(
            "exploratory_tuning: allow sector-specific knobs (e.g. weak_alpha_Etilt). "
            "anchor_calibration: only scan parameters declared global in the manifest; weak_alpha_Etilt must be fixed."
        ),
    )
    ap.add_argument(
        "--global_manifest",
        default=None,
        help="Optional path to global_parameter_manifest.json used to gate anchor_calibration.",
    )
    ap.add_argument("--epsilon", type=float, default=0.5)
    ap.add_argument("--max_keep", type=int, default=8)
    ap.add_argument("--grid_A", default="-0.004,-0.0035,-0.003,-0.0025,-0.002,-0.0015,-0.001,-0.0005,0")
    ap.add_argument("--grid_A_file", default=None, help="Optional path to a text file containing A grid values")
    ap.add_argument(
        "--grid_alpha",
        default="0.5,0.7,0.9,1.1",
        help="DEPRECATED: use --grid_weak_alpha_Etilt. Kept for backward compatibility.",
    )
    ap.add_argument(
        "--grid_alpha_file",
        default=None,
        help="DEPRECATED: use --grid_weak_alpha_Etilt_file. Kept for backward compatibility.",
    )
    ap.add_argument(
        "--grid_weak_alpha_Etilt",
        default=None,
        help="Grid values for weak_alpha_Etilt (WEAK energy-tilt knob). Overrides --grid_alpha if provided.",
    )
    ap.add_argument(
        "--grid_weak_alpha_Etilt_file",
        default=None,
        help="Optional path to a text file containing weak_alpha_Etilt grid values. Overrides --grid_alpha_file if provided.",
    )
    ap.add_argument("--thread_weight_app", type=float, default=6.0)
    ap.add_argument("--thread_weight_dis", type=float, default=0.5)
    args = ap.parse_args()

    py = Path(args.python)
    pack = Path(args.pack)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = None if not args.global_manifest else Path(args.global_manifest)
    allowed_globals: set[str] = set()
    if manifest_path is not None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        allowed = manifest.get("allowed_cross_sector_freeze", [])
        if not isinstance(allowed, list):
            raise ValueError("Manifest allowed_cross_sector_freeze must be a list")
        allowed_globals = {str(x) for x in allowed}

    # Persist run framing / provenance.
    (out_dir / "run_meta.json").write_text(
        json.dumps(
            {
                "intent": str(args.intent),
                "global_manifest": None if manifest_path is None else str(manifest_path.resolve()),
                "allowed_cross_sector_freeze": sorted(allowed_globals),
                "framing": {
                    "exploratory_tuning_not_global_calibration": bool(args.intent == "exploratory_tuning"),
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    if args.grid_A_file:
        grid_A = parse_grid_file(Path(args.grid_A_file))
    else:
        grid_A = parse_grid(args.grid_A)

    grid_alpha_file = args.grid_weak_alpha_Etilt_file or args.grid_alpha_file
    grid_alpha_spec = args.grid_weak_alpha_Etilt if args.grid_weak_alpha_Etilt is not None else args.grid_alpha

    if grid_alpha_file:
        grid_weak_alpha = parse_grid_file(Path(grid_alpha_file))
    else:
        grid_weak_alpha = parse_grid(grid_alpha_spec)

    if args.intent == "anchor_calibration":
        if manifest_path is None:
            raise ValueError("anchor_calibration requires --global_manifest")
        if "A" not in allowed_globals:
            raise ValueError("anchor_calibration requires 'A' to be allowed in the manifest")
        # weak_alpha_Etilt is sector-specific by default; require it fixed (single value) for anchor runs.
        uniq = sorted({float(x) for x in grid_weak_alpha})
        if len(uniq) != 1:
            raise ValueError("anchor_calibration requires weak_alpha_Etilt grid to have exactly one value")
        if abs(uniq[0]) > 1e-12:
            raise ValueError("anchor_calibration requires weak_alpha_Etilt to be fixed at 0.0")

    # Baseline from run05, with thread weights set via args.
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
        "--weak_alpha_Etilt",
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
        "--thread_weight_app",
        str(float(args.thread_weight_app)),
        "--thread_weight_dis",
        str(float(args.thread_weight_dis)),
        "--flavors",
        "3",
        "--steps",
        "700",
        "--chi2_mode",
        "poisson_dev",
        "--poisson_shape",
        "none",
    ]

    results: list[Result] = []

    for A, weak_alpha_Etilt in itertools.product(grid_A, grid_weak_alpha):
        tag = safe_tag(f"A_{A:.6g}__weak_alpha_Etilt_{weak_alpha_Etilt:.6g}")
        ev_dir = out_dir / tag
        art_dir = ev_dir / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)

        out_csv = art_dir / "out.csv"
        stdout_path = ev_dir / "terminal_output.txt"
        cmd_path = ev_dir / "command.txt"

        cmd = [
            str(py),
            *base,
            "--A",
            str(float(A)),
            "--weak_alpha_Etilt",
            str(float(weak_alpha_Etilt)),
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
                A=float(A),
                weak_alpha_Etilt=float(weak_alpha_Etilt),
                chi2_geo_total=float(chi2_geo),
                delta_total=float(delta),
                pos_channels=int(pos),
                exit_code=int(proc.returncode),
                stdout_path=stdout_path,
                cmd_path=cmd_path,
                out_csv=out_csv,
            )
        )

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

    summary_path = out_dir / "summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "intent",
            "global_manifest",
            "A",
            "weak_alpha_Etilt",
            "chi2_geo_total",
            "delta_total",
            "pos_channels",
            "exit_code",
            "ok",
            "evidence_dir",
        ])
        for r in sorted_results:
            w.writerow([
                str(args.intent),
                "" if manifest_path is None else str(manifest_path),
                r.A,
                r.weak_alpha_Etilt,
                r.chi2_geo_total,
                r.delta_total,
                r.pos_channels,
                r.exit_code,
                ok(r),
                str(r.stdout_path.parent),
            ])

    keep = set()
    for r in sorted_results[: int(args.max_keep)]:
        keep.add(r.stdout_path.parent)
    for r in sorted_results:
        if r.exit_code != 0:
            keep.add(r.stdout_path.parent)

    for p in out_dir.iterdir():
        if p.is_dir() and p not in keep:
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
    print(
        f"BEST: A={best.A} weak_alpha_Etilt={best.weak_alpha_Etilt} chi2_geo={best.chi2_geo_total} "
        f"delta={best.delta_total} pos={best.pos_channels} rc={best.exit_code}"
    )
    print(f"SUMMARY: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
