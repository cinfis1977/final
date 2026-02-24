from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pytest

from mastereq.unified_gksl import UnifiedGKSL


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _golden_file(rel: str) -> Path:
    p = _repo_root() / rel
    if not p.exists():
        pytest.skip(f"Golden output not found: {p}")
    return p


def _theta_for_amplitude(amp: float) -> float:
    amp = float(np.clip(amp, 0.0, 1.0))
    return 0.5 * math.asin(math.sqrt(amp))


def _prob_from_gksl(*, dm2: float, theta: float, L_km: float, E_GeV: float, dphi: float = 0.0, steps: int = 220, appearance: bool = True) -> float:
    ug = UnifiedGKSL(dm2, theta)

    if dphi != 0.0:
        delta_dm2 = float(dphi) * (4.0 * float(E_GeV)) / (1.267 * max(float(L_km), 1e-12))

        def extra_mass(_L: float, _E: float) -> np.ndarray:
            return np.array([[0.0, 0.0], [0.0, delta_dm2]], dtype=float)

        ug.add_mass_sector(extra_mass)

    rho = ug.integrate(float(L_km), float(E_GeV), steps=int(steps))
    if appearance:
        return float(np.real(rho[0, 0]))
    return float(np.real(rho[1, 1]))


def _infer_effective_phase_from_Psm(P_sm: float, *, mode: str, amp_app: float) -> float:
    """Infer the effective phase Delta used by the runner's phase-shift method.

    This intentionally mirrors the assumptions in the runner's `apply_phase_shift_to_prob()`:
    - appearance: P = A0 * sin^2(Delta)
    - disappearance: P = cos^2(Delta)
    returning Delta in the principal branch used by the runner.
    """
    P_sm = float(np.clip(P_sm, 0.0, 1.0))
    if mode == "appearance":
        A0 = max(float(amp_app), 1e-12)
        sin2 = float(np.clip(P_sm / A0, 0.0, 1.0))
        return float(np.arcsin(np.sqrt(sin2)))
    if mode == "disappearance":
        return float(np.arccos(np.sqrt(P_sm)))
    raise ValueError(f"Unknown mode={mode!r}")


def _dm2_from_phase(Delta: float, *, L_km: float, E_GeV: float) -> float:
    """Solve Delta = 1.267 * dm2 * L / (4E) for dm2 (GKSL convention)."""
    return float(Delta) * (4.0 * float(E_GeV)) / (1.267 * max(float(L_km), 1e-12))


def _mode_from_channel(ch: str) -> str:
    ch_low = ch.lower()
    if "_app" in ch_low or "appearance" in ch_low:
        return "appearance"
    if "_dis" in ch_low or "disappearance" in ch_low:
        return "disappearance"
    raise ValueError(f"Unrecognized channel mode from channel={ch!r}")


@pytest.mark.parametrize(
    "rel_path,L_km,omega",
    [
        ("integration_artifacts/out/verdict_golden/out/WEAK/nova_BREATH_THREAD_test.csv", 810.0, 0.0038785094488762877),
        ("integration_artifacts/out/verdict_golden/out/WEAK/t2k_BREATH_THREAD_validation_APPROXREAL.csv", 295.0, 0.010649466622338281),
    ],
)
def test_weak_golden_probabilities_match_gksl(rel_path: str, L_km: float, omega: float):
    """Paper-grade equivalence check for WEAK.

    For every bin in the golden runner CSV, reproduce:
    - P_sm via GKSL unitary evolution
    - P_geo via GKSL unitary evolution + a constant delta(dm2) that yields the runner's dphi

    This proves the runner's (Delta -> Delta + dphi) kernel is exactly representable
    as a GKSL Hamiltonian correction at the probability level (given the runner's
    own two-flavor approximations).
    """
    p = _golden_file(rel_path)

    # Runner hard-coded amplitude for appearance mode
    theta23 = math.radians(45.0)
    theta13 = math.radians(8.6)
    amp_app = (math.sin(theta23) ** 2) * (math.sin(2 * theta13) ** 2)
    theta_app = _theta_for_amplitude(amp_app)
    theta_dis = math.radians(45.0)  # maximal mixing for disappearance mode

    # Sanity: file omega should be constant and equal to expected
    omega_tol = 1e-12

    with p.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows, f"No rows read from {p}"

    # Use enough RK4 steps to make numerical error subdominant.
    steps = 900 if L_km >= 500 else 650

    for row in rows:
        ch = str(row["channel"])
        mode = _mode_from_channel(ch)
        appearance = mode == "appearance"

        E = float(row["E_ctr"])
        dphi = float(row["dphi"])

        omega_row = float(row.get("omega", "nan"))
        assert abs(omega_row - float(omega)) < omega_tol

        p_sm_out = float(row["P_sm"])
        p_geo_out = float(row["P_geo"])

        # The runner's algorithmic contract is: take the baseline P_sm (which may come from
        # different sources, including pack-provided ratios or bin shifts), infer a phase,
        # then apply Delta -> Delta + dphi and convert back to P_geo.
        #
        # We validate that this *exact map* is representable as a GKSL Hamiltonian update by:
        # 1) inferring the effective phase from the stored P_sm
        # 2) solving for an effective dm2 (GKSL convention) that reproduces that phase
        # 3) adding a mass-sector delta(dm2) that yields the same dphi
        mode = "appearance" if appearance else "disappearance"
        Delta_eff = _infer_effective_phase_from_Psm(p_sm_out, mode=mode, amp_app=amp_app)
        dm2_eff = _dm2_from_phase(Delta_eff, L_km=L_km, E_GeV=E)

        theta = theta_app if appearance else theta_dis

        p_sm_gksl = _prob_from_gksl(dm2=dm2_eff, theta=theta, L_km=L_km, E_GeV=E, dphi=0.0, steps=steps, appearance=appearance)
        p_geo_gksl = _prob_from_gksl(dm2=dm2_eff, theta=theta, L_km=L_km, E_GeV=E, dphi=dphi, steps=steps, appearance=appearance)

        # With dm2_eff constructed from P_sm, the SM agreement should be very tight.
        assert abs(p_sm_gksl - p_sm_out) < 8e-4
        assert abs(p_geo_gksl - p_geo_out) < 1.2e-3
