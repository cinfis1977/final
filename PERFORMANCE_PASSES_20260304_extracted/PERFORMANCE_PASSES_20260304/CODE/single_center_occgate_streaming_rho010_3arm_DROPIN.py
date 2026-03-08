from __future__ import annotations

import csv
import math
from pathlib import Path

RHO = 0.10
CORE_HALF_WIDTH = 0.05
SHOULDER_HALF_WIDTH = 0.15
OUTER_HALF_WIDTH = 0.30


def read_targets(path: Path):
    targets = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            label = row.get("label") or row.get("target_id") or row.get("id") or row.get("name")
            mz_raw = row.get("target_mz") or row.get("mz") or row.get("center_mz") or row.get("mz_center")
            if not label or mz_raw is None:
                continue
            targets.append((str(label), float(mz_raw)))
    if not targets:
        raise SystemExit(f"No usable targets found in {path}")
    return targets


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def process_points(path: Path, targets):
    acc = {label: {"I_core": 0.0, "I_shoulder": 0.0, "I_outer": 0.0} for label, _ in targets}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        headers = {h.lower(): h for h in (r.fieldnames or [])}
        mz_key = headers.get("mz")
        int_key = headers.get("intensity")
        if mz_key is None or int_key is None:
            raise SystemExit(f"Could not find mz/intensity columns in {path}")
        for row in r:
            try:
                mz = float(row[mz_key])
                inten = float(row[int_key])
            except Exception:
                continue
            if not math.isfinite(mz) or not math.isfinite(inten):
                continue
            for label, center in targets:
                d = abs(mz - center)
                if d <= CORE_HALF_WIDTH:
                    acc[label]["I_core"] += inten
                elif d <= SHOULDER_HALF_WIDTH:
                    acc[label]["I_shoulder"] += inten
                elif d <= OUTER_HALF_WIDTH:
                    acc[label]["I_outer"] += inten

    rows = []
    for label, center in targets:
        core = acc[label]["I_core"]
        shoulder = acc[label]["I_shoulder"]
        outer = acc[label]["I_outer"]
        total = core + shoulder + outer
        x_occ = clamp01(core / total) if total > 0.0 else 0.0
        gate = clamp01(1.0 - RHO * x_occ)
        rows.append({
            "target_id": label,
            "target_mz": center,
            "I_core": core,
            "I_shoulder": shoulder,
            "I_outer": outer,
            "local_total": total,
            "x_occ": x_occ,
            "rho": RHO,
            "gate_occ_factor": gate,
        })
    return rows


def main():
    base = Path(".")
    targets = read_targets(base / "targets_used.csv")
    files = [
        ("ModeA_points", base / "ModeA_points.csv"),
        ("ModeB_points", base / "ModeB_points.csv"),
        ("ModeB_holdout_points", base / "ModeB_holdout_points.csv"),
    ]
    all_rows = []
    for setting, path in files:
        rows = process_points(path, targets)
        for row in rows:
            out = {"setting": setting}
            out.update(row)
            all_rows.append(out)

    out_csv = base / "single_center_occgate_streaming_rho010_3arm.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "setting", "target_id", "target_mz", "I_core", "I_shoulder", "I_outer",
            "local_total", "x_occ", "rho", "gate_occ_factor"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in all_rows:
            w.writerow({k: (f"{row[k]:.12f}" if isinstance(row[k], float) else row[k]) for k in fieldnames})

    print(f"wrote={out_csv}")


if __name__ == "__main__":
    main()
