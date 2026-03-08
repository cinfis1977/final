import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from em_c1a1_scattering_amplitude_core import evolve_A_over_scan_c1a1


ROOT = Path(__file__).resolve().parents[3]


def _write_pack(path: Path, pack: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pack, indent=2, sort_keys=True), encoding="utf-8")


def _run_runner(tmp_path: Path, pack_path: Path, *, dt_max: float, extra_env: dict[str, str] | None = None):
    out_csv = tmp_path / f"out_dt{dt_max}.csv"
    out_json = tmp_path / f"out_dt{dt_max}.json"

    cmd = [
        sys.executable,
        str(ROOT / "em_scattering_pack_chi2_c1a1.py"),
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


def test_em_c1a1_holomorphic_term_closure_refinement_and_antifallback(tmp_path: Path):
    s_values = np.array([10.0, 15.0, 22.0, 33.0, 50.0], dtype=float)
    s0 = float(s_values[0])

    A0 = complex(0.9, 0.2)
    beta = 0.4
    gamma = 0.08
    sigma_norm = 2.5

    # Nonlinear holomorphic term: m_hol = kappa*(A/A_scale)^(p-1), with p=2 => dA has A^2 contribution.
    kappa_re = 0.06
    kappa_im = -0.02
    power = 2
    A_scale = 1.0

    dt_gen = 0.05
    A_vals = evolve_A_over_scan_c1a1(
        s_values,
        s0=s0,
        A0=A0,
        beta_fn=lambda _t: beta,
        gamma_fn=lambda _t: gamma,
        m_hol_fn=lambda _t, A: complex(kappa_re, kappa_im) * (A / A_scale) ** (power - 1),
        dt_max=dt_gen,
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
            "m_hol": {
                "kind": "poly",
                "kappa_re": float(kappa_re),
                "kappa_im": float(kappa_im),
                "power": int(power),
                "A_scale": float(A_scale),
            },
        },
        "obs": {"sigma_norm": float(sigma_norm)},
        "data": [{"sigma_data": float(v), "sigma_err": 1.0} for v in sigma_pred.astype(float).tolist()],
    }

    pack_path = tmp_path / "pack.json"
    _write_pack(pack_path, pack)

    # Anti-fallback enabled.
    df1, summary1 = _run_runner(
        tmp_path / "run1",
        pack_path,
        dt_max=dt_gen,
        extra_env={"EM_C1A_POISON_BASELINE_CALLS": "1"},
    )

    assert summary1["telemetry"]["amplitude_core_used"] is True
    assert summary1["telemetry"]["holomorphic_term_used"] is True
    assert summary1["telemetry"]["baseline_used"] is False
    assert summary1["framing"]["stability_not_accuracy"] is True

    # Closure: data==pred => chi2 ~ 0.
    assert summary1["fit"]["chi2_total"] <= 1e-10

    # Integrity checks.
    for c in ["s", "A_re", "A_im", "sigma_pred", "sigma_data", "sigma_err", "pull"]:
        assert c in df1.columns
        assert np.all(np.isfinite(df1[c].to_numpy(float)))
    assert np.all(df1["sigma_pred"].to_numpy(float) >= 0.0)

    # Refinement stability.
    df2, summary2 = _run_runner(
        tmp_path / "run2",
        pack_path,
        dt_max=dt_gen / 2.0,
        extra_env={"EM_C1A_POISON_BASELINE_CALLS": "1"},
    )

    s1 = df1["sigma_pred"].to_numpy(float)
    s2 = df2["sigma_pred"].to_numpy(float)
    denom = np.maximum(np.abs(s1), 1e-12)
    rel = np.max(np.abs(s2 - s1) / denom)
    assert rel <= 0.05

    assert summary2["fit"]["chi2_total"] <= 1e-10

    # Sanity: holomorphic term should have a noticeable effect vs m_hol omitted.
    pack_nohol = json.loads(json.dumps(pack))
    del pack_nohol["dyn"]["m_hol"]
    pack2_path = tmp_path / "pack_nohol.json"
    _write_pack(pack2_path, pack_nohol)

    df_nohol, summary_nohol = _run_runner(
        tmp_path / "run3",
        pack2_path,
        dt_max=dt_gen,
        extra_env={"EM_C1A_POISON_BASELINE_CALLS": "1"},
    )
    assert summary_nohol["telemetry"]["holomorphic_term_used"] is False

    diff = np.max(np.abs(df_nohol["sigma_pred"].to_numpy(float) - df1["sigma_pred"].to_numpy(float)))
    assert diff > 1e-6
