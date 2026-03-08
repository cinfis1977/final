import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from em_c1a_scattering_amplitude_core import evolve_A_over_scan


ROOT = Path(__file__).resolve().parents[3]


def _write_pack(path: Path, pack: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pack, indent=2, sort_keys=True), encoding="utf-8")


def _run_runner(tmp_path: Path, pack_path: Path, *, dt_max: float, extra_env: dict[str, str] | None = None):
    out_csv = tmp_path / f"out_dt{dt_max}.csv"
    out_json = tmp_path / f"out_dt{dt_max}.json"

    cmd = [
        sys.executable,
        str(ROOT / "em_scattering_pack_chi2_c1a.py"),
        "--pack",
        str(pack_path),
        "--out_csv",
        str(out_csv),
        "--out_json",
        str(out_json),
        "--dt_max",
        str(dt_max),
    ]

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    print("[CMD]", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    print("[STDOUT]\n", cp.stdout)
    print("[STDERR]\n", cp.stderr)
    assert cp.returncode == 0

    df = pd.read_csv(out_csv)
    summary = json.loads(out_json.read_text(encoding="utf-8"))
    return df, summary


def test_em_c1a_integrity_closure_refinement_and_antifallback(tmp_path: Path):
    s_values = np.array([10.0, 20.0, 40.0, 80.0, 160.0], dtype=float)
    s0 = float(s_values[0])

    A0 = complex(1.2, -0.3)
    beta = 0.7
    gamma = 0.12
    sigma_norm = 3.0

    A_vals = evolve_A_over_scan(
        s_values,
        s0=s0,
        A0=A0,
        beta_fn=lambda _t: beta,
        gamma_fn=lambda _t: gamma,
        dt_max=0.5,
    )
    sigma_pred = sigma_norm * (np.abs(A_vals) ** 2)

    pack = {
        "scan": [{"s": float(s)} for s in s_values.tolist()],
        "dyn": {
            "s0": float(s0),
            "A0_re": float(A0.real),
            "A0_im": float(A0.imag),
            "beta": {"kind": "const", "value": float(beta)},
            "gamma": {"kind": "const", "value": float(gamma)},
        },
        "obs": {"sigma_norm": float(sigma_norm)},
        "data": [
            {"sigma_data": float(v), "sigma_err": 1.0} for v in sigma_pred.astype(float).tolist()
        ],
    }

    pack_path = tmp_path / "pack.json"
    _write_pack(pack_path, pack)

    # Anti-fallback: poison baseline/overlay calls, runner must still pass.
    df1, summary1 = _run_runner(
        tmp_path / "run1",
        pack_path,
        dt_max=0.4,
        extra_env={"EM_C1A_POISON_BASELINE_CALLS": "1"},
    )

    assert summary1["telemetry"]["amplitude_core_used"] is True
    assert summary1["telemetry"]["baseline_used"] is False
    assert summary1["telemetry"]["gw_coupling_used"] is False
    assert summary1["framing"]["stability_not_accuracy"] is True

    # Closure: data==pred => chi2 ~ 0.
    assert summary1["fit"]["chi2_total"] <= 1e-10

    # Integrity checks.
    for c in ["s", "A_re", "A_im", "sigma_pred", "sigma_data", "sigma_err", "pull"]:
        assert c in df1.columns
        assert np.all(np.isfinite(df1[c].to_numpy(float)))
    assert np.all(df1["sigma_pred"].to_numpy(float) >= 0.0)

    # Refinement stability: dt_max halved should not change predictions much.
    df2, summary2 = _run_runner(
        tmp_path / "run2",
        pack_path,
        dt_max=0.2,
        extra_env={"EM_C1A_POISON_BASELINE_CALLS": "1"},
    )
    s1 = df1["sigma_pred"].to_numpy(float)
    s2 = df2["sigma_pred"].to_numpy(float)
    denom = np.maximum(np.abs(s1), 1e-12)
    rel = np.max(np.abs(s2 - s1) / denom)
    assert rel <= 0.05

    # Both runs should be closure-tight.
    assert summary2["fit"]["chi2_total"] <= 1e-10
