#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DM-C1 paper-run mode.

Single-command driver that generates a deterministic DM-C1 synthetic pack,
runs the DM-C1 dynamics runner under proxy-call poison, and writes artifacts
under out/.

This is an IO/closure + schema-stability deliverable, not an accuracy claim.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from dm_dynamics_core_c1 import DMDynamicsC1Params, simulate_profile


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(_repo_root()))
    if r.returncode != 0:
        raise RuntimeError(
            "DM-C1 paper run failed\n"
            f"cmd={' '.join(cmd)}\n"
            f"rc={r.returncode}\n"
            f"STDOUT:\n{r.stdout}\n"
            f"STDERR:\n{r.stderr}\n"
        )


def _fmt_block(title: str, summary: dict[str, Any]) -> str:
    chi2 = summary.get("chi2", {})
    tel = summary.get("telemetry", {})
    b = tel.get("boundedness", {})
    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"- pack: {summary.get('pack', {}).get('path')}")
    lines.append(f"- chi2.total: {chi2.get('total')}")
    lines.append(f"- ndof: {chi2.get('ndof')}")
    lines.append(f"- dm_dynamics_core_used: {tel.get('dm_dynamics_core_used')}")
    lines.append(f"- proxy_overlay_used: {tel.get('proxy_overlay_used')}")
    lines.append(f"- stiffgate_in_evolution: {tel.get('stiffgate_in_evolution')}")
    lines.append(f"- bounded.g_in_0_1: {b.get('g_in_0_1')}")
    lines.append(f"- bounded.epsilon_nonneg: {b.get('epsilon_nonneg')}")
    lines.append(f"- bounded.finite_all: {b.get('finite_all')}")
    lines.append(f"- stability_not_accuracy: {summary.get('framing', {}).get('stability_not_accuracy')}")
    lines.append("")
    return "\n".join(lines)


def _make_self_consistent_pack(*, out_pack: Path, seed: int, n_steps: int, dt: float) -> None:
    rng = np.random.default_rng(int(seed))

    p = DMDynamicsC1Params(
        A_dm=0.07,
        texture_C=0.4,
        texture_wr=0.6,
        env_r0=2.5,
        env_p=2.0,
        eps_decay=0.7,
        k_circ=0.9,
        k_omega=0.25,
        drive_strength=0.45,
        k_eps=0.25,
        gamma_eps=0.18,
        k_g=0.9,
        S0=1.0,
        eps_w=0.6,
        m_w=0.9,
    )

    r_ref = np.linspace(0.2, 10.0, int(n_steps), dtype=float)
    a_bary_ref = 0.25 / (1.0 + (r_ref / 3.0) ** 2)

    def a_bary_fn(r: float) -> float:
        return float(np.interp(float(r), r_ref, a_bary_ref, left=float(a_bary_ref[0]), right=float(a_bary_ref[-1])))

    # Initial sim without mismatch feedback.
    sim = simulate_profile(
        n_steps=int(n_steps),
        dt=float(dt),
        r0=float(r_ref[0]),
        v0=0.0,
        theta0=0.1,
        omega0=0.05,
        epsilon0=0.0,
        g0=0.5,
        a_bary_fn=a_bary_fn,
        v_target_fn=None,
        sigma_v_fn=None,
        params=p,
        order_mode="forward",
        shuffle_seed=int(seed),
        enforce_circular_velocity=True,
    )

    for _ in range(3):
        r_prev = sim["r"].astype(float)
        v_prev = sim["v_pred"].astype(float)
        sig_prev = np.full_like(v_prev, 0.5, dtype=float)

        order = np.argsort(r_prev)
        r_sorted = r_prev[order]
        v_sorted = v_prev[order]
        s_sorted = sig_prev[order]

        def v_target_fn(r: float) -> float:
            return float(np.interp(float(r), r_sorted, v_sorted, left=float(v_sorted[0]), right=float(v_sorted[-1])))

        def sigma_fn(r: float) -> float:
            return float(np.interp(float(r), r_sorted, s_sorted, left=float(s_sorted[0]), right=float(s_sorted[-1])))

        sim = simulate_profile(
            n_steps=int(n_steps),
            dt=float(dt),
            r0=float(r_prev[0]),
            v0=float(v_prev[0]),
            theta0=0.1,
            omega0=0.05,
            epsilon0=0.0,
            g0=0.5,
            a_bary_fn=a_bary_fn,
            v_target_fn=v_target_fn,
            sigma_v_fn=sigma_fn,
            params=p,
            order_mode="forward",
            shuffle_seed=int(seed),
            enforce_circular_velocity=True,
        )

    r_obs = sim["r"].astype(float)
    v_obs = sim["v_pred"].astype(float)
    sigma_v = np.full_like(v_obs, 0.5, dtype=float)
    a_bary_obs = np.array([a_bary_fn(float(x)) for x in r_obs], dtype=float)

    pack = {
        "schema_version": "dm_c1_pack_v1",
        "galaxies": [
            {
                "name": "toy1",
                "r0": float(r_obs[0]),
                "v0": float(v_obs[0]),
                "theta0": 0.1,
                "omega0": 0.05,
                "epsilon0": 0.0,
                "g0": 0.5,
                "obs": {
                    "r": r_obs.tolist(),
                    "v_obs": v_obs.tolist(),
                    "sigma_v": sigma_v.tolist(),
                    "a_bary": a_bary_obs.tolist(),
                },
            }
        ],
        "meta": {
            "seed": int(seed),
            "n_steps": int(n_steps),
            "dt": float(dt),
        },
    }

    _write_json(out_pack, pack)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out_dir",
        default=str(_repo_root() / "out" / "dm_c1_paper"),
        help="Output directory (default: out/dm_c1_paper)",
    )
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--dt", type=float, default=0.2)
    ap.add_argument("--n_steps", type=int, default=240)

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pack_path = out_dir / "pack_dm_c1_toy.json"
    _make_self_consistent_pack(out_pack=pack_path, seed=int(args.seed), n_steps=int(args.n_steps), dt=float(args.dt))

    env = dict(os.environ)
    # Anti-fallback evidence: poison proxy paths; DM-C1 must remain runnable.
    env["DM_POISON_PROXY_CALLS"] = "1"

    out_fwd_csv = out_dir / "dm_c1_pred_forward.csv"
    out_fwd_json = out_dir / "dm_c1_summary_forward.json"
    out_rev_csv = out_dir / "dm_c1_pred_reverse.csv"
    out_rev_json = out_dir / "dm_c1_summary_reverse.json"
    report_md = out_dir / "paper_run_report.md"

    base_cmd = [
        sys.executable,
        str(_repo_root() / "dm_dynamics_runner_c1.py"),
        "--pack",
        str(pack_path),
        "--dt",
        str(float(args.dt)),
        "--n_steps",
        str(int(args.n_steps)),
        "--seed",
        str(int(args.seed)),
        "--A_dm",
        "0.07",
        "--texture_C",
        "0.4",
        "--texture_wr",
        "0.6",
        "--env_r0",
        "2.5",
        "--env_p",
        "2.0",
        "--eps_decay",
        "0.7",
        "--k_circ",
        "0.9",
        "--k_omega",
        "0.25",
        "--drive_strength",
        "0.45",
        "--k_eps",
        "0.25",
        "--gamma_eps",
        "0.18",
        "--k_g",
        "0.9",
        "--S0",
        "1.0",
        "--eps_w",
        "0.6",
        "--m_w",
        "0.9",
    ]

    cmd_fwd = base_cmd + ["--order_mode", "forward", "--out_csv", str(out_fwd_csv), "--out_json", str(out_fwd_json)]
    _run(cmd_fwd, env=env)

    cmd_rev = base_cmd + ["--order_mode", "reverse", "--out_csv", str(out_rev_csv), "--out_json", str(out_rev_json)]
    _run(cmd_rev, env=env)

    s_fwd = _load_json(out_fwd_json)
    s_rev = _load_json(out_rev_json)

    lines: list[str] = []
    lines.append("# DM-C1 paper run report")
    lines.append("")
    lines.append("This report is produced by `run_dm_c1_paper_run.py`.")
    lines.append("It is an IO/closure + schema-stability artifact for DM-C1 dynamics; not a physical-accuracy claim.")
    lines.append("")
    lines.append("## Run settings")
    lines.append("")
    lines.append(f"- seed: {int(args.seed)}")
    lines.append(f"- dt: {float(args.dt)}")
    lines.append(f"- n_steps: {int(args.n_steps)}")
    lines.append(f"- DM_POISON_PROXY_CALLS: {env.get('DM_POISON_PROXY_CALLS')}")
    lines.append("")
    lines.append(_fmt_block("Forward order", s_fwd))
    lines.append(_fmt_block("Reverse order", s_rev))

    report_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
