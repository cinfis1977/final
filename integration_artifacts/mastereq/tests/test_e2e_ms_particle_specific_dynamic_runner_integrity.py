from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def _write_points_csv(path: Path, *, setting: str, targets: list[float], n_scans: int, phase: float, seed: int) -> None:
    rng = np.random.default_rng(seed)
    rows = []

    for scan in range(n_scans):
        t = scan / max(1, n_scans - 1)
        drift_ppm = 6.0 * np.sin(2 * np.pi * t + phase) + (1.0 if setting.endswith("B2") else 0.0)

        # Deterministic scan-level scale so TIC varies across scans.
        scan_scale = 1.0 + 0.35 * np.cos(2 * np.pi * t + 0.3)

        # True peaks at targets with per-peak noise.
        for j, mz0 in enumerate(targets):
            noise_ppm = rng.normal(0.0, 2.5)  # make drift_obs somewhat noisy so smoothing is measurable
            mz = mz0 * (1.0 + (drift_ppm + noise_ppm) * 1e-6)
            intensity = (1200.0 + 50.0 * j) * scan_scale * (1.0 + 0.05 * rng.normal())
            rows.append({"scan": scan, "mz": mz, "intensity": max(1e-3, float(intensity))})

        # Distractor peaks outside windows.
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


def _run_runner(tmp_path: Path, *, out_dir: Path, ablation: str, require_stateful: bool) -> dict:
    a1 = tmp_path / "A1_points.csv"
    b2 = tmp_path / "B2_points.csv"
    targets_csv = tmp_path / "targets.csv"

    targets = [100.0, 150.0, 200.0, 250.0, 300.0]
    _write_points_csv(a1, setting="A1", targets=targets, n_scans=60, phase=0.0, seed=123)
    _write_points_csv(b2, setting="B2", targets=targets, n_scans=60, phase=0.6, seed=456)
    _write_targets_csv(targets_csv, targets, window_ppm=30.0)

    cmd = [
        sys.executable,
        str(ROOT / "ms_particle_specific_dynamic_runner_v1_0_DROPIN.py"),
        "--inputs",
        str(a1),
        str(b2),
        "--out_dir",
        str(out_dir),
        "--targets_csv",
        str(targets_csv),
        "--baseline",
        "A1_points",  # derived from filename stem
        "--ablation",
        str(ablation),
        "--alpha",
        "0.25",
    ]
    if require_stateful:
        cmd.append("--require_stateful_dynamics")

    cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    print("[CMD]", " ".join(cmd))
    print("[STDOUT]\n", cp.stdout)
    print("[STDERR]\n", cp.stderr)
    assert cp.returncode == 0

    tel = json.loads((out_dir / "ms_dynamic_telemetry.json").read_text(encoding="utf-8"))
    scan_state = pd.read_csv(out_dir / "scan_state.csv")
    return {"telemetry": tel, "scan_state": scan_state, "out_dir": out_dir}


def test_ms_dynamic_runner_integrity_and_ablation(tmp_path: Path) -> None:
    out_internal = tmp_path / "out_internal"
    out_thread = tmp_path / "out_thread"

    r_int = _run_runner(tmp_path, out_dir=out_internal, ablation="internal_only", require_stateful=True)
    r_thr = _run_runner(tmp_path, out_dir=out_thread, ablation="thread_only", require_stateful=False)

    # Required legacy artifacts for prereg finalizer compatibility
    for out_dir in (out_internal, out_thread):
        assert (out_dir / "alltargets_bin_success_width_stats.csv").exists()
        assert (out_dir / "alltargets_delta_success_width_pairs.csv").exists()
        assert (out_dir / "targets_summary.csv").exists()
        assert (out_dir / "targets_used.csv").exists()
        assert (out_dir / "anchors.json").exists()
        assert (out_dir / "ms_dynamic_telemetry.json").exists()
        assert (out_dir / "scan_state.csv").exists()

    tel_int = r_int["telemetry"]
    tel_thr = r_thr["telemetry"]

    assert tel_int["dynamics"]["internal_dynamics_used"] is True
    assert tel_thr["dynamics"]["internal_dynamics_used"] is False

    assert tel_int["dynamics"]["stateful_steps_total"] > 0
    assert tel_thr["dynamics"]["stateful_steps_total"] == 0

    # Ablation behavior: INTERNAL_ONLY should be smoother than THREAD_ONLY.
    ss_int = r_int["scan_state"].sort_values(["setting", "scan"]).copy()
    ss_thr = r_thr["scan_state"].sort_values(["setting", "scan"]).copy()

    def mean_abs_step(df: pd.DataFrame) -> float:
        steps = []
        for _, g in df.groupby("setting", sort=True):
            x = g["drift_state_ppm"].to_numpy(dtype=float)
            dx = np.abs(np.diff(x[np.isfinite(x)]))
            if dx.size:
                steps.append(float(np.mean(dx)))
        return float(np.mean(steps)) if steps else float("nan")

    m_int = mean_abs_step(ss_int)
    m_thr = mean_abs_step(ss_thr)

    assert np.isfinite(m_int) and np.isfinite(m_thr)
    assert m_int < m_thr
