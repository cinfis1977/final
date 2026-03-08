from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def _write_points_csv(path: Path, *, mode: str, targets: list[float], n_scans: int, phase: float, seed: int) -> None:
    rng = np.random.default_rng(seed)
    rows = []

    for scan in range(n_scans):
        t = scan / max(1, n_scans - 1)
        # A mode-specific offset + shared oscillatory drift.
        drift_ppm = 6.0 * np.sin(2 * np.pi * t + phase)
        if mode == "B2":
            drift_ppm += 0.8
        if mode == "B3":
            drift_ppm += 1.6
        if mode == "A2":
            drift_ppm += -0.3

        scan_scale = 1.0 + 0.35 * np.cos(2 * np.pi * t + 0.3)

        for j, mz0 in enumerate(targets):
            noise_ppm = rng.normal(0.0, 2.5)
            mz = mz0 * (1.0 + (drift_ppm + noise_ppm) * 1e-6)
            intensity = (1200.0 + 50.0 * j) * scan_scale * (1.0 + 0.05 * rng.normal())
            rows.append({"scan": scan, "mz": mz, "intensity": max(1e-3, float(intensity))})

        for _ in range(12):
            mz = float(rng.uniform(50.0, 350.0))
            intensity = float(rng.uniform(1.0, 60.0) * scan_scale)
            rows.append({"scan": scan, "mz": mz, "intensity": max(1e-3, intensity)})

    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _write_targets_csv(path: Path, targets: list[float], window_ppm: float) -> None:
    tdf = pd.DataFrame(
        {
            "label": [f"T{i+1:02d}" for i in range(len(targets))],
            "target_mz": targets,
            "window_ppm": [float(window_ppm)] * len(targets),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    tdf.to_csv(path, index=False)


def test_ms_dynamic_3arm_driver_smoke(tmp_path: Path) -> None:
    targets = [100.0, 150.0, 200.0, 250.0, 300.0]

    a1 = tmp_path / "A1_points.csv"
    b2 = tmp_path / "B2_points.csv"
    b3 = tmp_path / "B3_points.csv"
    a2 = tmp_path / "A2_points.csv"
    targets_csv = tmp_path / "targets.csv"

    _write_points_csv(a1, mode="A1", targets=targets, n_scans=60, phase=0.0, seed=101)
    _write_points_csv(b2, mode="B2", targets=targets, n_scans=60, phase=0.4, seed=202)
    _write_points_csv(b3, mode="B3", targets=targets, n_scans=60, phase=0.8, seed=303)
    _write_points_csv(a2, mode="A2", targets=targets, n_scans=60, phase=1.2, seed=404)
    _write_targets_csv(targets_csv, targets, window_ppm=30.0)

    out_root = tmp_path / "out_root"

    cmd = [
        sys.executable,
        str(ROOT / "run_ms_particle_specific_dynamic_3arm_v1_0.py"),
        "--run_id",
        "TEST_RUN",
        "--out_root",
        str(out_root),
        "--mode_a1_points",
        str(a1),
        "--mode_b2_points",
        str(b2),
        "--mode_b3_points",
        str(b3),
        "--mode_a2_points",
        str(a2),
        "--targets_csv",
        str(targets_csv),
        "--ablations",
        "internal_only",
        "--good_ppm",
        "3",
        "--window_ppm",
        "30",
        "--min_n",
        "8",
        "--max_bins",
        "8",
        "--alpha",
        "0.25",
    ]

    cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    print("[CMD]", " ".join(cmd))
    print("[STDOUT]\n", cp.stdout)
    print("[STDERR]\n", cp.stderr)
    assert cp.returncode == 0

    base = out_root / "TEST_RUN" / "internal_only"
    assert (base / "A1_B2" / "ms_dynamic_telemetry.json").exists()
    assert (base / "A1_B3_holdout" / "ms_dynamic_telemetry.json").exists()
    assert (base / "A2_B3_thirdarm" / "ms_dynamic_telemetry.json").exists()

    final_dir = base / "final"
    verdict_json = list(final_dir.glob("prereg_lock_and_final_verdict_goodppm*.json"))
    verdict_md = list(final_dir.glob("FINAL_VERDICT_REPORT_goodppm*.md"))
    assert len(verdict_json) == 1
    assert len(verdict_md) == 1

    tel = json.loads((base / "A1_B2" / "ms_dynamic_telemetry.json").read_text(encoding="utf-8"))
    assert tel["dynamics"]["internal_dynamics_used"] is True
