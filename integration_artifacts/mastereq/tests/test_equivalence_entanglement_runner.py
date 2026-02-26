from __future__ import annotations

import csv
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

_INTEGRATION_ROOT = Path(__file__).resolve().parents[2]
if str(_INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_ROOT))

from mastereq.unified_gksl import UnifiedGKSL
from mastereq.entanglement_sector import (
    make_entanglement_dephasing_fn,
    chsh_visibility_from_gamma,
)
from mastereq.microphysics import (
    gamma_km_inv_from_n_sigma_v,
    sigma_entanglement_reference_cm2,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _bridge_runner_module():
    p = _repo_root() / "integration_artifacts" / "entanglement_photon_bridge" / "audit_nist_coinc_csv_bridgeE0_v1_DROPIN.py"
    if not p.exists():
        raise RuntimeError(f"Runner file not found: {p}")
    return _load_module_from_path("audit_nist_coinc_csv_bridgeE0_v1_DROPIN", p)


def _read_rows_for_chsh(csv_path: Path) -> list[tuple[int, int, int, int]]:
    rows_raw: list[tuple[float, int, int, int, int]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            t = float(r["coinc_idx"])
            a = int(r["a_set"])
            b = int(r["b_set"])
            ao = int(r["a_out"])
            bo = int(r["b_out"])
            rows_raw.append((t, a, b, ao, bo))

    rows_raw.sort(key=lambda x: x[0])
    # Mirror runner: use gap-valid rows (all except first after sorting)
    return [(a, b, ao, bo) for _, a, b, ao, bo in rows_raw[1:]]


def _independent_chsh(rows: list[tuple[int, int, int, int]]):
    by_combo: dict[tuple[int, int], list[tuple[int, int]]] = {
        (0, 0): [],
        (0, 1): [],
        (1, 0): [],
        (1, 1): [],
    }
    for a, b, ao, bo in rows:
        by_combo[(a, b)].append((ao, bo))

    Es: dict[tuple[int, int], float] = {}
    for c, obs in by_combo.items():
        npp = npm = nmp = nmm = 0
        for ao, bo in obs:
            if ao == 1 and bo == 1:
                npp += 1
            elif ao == 1 and bo == -1:
                npm += 1
            elif ao == -1 and bo == 1:
                nmp += 1
            elif ao == -1 and bo == -1:
                nmm += 1
        n = npp + npm + nmp + nmm
        Es[c] = (npp + nmm - npm - nmp) / n if n > 0 else float("nan")

    s_signed = Es[(0, 0)] + Es[(0, 1)] + Es[(1, 0)] - Es[(1, 1)]
    s_abs = abs(s_signed)
    return Es, s_signed, s_abs


def test_entanglement_runner_chsh_matches_independent_math():
    runner = _bridge_runner_module()
    data_csv = _repo_root() / "integration_artifacts" / "entanglement_photon_bridge" / "nist_run4_coincidences.csv"
    rows = _read_rows_for_chsh(data_csv)

    Es_ref, s_signed_ref, s_abs_ref = _independent_chsh(rows)
    Es_run, _, _, s_signed_run, s_abs_run = runner.chsh_from_rows(rows)

    for key in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        assert math.isclose(float(Es_ref[key]), float(Es_run[key]), rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(float(s_signed_ref), float(s_signed_run), rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(float(s_abs_ref), float(s_abs_run), rel_tol=0.0, abs_tol=1e-15)


def test_entanglement_microphysics_wiring_matches_explicit_gamma():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    L_km = 295.0
    E_GeV = 1.0

    n_cm3 = 1.0e18
    vis = 0.9
    sigma = sigma_entanglement_reference_cm2(E_GeV, vis)
    gamma = gamma_km_inv_from_n_sigma_v(n_cm3, sigma, 3.0e10)

    ug_micro = UnifiedGKSL(dm2, theta)
    ug_micro.add_damping(
        make_entanglement_dephasing_fn(
            use_microphysics=True,
            n_cm3=n_cm3,
            E_GeV_ref=E_GeV,
            visibility=vis,
            v_cm_s=3.0e10,
        )
    )

    ug_explicit = UnifiedGKSL(dm2, theta)
    ug_explicit.add_damping(make_entanglement_dephasing_fn(gamma=gamma, use_microphysics=False))

    rho_micro = ug_micro.integrate(L_km, E_GeV, steps=320)
    rho_explicit = ug_explicit.integrate(L_km, E_GeV, steps=320)
    assert np.allclose(rho_micro, rho_explicit, atol=5e-13, rtol=0.0)


def test_chsh_visibility_template_is_monotone_decreasing():
    g = 2.0e-3
    s0 = 2.0 * math.sqrt(2.0)
    s1 = chsh_visibility_from_gamma(g, 100.0, s0=s0)
    s2 = chsh_visibility_from_gamma(g, 300.0, s0=s0)
    assert s1 <= s0
    assert s2 <= s1
